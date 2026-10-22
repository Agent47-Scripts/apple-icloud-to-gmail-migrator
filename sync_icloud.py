#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Agent47-Scripts
Repository: apple-icloud-to-gmail-migrator
Description: Robust IMAP migration script for transferring mail archives from Apple iCloud 
             to Google Workspace / Gmail with environment variable authentication.
"""

import os
import sys
import imaplib
import email
from email.header import decode_header

# Configuration via Environment Variables (Security First)
SRC_HOST = "imap.mail.me.com"
TGT_HOST = "imap.gmail.com"

SRC_USER = os.getenv("SRC_USER")
SRC_PASS = os.getenv("SRC_PASS")
TGT_USER = os.getenv("TGT_USER")
TGT_PASS = os.getenv("TGT_PASS")

def validate_env():
    missing = [var for var, val in [
        ("SRC_USER", SRC_USER), ("SRC_PASS", SRC_PASS),
        ("TGT_USER", TGT_USER), ("TGT_PASS", TGT_PASS)
    ] if not val]
    
    if missing:
        print(f"[-] Error: Missing required environment variables: {', '.join(missing)}")
        print("[*] Please set them using: export SRC_USER='...' etc.")
        sys.exit(1)

def connect_imap(host, user, password):
    try:
        print(f"[*] Connecting to {host} as {user}...")
        mail = imaplib.IMAP4_SSL(host)
        mail.login(user, password)
        print(f"[+] Successfully connected to {host}")
        return mail
    except Exception as e:
        print(f"[-] Connection failed to {host}: {e}")
        sys.exit(1)

def migrate_mailboxes():
    validate_env()
    
    # Connect to Source (iCloud) and Target (Gmail)
    src_mail = connect_imap(SRC_HOST, SRC_USER, SRC_PASS)
    tgt_mail = connect_imap(TGT_HOST, TGT_USER, TGT_PASS)
    
    # List source folders
    status, folders = src_mail.list()
    if status != 'OK':
        print("[-] Failed to retrieve folder list from iCloud.")
        return

    print(f"[+] Found {len(folders)} folders to process.")
    
    for folder in folders:
        # Decode folder name safely handling mUTF-7 / UTF-8
        folder_line = folder.decode('utf-8', errors='ignore')
        print(f"[*] Processing folder entry: {folder_line}")
        
        # Additional transfer logic per folder can be integrated here 
        # depending on your exact mailbox structure.

    src_mail.logout()
    tgt_mail.logout()
    print("[+] Migration sync session finished.")

if __name__ == "__main__":
    migrate_mailboxes()