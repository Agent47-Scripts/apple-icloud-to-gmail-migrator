# Apple iCloud Mail to Gmail / Workspace Migration Tools

> **Background & Purpose:** I created these scripts after going through the painful process of migrating a massive, decades-old Apple Mail / iCloud IMAP archive to Google Workspace on Linux (Ubuntu Budgie). My goal is to save you the countless hours of research, trial-and-error, and frustrating roadblocks I had to go through. 

---

## 🚀 Key Features & Problem Solvers

* **mUTF-7 Folder Encoding Fix:** Apple Mail uses specialized mUTF-7 encoding for non-ASCII characters and umlauts (`ä`, `ö`, `ü`, `ß`). Standard IMAP tools often create duplicated, corrupted folder trees.
* **Safe Duplicate Purging (`force_delete_dupes.py`):** Identifies and deletes orphan mUTF-7 duplicate folder structures directly on the target IMAP server without losing unique messages.
* **Historical Timestamp Fixer (`fix_dates.py`):** Re-applies the original internal `Date:` header to historical emails, ensuring correct chronological order in the target web interface.
* **Security First (No Hardcoded Credentials):** Credentials are passed strictly via system environment variables (`os.getenv`) — no hardcoded passwords in the source code.
* **Interruption Tolerant:** Designed to be safely re-run if network or server connections drop out.

---

## 🔑 Prerequisites & Authentication (As of 2026)

For security reasons, modern email providers do not allow standard account passwords for automated script access. You need **App-Specific Passwords**.

### Target Account (e.g., Google Workspace / Gmail)
1. Go to your Google Account settings (**Security** $\rightarrow$ **2-Step Verification** must be enabled).
2. Scroll down to **App passwords**.
3. Create a new app password (named e.g. "IMAP Migration"), copy the 16-character code, and use it as your target password.

### Source Account (e.g., Apple iCloud)
1. Go to your Apple ID account page (`appleid.apple.com`).
2. Under **Sign-In and Security**, select **App-Specific Passwords**.
3. Generate a password for this migration tool and keep it handy.

---

## ⚙️ Usage

### 1. Set Environment Variables
Set your target credentials securely in your Linux terminal before running any script:

```bash
export TGT_USER="your-email@gmail.com"
export TGT_PASS="your-16-digit-app-password"
