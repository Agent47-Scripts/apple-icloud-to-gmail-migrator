#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
Apple iCloud Mail to Google Workspace / Gmail Migration Pipeline (Bulletproof)
==============================================================================
Author:      Tino Höhne
Repository:  Agent47-Scripts/Apple-Mail-to-Google-Workspace-Migration
License:     MIT License

Description:
  Production-grade IMAP migration script with auto-reconnect, size limits,
  mUTF-7 decoding/encoding fixes, and robust fallback duplicate checking.
==============================================================================
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

# Limit for Gmail IMAP APPEND (approx 24.5 MB to be safe with encoding overhead)
MAX_EMAIL_SIZE = 24.5 * 1024 * 1024  

def connect_imap(host, user, password):
    """Establishes SSL IMAP connection with automatic retry."""
    while True:
        try:
            conn = imaplib.IMAP4_SSL(host)
            conn.login(user, password)
            return conn
        except Exception as e:
            print(f"  [!] Connection failed to {host} ({e}). Retrying in 5 seconds...")
            time.sleep(5)

def decode_mutf7(encoded_str):
    """Safely decodes mUTF-7 encoded IMAP folder names."""
    try:
        # Standard conversion for IMAP modified UTF-7
        res = []
        b = encoded_str.encode('ascii')
        i = 0
        while i < len(b):
            if b[i:i+1] == b'&':
                j = b.find(b'-', i)
                if j == -1:
                    res.append(b[i:])
                    break
                if j == i + 1:
                    res.append(b'&')
                else:
                    sub = b[i+1:j].replace(b',', b'/')
                    pad = (-len(sub)) % 4
                    sub += b'=' * pad
                    import base64
                    res.append(base64.b64decode(sub).decode('utf-16be'))
                i = j + 1
            else:
                res.append(chr(b[i]))
                i += 1
        return "".join(res)
    except Exception:
        return encoded_str

def format_imap_date(raw_email):
    """Extracts original email date header and converts to IMAP INTERNALDATE."""
    try:
        msg = email.message_from_bytes(raw_email)
        date_str = msg.get("Date")
        if date_str:
            dt = parsedate_to_datetime(date_str)
            return imaplib.Time2Internaldate(dt.timestamp())
    except Exception:
        pass
    return imaplib.Time2Internaldate(time.time())

def generate_fallback_id(msg):
    """Generates a unique hash if Message-ID header is missing."""
    subject = str(msg.get("Subject", ""))
    date = str(msg.get("Date", ""))
    from_addr = str(msg.get("From", ""))
    raw_sig = f"{subject}-{date}-{from_addr}"
    return hashlib.md5(raw_sig.encode("utf-8")).hexdigest()

# Connect to servers
print(f"[*] Connecting to Apple iCloud IMAP ({SRC_USER})...")
src = connect_imap("imap.mail.me.com", SRC_USER, SRC_PASS)

print(f"[*] Connecting to Gmail IMAP ({TGT_USER})...")
tgt = connect_imap("imap.gmail.com", TGT_USER, TGT_PASS)

print("\n[=== PHASE 1: Executing Mail Synchronization ===]")
status, mailboxes = src.list()

