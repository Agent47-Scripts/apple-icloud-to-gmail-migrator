#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
Apple iCloud Mail to Google Workspace / Gmail Migration Pipeline (Bulletproof)
================================================================================
Author:       Tino Höhne
Repository:   Agent47-Scripts/Apple-Mail-to-Google-Workspace-Migration
License:      MIT License

Description:
Production-grade IMAP migration script with auto-reconnect, size limits,
mUTF-7 decoding/encoding fixes, and robust fallback duplicate checking.
================================================================================
"""

import os
import sys
import time
import socket
import ssl
import imaplib
import email
import hashlib
from email.utils import parsedate_to_datetime

# Retrieve credentials from environment variables
SRC_USER = os.getenv("SRC_USER")
SRC_PASS = os.getenv("SRC_PASS")
TGT_USER = os.getenv("TGT_USER")
TGT_PASS = os.getenv("TGT_PASS")

if not all([SRC_USER, SRC_PASS, TGT_USER, TGT_PASS]):
    print("ERROR: Missing required environment variables (SRC_USER, SRC_PASS, TGT_USER, TGT_PASS)!")
    sys.exit(1)

# RESUME SETTING: Set to None for standard runs, or exact folder name to resume
RESUME_FROM_FOLDER = None

# Limit for Gmail IMAP APPEND (approx 24.5 MB to be safe with encoding overhead)
MAX_EMAIL_SIZE = 24.5 * 1024 * 1024

SRC_HOST = "imap.mail.me.com"
SRC_PORT = 993
TGT_HOST = "imap.gmail.com"
TGT_PORT = 993


def connect_imap(host, port, user, password):
    """Establishes SSL IMAP connection with automatic retry."""
    while True:
        try:
            context = ssl.create_default_context()
            conn = imaplib.IMAP4_SSL(host, port, ssl_context=context)
            conn.login(user, password)
            return conn
        except Exception as e:
            print(f"  [!] Connection failed to {host} ({e}). Retrying in 5 seconds...")
            time.sleep(5)


def decode_mutf7(folder_bytes):
    """Safely decodes mUTF-7 encoded IMAP folder names."""
    if isinstance(folder_bytes, str):
        folder_bytes = folder_bytes.encode('latin1')
    
    res = []
    i = 0
    n = len(folder_bytes)
    while i < n:
        if folder_bytes[i] == ord('&'):
            j = folder_bytes.find(b'-', i)
            if j == -1:
                res.append(folder_bytes[i:])
                break
            if j == i + 1:
                res.append('&')
            else:
                b64 = folder_bytes[i+1:j].replace(b',', b'/')
                pad = (-len(b64)) % 4
                b64 += b'=' * pad
                try:
                    import base64
                    decoded = base64.b64decode(b64).decode('utf-16be')
                    res.append(decoded)
                except Exception:
                    res.append(folder_bytes[i:j+1].decode('latin1', errors='ignore'))
            i = j + 1
        else:
            res.append(chr(folder_bytes[i]))
            i += 1
    return "".join(res)


def encode_mutf7(unicode_str):
    """Encodes Unicode string to mUTF-7 for IMAP folder operations."""
    res = []
    b64_buf = []
    
    def flush_b64():
        if not b64_buf:
            return ""
        s = "".join(b64_buf)
        b64 = s.encode('utf-16be')
        import base64
        encoded = base64.b64encode(b64).decode('ascii').rstrip('=').replace('/', ',')
        return "&" + encoded + "-"

    for char in unicode_str:
        if 0x20 <= ord(char) <= 0x7E:
            if char == '&':
                res.append(flush_b64())
                b64_buf = []
                res.append("&-")
            else:
                if b64_buf:
                    res.append(flush_b64())
                    b64_buf = []
                res.append(char)
        else:
            b64_buf.append(char)
            
    if b64_buf:
        res.append(flush_b64())
        
    return "".join(res)


def generate_fallback_id(msg):
    """Generates MD5 hash fallback for emails lacking Message-ID."""
    date_str = msg.get("Date", "")
    sub_str = msg.get("Subject", "")
    from_str = msg.get("From", "")
    raw = f"{date_str}-{sub_str}-{from_str}".encode('utf-8', errors='ignore')
    return hashlib.md5(raw).hexdigest()


def get_target_existing_ids(tgt_client, tgt_folder):
    """Fetches Message-IDs of already uploaded emails in target folder."""
    encoded_folder = encode_mutf7(tgt_folder)
    status, _ = tgt_client.select(f'"{encoded_folder}"', readonly=True)
    if status != 'OK':
        return set()
    
    status, data = tgt_client.search(None, 'ALL')
    if status != 'OK' or not data[0]:
        return set()
    
    existing_ids = set()
    msg_nums = data[0].split()
    
    for i in range(0, len(msg_nums), 100):
        chunk = b','.join(msg_nums[i:i+100])
        status, headers_data = tgt_client.fetch(chunk, '(BODY[HEADER.FIELDS (MESSAGE-ID DATE SUBJECT FROM)])')
        if status == 'OK':
            for response in headers_data:
                if isinstance(response, tuple):
                    msg = email.message_from_bytes(response[1])
                    raw_msg_id = msg.get("Message-ID")
                    if raw_msg_id:
                        msg_id = str(raw_msg_id).strip()
                    else:
                        msg_id = generate_fallback_id(msg)
                    existing_ids.add(msg_id)
    return existing_ids


def ensure_target_folder(tgt_client, tgt_folder):
    """Ensures target IMAP folder exists."""
    encoded_folder = encode_mutf7(tgt_folder)
    status, _ = tgt_client.select(f'"{encoded_folder}"')
    if status != 'OK':
        tgt_client.create(f'"{encoded_folder}"')


def migrate():
    print(f"[*] Connecting to Apple iCloud IMAP ({SRC_USER})...")
    src_client = connect_imap(SRC_HOST, SRC_PORT, SRC_USER, SRC_PASS)
    
    print(f"[*] Connecting to Gmail IMAP ({TGT_USER})...")
    tgt_client = connect_imap(TGT_HOST, TGT_PORT, TGT_USER, TGT_PASS)
    
    status, folders = src_client.list()
    if status != 'OK':
        print("[!] Failed to list source folders.")
        return

    # Nur reine System-Ordner ignorieren (keine Wörter wie 'Archiv', die in Nutzerordnern vorkommen können)
    ignored_system_folders = {
        '[Gmail]', 'Junk', 'Trash', 'Deleted Messages', 'Drafts',
        'Papierkorb', 'Gelöschte E-Mails', 'Entwürfe', 'Spam',
        'Corbeille', 'Courrier indésirable', 'Brouillons',
        'Papelera', 'Correo no deseado', 'Borradores',
        'Cestino', 'Posta indesiderata', 'Bozze',
        'Prullenbak', 'Ongewenste e-mail', 'Concepten',
        'Lixeira', 'Lixo', 'Rascunhos',
        'Корзина', 'Спам', 'Черновики'
    }
    
    skip_mode = True if RESUME_FROM_FOLDER else False

    for folder_info in folders:
        raw_name = folder_info.decode('latin1').split(' "/" ')
        if len(raw_name) < 2:
            continue
        
        raw_folder = raw_name[1].strip('"')
        decoded_folder = decode_mutf7(raw_folder)
        
        # Exakter Vergleich der Pfadsegmente (damit 'Mein Archiv' NICHT ignoriert wird)
        path_parts = [p.strip() for p in decoded_folder.split('/')]
        if any(part in ignored_system_folders for part in path_parts):
            print(f"  [-] Ignoring system folder: {decoded_folder}")
            continue
            
        if skip_mode:
            if decoded_folder == RESUME_FROM_FOLDER:
                skip_mode = False
            else:
                print(f"  [-] Skipping folder: {decoded_folder}")
                continue
            
        print(f"\n[*] Processing folder: {decoded_folder} (Raw IMAP: {raw_folder})")
        
        status, _ = src_client.select(f'"{raw_folder}"', readonly=True)
        if status != 'OK':
            print(f"  [!] Could not select source folder {decoded_folder}")
            continue
            
        status, data = src_client.search(None, 'ALL')
        if status != 'OK' or not data[0]:
            print("  -> 0 messages found.")
            continue
            
        msg_nums = data[0].split()
        total_msgs = len(msg_nums)
        print(f"  -> Found {total_msgs} messages on source.")
        
        ensure_target_folder(tgt_client, decoded_folder)
        existing_ids = get_target_existing_ids(tgt_client, decoded_folder)
        
        uploaded = 0
        skipped = 0
        
        for msg_num in msg_nums:
            retries = 3
            while retries > 0:
                try:
                    status, msg_data = src_client.fetch(msg_num, '(RFC822 INTERNALDATE)')
                    if status != 'OK':
                        break
                        
                    raw_email = msg_data[0][1]
                    
                    if len(raw_email) > MAX_EMAIL_SIZE:
                        print(f"  [!] Skipping message {msg_num}: Size exceeds Gmail IMAP limit.")
                        break

                    internal_date = imaplib.Internaldate2tuple(msg_data[0][0])
                    msg = email.message_from_bytes(raw_email)
                    
                    raw_msg_id = msg.get("Message-ID")
                    if raw_msg_id:
                        msg_id = str(raw_msg_id).strip()
                    else:
                        msg_id = generate_fallback_id(msg)
                    
                    if msg_id in existing_ids:
                        skipped += 1
                        break
                        
                    encoded_target_folder = encode_mutf7(decoded_folder)
                    tgt_client.append(f'"{encoded_target_folder}"', None, internal_date, raw_email)
                    
                    existing_ids.add(msg_id)
                    uploaded += 1
                    break
                    
                except (imaplib.IMAP4.abort, ssl.SSLEOFError, OSError, socket.error) as e:
                    retries -= 1
                    if retries > 0:
                        print(f"  [!] Upload interrupted ({e}). Reconnecting Gmail (Attempt {3-retries}/3)...")
                        try:
                            tgt_client = connect_imap(TGT_HOST, TGT_PORT, TGT_USER, TGT_PASS)
                        except Exception:
                            pass
                    else:
                        print(f"  [!] Upload permanently failed for message {msg_num} after 3 retries: {e}")
        
        print(f"  -> Done: {uploaded} uploaded, {skipped} skipped (already migrated).")

    try:
        src_client.logout()
        tgt_client.logout()
    except Exception:
        pass


if __name__ == "__main__":
    migrate()
