# Apple iCloud Mail to Google Workspace Migration Tool

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Donate-orange.svg)](https://www.buymeacoffee.com/agent47.scripts)

A resilient, single-threaded Python tool designed to migrate email archives from Apple iCloud Mail to Google Workspace / Gmail via IMAP. 

It preserves original message timestamps (`INTERNALDATE`), decodes mUTF-7 folder structures accurately, and implements auto-reconnect logic with duplicate prevention to handle server throttling reliably.

---

## 🛑 Important Security Notice

**Never hardcode plain text passwords into scripts or documentation!**

Both Apple iCloud and Google Workspace require **App-Specific Passwords** when accessing IMAP services programmatically.

### How to Generate App-Specific Passwords:

1. **Apple iCloud Mail (Source):**
   * Go to [Apple ID Account Management](https://appleid.apple.com/)
   * Sign in > **Sign-In and Security** > **App-Specific Passwords**
   * Create a new password for this migration tool.

2. **Google Workspace / Gmail (Target):**
   * Ensure 2-Step Verification is enabled in your [Google Account Security Settings](https://myaccount.google.com/security)
   * Go directly to [Google App Passwords](https://myaccount.google.com/apppasswords)
   * Generate a dedicated password for "Mail" / "Custom Name".

---

## ⚠️ Recommended Usage & Archive Limits

This Python script is lightweight, easy to inspect, and tailored for **small to medium email archives**:

- **Optimal Scope:** Perfect for individual folders or total mailbox sizes **up to ~1 GB** (or ~1,000 to 2,000 emails).
- **Rate-Limiting Reality:** Due to strict IMAP bandwidth throttling by Google and Apple, single-threaded Python transfers process roughly **250–300 emails per hour (~1 GB per 3 hours)**.
- **For Large Mailbox Archives (>1 GB / >3,000 Mails):** If you are migrating full multi-gigabyte archives with tens of thousands of emails, we recommend using a high-throughput, multithreaded IMAP tool (such as `imapsync`). *(A dedicated pipeline configuration for large-scale migrations is currently in development).*

---

## ✨ Features

* **Original Timestamp Preservation:** Applies the original `Date` header from source emails directly to the IMAP `APPEND` command so that historical emails land chronologically in Gmail.
* **Folder Structure Decoding:** Native handling and decoding of modified UTF-7 (`mUTF-7`) encoded folder names (e.g., handling umlauts like `ä`, `ö`, `ü` and special characters).
* **Automatic Reconnection:** Automatically catches broken connections, network timeouts, or server dropouts, performing up to 3 retry attempts per batch.
* **Duplicate Prevention:** Tracks migrated `Message-ID` headers (falling back to a hash of Date/Subject/Sender if missing) to safely allow script restarts without creating duplicate emails in Gmail.

---

## 🚀 Setup & Execution

### 1. Prerequisites
Ensure Python 3 is installed on your system. No external pip modules are strictly required (uses built-in `imaplib`, `email`, `ssl`, and `hashlib`).

### 2. Environment Variables
To keep your credentials secure, pass them via environment variables instead of storing them in the script:

```bash
export SRC_USER="your-apple-id@icloud.com"
export SRC_PASS="xxxx-xxxx-xxxx-xxxx"   # Apple App-Specific Password

export TGT_USER="your-email@yourdomain.com"
export TGT_PASS="xxxxxxxxxxxxxxxx"      # Google App Password
```

### 3. Run the Script
Execute the script directly from your terminal:

```bash
python3 migrate_all.py
```

---

## 🛠️ Troubleshooting & System Stability

* **Mac/System Sleep:** Ensure system sleep and display idle timeouts are disabled during execution, as unexpected system suspension can disrupt active IMAP streams.
* **IMAP Throttling / Drops:** If Google briefly interrupts the connection (*"Upload interrupted. Reconnecting..."*), the built-in auto-retry mechanism will re-establish the socket automatically.

---

## 📄 License

This project is licensed under the **MIT License**. See the `LICENSE` file in the repository for full details.
