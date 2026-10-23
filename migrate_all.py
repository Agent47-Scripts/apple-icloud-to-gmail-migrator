#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
Apple iCloud Mail to Google Workspace / Gmail Migration Pipeline
==============================================================================
Author:      Tino Höhne
Repository:  Agent47-Scripts/Apple-Mail-to-Google-Workspace-Migration
License:     MIT License

Description:
  All-in-one Python script to migrate full folder hierarchies and email archives 
  from Apple iCloud Mail to Google Workspace or Gmail over IMAP. 
  
  Key Features:
  - Preserves original internal timestamps (INTERNALDATE) during transfer.
  - Automatically handles custom IMAP folder structures and special characters (&).
  - Robust exception handling for empty responses and duplicate folder creation.
  - Secure credential handling via system environment variables.
==============================================================================
"""

import os
import imaplib
import email

# Retrieve authentication credentials from environment variables
SRC_USER = os.getenv("SRC_USER")
SRC_PASS = os.getenv("SRC_PASS")
TGT_USER = os.getenv("TGT_USER")
TGT_PASS = os.getenv("TGT_PASS")

# Validate environment variables
if not all([SRC_USER, SRC_PASS, TGT_USER, TGT_PASS]):
    print("ERROR: Missing required environment variables!")
    print("Please set SRC_USER, SRC_PASS, TGT_USER, and TGT_PASS before running this script.")
    exit(1)

# Connect to source server (Apple iCloud IMAP)
print(f"[*] Connecting to Apple iCloud IMAP ({SRC_USER})...")
src = imaplib.IMAP4_SSL("imap.mail.me.com")
src.login(SRC_USER, SRC_PASS)

# Connect to target server (Google Workspace / Gmail IMAP)
print(f"[*] Connecting to Gmail IMAP ({TGT_USER})...")
tgt = imaplib.IMAP4_SSL("imap.gmail.com")
tgt.login(TGT_USER, TGT_PASS)

print("\n[=== PHASE 1: Executing Mail Synchronization ===]")
status, mailboxes = src.list()

if status == "OK":
    for mb in mailboxes:
        # Extract folder name from IMAP response
        raw_name = mb.decode().split(' "/" ')[-1].strip()
        folder_name = raw_name.strip('"')
        
        # Skip system folders and trash
        if folder_name.lower() in ["junk", "trash", "deleted messages", "notes"]:
            continue

        print(f"\n[*] Processing folder: {folder_name}")
        
        # Select source folder in read-only mode
        status_src, _ = src.select(f'"{folder_name}"', readonly=True)
        if status_src != "OK":
            print(f"  -> Failed to open folder on iCloud. Skipping.")
            continue

        # Format folder name safely for Gmail IMAP (Escape unescaped '&' characters)
        formatted_folder_name = folder_name.replace('&', '&-') if '&' in folder_name and '&-' not in folder_name else folder_name

        # Create corresponding target folder on Gmail safely
        try:
            tgt.create(f'"{formatted_folder_name}"')
        except Exception:
            pass  # Folder might already exist or be created automatically
        
        # Search for all messages within the current folder
        search_status, msg_nums = src.search(None, "ALL")
        if search_status != "OK" or not msg_nums or not msg_nums[0]:
            print("  -> 0 messages found.")
            continue

        nums = msg_nums[0].split()
        print(f"  -> Found {len(nums)} messages.")

        # Iterate through messages and append to target IMAP server
        for num in nums:
            _, data = src.fetch(num, "(RFC822 INTERNALDATE)")
            if not data or not data[0]:
                continue
            
            raw_email = None
            internal_date = None
            
            for response_part in data:
                if isinstance(response_part, tuple):
                    raw_email = response_part[1]
                    for item in response_part:
                        if isinstance(item, bytes) and b"INTERNALDATE" in item:
                            try:
                                internal_date = imaplib.Internaldate2tuple(item)
                            except Exception:
                                pass

            if raw_email:
                try:
                    tgt.append(f'"{formatted_folder_name}"', None, internal_date, raw_email)
                except Exception as e:
                    print(f"     Failed to append message: {e}")

print("\n[+] Migration process successfully completed!")

# Close connections cleanly
src.logout()
tgt.logout()
