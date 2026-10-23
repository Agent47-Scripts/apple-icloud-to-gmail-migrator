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
  All-in-one script to migrate full folder hierarchies and emails from Apple 
  iCloud Mail to Google Workspace or Gmail over IMAP. Restores original email 
  timestamps (INTERNALDATE) during transfer.
==============================================================================
"""

import os
import imaplib
import email

SRC_USER = os.getenv("SRC_USER")
SRC_PASS = os.getenv("SRC_PASS")
TGT_USER = os.getenv("TGT_USER")
TGT_PASS = os.getenv("TGT_PASS")

if not all([SRC_USER, SRC_PASS, TGT_USER, TGT_PASS]):
    print("FEHLER: SRC_USER, SRC_PASS, TGT_USER oder TGT_PASS fehlen!")
    print("Bitte vorher 'export SRC_USER=...', etc. im Terminal ausführen.")
    exit(1)

print(f"[*] Verbinde mit iCloud ({SRC_USER})...")
src = imaplib.IMAP4_SSL("imap.mail.me.com")
src.login(SRC_USER, SRC_PASS)

print(f"[*] Verbinde mit Gmail ({TGT_USER})...")
tgt = imaplib.IMAP4_SSL("imap.gmail.com")
tgt.login(TGT_USER, TGT_PASS)

print("\n[=== PHASE 1: Mail Sync ===]")
status, mailboxes = src.list()

if status == "OK":
    for mb in mailboxes:
        raw_name = mb.decode().split(' "/" ')[-1].strip()
        folder_name = raw_name.strip('"')
        
        # System-Ordner überspringen
        if folder_name.lower() in ["junk", "trash", "deleted messages", "notes"]:
            continue

        print(f"\n[*] Verarbeite Ordner: {folder_name}")
        
        # Quell-Ordner selektieren
        status_src, _ = src.select(f'"{folder_name}"', readonly=True)
        if status_src != "OK":
            print(f"  -> Fehler beim Öffnen auf iCloud, überspringe.")
            continue

        # Ziel-Ordner erstellen
        tgt.create(f'"{folder_name}"')
        
        # Mails suchen
        _, msg_nums = src.search(None, "ALL")
        nums = msg_nums[0].split()
        print(f"  -> {len(nums)} Mails gefunden.")

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
                    tgt.append(f'"{folder_name}"', None, internal_date, raw_email)
                except Exception as e:
                    print(f"     Fehler beim Kopieren einer Mail: {e}")

print("\n[+] Migration erfolgreich abgeschlossen!")
src.logout()
tgt.logout()