if status == "OK":
    for mb in mailboxes:
        raw_name = mb.decode().split(' "/" ')[-1].strip()
        folder_name = raw_name.strip('"')
        
        # Skip garbage and system folders
        if folder_name.lower() in ["junk", "trash", "deleted messages", "notes"]:
            continue

        decoded_folder_display = decode_mutf7(folder_name)
        print(f"\n[*] Processing folder: {decoded_folder_display} (Raw IMAP: {folder_name})")
        
        # Try selecting source folder (auto-reconnect on socket drop)
        while True:
            try:
                status_src, _ = src.select(f'"{folder_name}"', readonly=True)
                break
            except (imaplib.IMAP4.abort, socket.error, ssl.SSLError):
                print("  [!] Connection lost to iCloud. Reconnecting...")
                src = connect_imap("imap.mail.me.com", SRC_USER, SRC_PASS)

        if status_src != "OK":
            print("  -> Failed to open folder on iCloud. Skipping.")
            continue

        # Format target folder for Gmail safely
        formatted_tgt = folder_name.replace('&', '&-') if '&' in folder_name and '&-' not in folder_name else folder_name

        # Create target folder in Gmail
        try:
            tgt.create(f'"{formatted_tgt}"')
        except Exception:
            pass

        # Select target folder (auto-reconnect)
        while True:
            try:
                status_tgt, _ = tgt.select(f'"{formatted_tgt}"')
                break
            except (imaplib.IMAP4.abort, socket.error, ssl.SSLError):
                print("  [!] Connection lost to Gmail. Reconnecting...")
                tgt = connect_imap("imap.gmail.com", TGT_USER, TGT_PASS)

        # Build in-memory set of existing Message-IDs in Gmail target folder
        existing_ids = set()
        if status_tgt == "OK":
            _, tgt_ids = tgt.search(None, "ALL")
            if tgt_ids and tgt_ids[0]:
                for t_num in tgt_ids[0].split():
                    try:
                        _, tgt_hdr = tgt.fetch(t_num, "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])")
                        if tgt_hdr and isinstance(tgt_hdr[0], tuple):
                            hdr_text = tgt_hdr[0][1].decode(errors='ignore').strip()
                            if hdr_text:
                                # Extract raw ID string
                                clean_id = hdr_text.replace("Message-ID:", "").replace("message-id:", "").strip()
                                existing_ids.add(clean_id)
                    except Exception:
                        pass

        # Search messages in source folder
        search_status, msg_nums = src.search(None, "ALL")
        if search_status != "OK" or not msg_nums or not msg_nums[0]:
            print("  -> 0 messages found.")
            continue

        nums = msg_nums[0].split()
        print(f"  -> Found {len(nums)} messages on source.")

        uploaded_count = 0
        skipped_count = 0

        for num in nums:
            # Fetch message data securely
            try:
                _, data = src.fetch(num, "(RFC822)")
            except (imaplib.IMAP4.abort, socket.error, ssl.SSLError):
                print("  [!] Connection interrupted during fetch. Reconnecting...")
                src = connect_imap("imap.mail.me.com", SRC_USER, SRC_PASS)
                src.select(f'"{folder_name}"', readonly=True)
                _, data = src.fetch(num, "(RFC822)")

            if not data or not data[0] or not isinstance(data[0], tuple):
                continue
            
            raw_email = data[0][1]

            # 1. Size Check
            if len(raw_email) > MAX_EMAIL_SIZE:
                print(f"  [!] Skipping mail #{num.decode()}: Exceeds Gmail 25MB limit ({round(len(raw_email)/1024/1024, 2)} MB)")
                with open("skipped_large_mails.log", "a") as log:
                    log.write(f"Folder: {decoded_folder_display} | Msg NUM: {num.decode()}\n")
                continue

            msg = email.message_from_bytes(raw_email)
            msg_id = msg.get("Message-ID", "").strip() if msg.get("Message-ID") else generate_fallback_id(msg)

            # 2. Duplicate Check
            if msg_id in existing_ids:
                skipped_count += 1
                continue

            internal_date = format_imap_date(raw_email)

            # 3. Upload with auto-retry
            upload_success = False
            for attempt in range(3):
                try:
                    tgt.append(f'"{formatted_tgt}"', None, internal_date, raw_email)
                    upload_success = True
                    uploaded_count += 1
                    existing_ids.add(msg_id)
                    break
                except (imaplib.IMAP4.abort, socket.error, ssl.SSLError):
                    print(f"  [!] Upload interrupted. Reconnecting Gmail (Attempt {attempt+1}/3)...")
                    tgt = connect_imap("imap.gmail.com", TGT_USER, TGT_PASS)
                    tgt.select(f'"{formatted_tgt}"')
                except Exception as e:
                    print(f"     Failed to append message: {e}")
                    break

        print(f"  -> Done: {uploaded_count} uploaded, {skipped_count} skipped (already migrated).")

print("\n[+] Migration process successfully completed!")
try:
    src.logout()
    tgt.logout()
except Exception:
    pass
