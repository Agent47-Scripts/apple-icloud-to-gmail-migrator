#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
Gmail In-Place IMAP Timestamp Fixer & Re-Uploader (Bulletproof)
================================================================================
Author:       Tino Höhne
Repository:   Agent47-Scripts/Gmail-IMAP-Timestamp-Fixer
Version:      1.0.3
License:      MIT License

Description:
Standalone utility script designed to repair incorrect internal timestamps
(INTERNALDATE) on emails already uploaded to Gmail / Google Workspace.

Since IMAP servers do not allow mutating the INTERNALDATE of an existing message,
this script performs an in-place migration per message:
1. Fetches the raw email body and parses the original RFC2822 'Date' header.
2. Converts the parsed header into a native datetime object.
3. Appends the exact message back to the same folder with the corrected timestamp.
4. Marks the original message with the incorrect timestamp as DELETED and EXPUNGES it immediately.
================================================================================
"""

__version__ = "1.0.3"

import os
import sys
import time
import socket
import ssl
import imaplib
import email
import hashlib
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# ==============================================================================
# 1. ENVIRONMENT CONFIGURATION & VALIDATION
# ==============================================================================
# Retrieve target credentials securely from environment variables.
# Fallback support is provided for both TGT_* and GMAIL_* variable names.
GMAIL_USER = os.getenv("TGT_USER") or os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("TGT_PASS") or os.getenv("GMAIL_PASS")

# Terminate execution early if authentication credentials are not provided.
if not all([GMAIL_USER, GMAIL_PASS]):
    print("ERROR: Missing required environment variables (TGT_USER/GMAIL_USER, TGT_PASS/GMAIL_PASS)!")
    sys.exit(1)

# Enforce Gmail's maximum IMAP APPEND size limit (~24.5 MB to account for base64 encoding overhead).
MAX_EMAIL_SIZE = 24.5 * 1024 * 1024

# Gmail IMAP Server Endpoint.
GMAIL_HOST = "imap.gmail.com"
GMAIL_PORT = 993


# ==============================================================================
# 2. PROTOCOL & UTILITY HELPER FUNCTIONS
# ==============================================================================

def connect_imap(host, port, user, password):
    """
    Establishes a secure SSL/TLS IMAP connection wrapped in an infinite retry loop.
    This prevents script termination during transient network drops or IMAP socket timeouts.
    """
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
    """
    Safely decodes mUTF-7 encoded IMAP folder names (e.g. containing German umlauts,
    accents, or special characters) into standard Unicode strings.
    Includes robust fallback for malformed or unclosed sequence bytes.
    """
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
    """
    Encodes standard Unicode folder names back into mUTF-7 format as required
    by IMAP specifications for folder selection, creation, and append commands.
    """
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


# ==============================================================================
# 3. TIMESTAMP FIXING PIPELINE
# ==============================================================================

def fix_timestamps():
    """
    Main orchestration loop for inspecting IMAP folders, extracting RFC2822 dates,
    re-uploading messages with corrected timestamps, and removing stale duplicates.
    """
    print(f"[*] Connecting to Gmail IMAP ({GMAIL_USER})...")
    client = connect_imap(GMAIL_HOST, GMAIL_PORT, GMAIL_USER, GMAIL_PASS)
    
    # Retrieve all mailbox folders from the Gmail target account
    status, folders = client.list()
    if status != 'OK':
        print("[!] Failed to retrieve Gmail folders.")
        return

    # Multi-language set of system folders to exclude from timestamp processing
    ignored_system_folders = {
        '[Gmail]', 'Junk', 'Trash', 'Deleted Messages', 'Drafts',
        'Papierkorb', 'Gelöschte E-Mails', 'Entwürfe', 'Spam',
        'Corbeille', 'Courrier indésirable', 'Brouillons',
        'Papelera', 'Correo no deseado', 'Borradores'
    }

    # Iterate through all discovered folders on the IMAP server
    for folder_info in folders:
        raw_name = folder_info.decode('latin1').split(' "/" ')
        if len(raw_name) < 2:
            continue
        
        raw_folder = raw_name[1].strip('"')
        decoded_folder = decode_mutf7(raw_folder)
        
        # Check folder hierarchy against system exclusions
        path_parts = [p.strip() for p in decoded_folder.split('/')]
        if any(part in ignored_system_folders for part in path_parts):
            print(f"  [-] Skipping system folder: {decoded_folder}")
            continue

        # Select target folder in read-write mode to enable STORE and EXPUNGE commands
        encoded_folder = encode_mutf7(decoded_folder)
        status, _ = client.select(f'"{encoded_folder}"', readonly=False)
        if status != 'OK':
            print(f"  [!] Could not select folder: {decoded_folder}")
            continue

        # Fetch message sequence numbers within current folder
        status, data = client.search(None, 'ALL')
        if status != 'OK' or not data[0]:
            print(f"\n[*] Folder: {decoded_folder} -> 0 messages found.")
            continue

        msg_nums = data[0].split()
        total_msgs = len(msg_nums)
        print(f"\n[*] Processing folder: {decoded_folder} ({total_msgs} messages)")

        fixed_count = 0
        skipped_count = 0

        # CRITICAL: Iterate through messages in REVERSE order.
        # Immediate EXPUNGE calls modify message sequence numbers.
        # Processing backwards guarantees that earlier message indices remain intact and unaltered.
        for msg_num in reversed(msg_nums):
            retries = 3
            while retries > 0:
                try:
                    # Fetch full raw MIME body for parsing and re-uploading
                    status, msg_data = client.fetch(msg_num, '(RFC822)')
                    if status != 'OK' or not msg_data or not msg_data[0]:
                        break

                    raw_email = msg_data[0][1]
                    if len(raw_email) > MAX_EMAIL_SIZE:
                        print(f"  [!] Skipping message {msg_num.decode()}: Exceeds size limit.")
                        break

                    # Extract original RFC2822 'Date' header from MIME structure
                    msg_obj = email.message_from_bytes(raw_email)
                    date_header = msg_obj.get("Date")

                    if not date_header:
                        skipped_count += 1
                        break

                    try:
                        dt_object = parsedate_to_datetime(date_header)
                    except Exception:
                        dt_object = None

                    if not dt_object:
                        skipped_count += 1
                        break

                    # 1. Re-upload email message appended natively with Python 3.12 datetime support
                    status, _ = client.append(f'"{encoded_folder}"', flags=None, date_time=dt_object, message=raw_email)
                    if status == 'OK':
                        # 2. Mark original message as \Deleted internally via IMAP command and purge immediately
                        client.store(msg_num, '+FLAGS', '\\Deleted')
                        client.expunge()
                        fixed_count += 1
                    else:
                        print(f"  [!] Failed to append message {msg_num.decode()}")

                    # Rate-limiting delay to prevent triggering Google IMAP socket throttling
                    time.sleep(0.3)
                    break

                except (imaplib.IMAP4.abort, ssl.SSLEOFError, OSError, socket.error) as e:
                    retries -= 1
                    if retries > 0:
                        print(f"  [!] Connection interrupted ({e}). Reconnecting (Attempt {3-retries}/3)...")
                        try:
                            client = connect_imap(GMAIL_HOST, GMAIL_PORT, GMAIL_USER, GMAIL_PASS)
                            client.select(f'"{encoded_folder}"', readonly=False)
                        except Exception:
                            pass
                    else:
                        print(f"  [!] Failed processing message {msg_num.decode()} after retries.")

        print(f"  -> Done with {decoded_folder}: {fixed_count} timestamps repaired, {skipped_count} skipped.")

    # Gracefully terminate session upon completion
    try:
        client.logout()
    except Exception:
        pass


if __name__ == "__main__":
    fix_timestamps()
