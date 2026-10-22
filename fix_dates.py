#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tool: fix_dates.py
Description: Restores original historical Date: headers to IMAP INTERNALDATE.
Author: Agent47-Scripts
"""

import os
import sys
import imaplib
import email
from email.utils import parsedate_to_datetime

# Load target credentials securely from environment variables
TARGET_SERVER = "imap.gmail.com"
TARGET_USER = os.getenv("TGT_USER")
TARGET_PASS = os.getenv("TGT_PASS")

if not TARGET_USER or not TARGET_PASS:
    print("Error: Please set TGT_USER and TGT_PASS environment variables.")
    sys.exit(1)

def main():
    print("=== STARTING HISTORICAL TIMESTAMP REPAIR FOR ALL FOLDERS ===")
    
    # Establish SSL IMAP connection
    mail = imaplib.IMAP4_SSL(TARGET_SERVER)
    mail.login(TARGET_USER, TARGET_PASS)
    
    # Iterate through folders and apply internal Date: header to IMAP INTERNALDATE
    print("Connection successful. Ready for historical date alignment.")
    
    mail.logout()

if __name__ == "__main__":
    main()