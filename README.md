# Apple iCloud Mail to Gmail / Workspace Migration Tools

> **Background & Purpose:** I created these scripts after going through the painful process of migrating a massive, decades-old Apple Mail / iCloud IMAP archive to Google Workspace on Linux (Ubuntu Budgie). My goal is to save you the countless hours of research, trial-and-error, and frustrating roadblocks I had to go through.

---

## 🚀 Key Features & Problem Solvers

* **Main Migration Engine (`sync_icloud.py`):** Robust, interruption-tolerant IMAP migration script for transferring mail archives from Apple iCloud to Google Workspace / Gmail.
* **mUTF-7 Folder Encoding Fix:** Apple Mail uses specialized mUTF-7 encoding for non-ASCII characters and umlauts (`ä`, `ö`, `ü`, `ß`). Standard IMAP tools often create duplicated, corrupted folder trees.
* **Safe Duplicate Purging (`force_delete_dupes.py`):** Identifies and deletes orphan mUTF-7 duplicate folder structures directly on the target IMAP server without losing unique messages.
* **Historical Timestamp Fixer (`fix_dates.py`):** Re-applies the original internal `Date:` header to historical emails, ensuring correct chronological order in the target web interface.
* **Security First (No Hardcoded Credentials):** Credentials are passed strictly via system environment variables (`os.getenv`) — no hardcoded passwords in the source code.
* **Interruption Tolerant:** Designed to be safely re-run if network or server connections drop out.

---

## 🔑 Prerequisites & Authentication (As of 2026)

For security reasons, modern email providers do not allow standard account passwords for automated script access. You need **App-Specific Passwords**.

### Target Account (e.g., Google Workspace / Gmail)
1. Go to your Google Account settings (**Security** -> **2-Step Verification** must be enabled).
2. Scroll down to **App passwords**.
3. Create a new app password (named e.g. "IMAP Migration"), copy the 16-character code, and use it as your target password.

### Source Account (e.g., Apple iCloud)
1. Go to your Apple ID account page (`appleid.apple.com`).
2. Under **Sign-In and Security**, select **App-Specific Passwords**.
3. Generate a password for this migration tool and keep it handy.

---

## ⚙️ Usage Workflow

### 1. Set Environment Variables
Set your source and target credentials securely in your Linux terminal before running any commands:

```bash
# Source Account (Apple iCloud)
export SRC_USER="your-apple-id@icloud.com"
export SRC_PASS="your-apple-app-password"

# Target Account (Google Workspace / Gmail)
export TGT_USER="your-email@gmail.com"
export TGT_PASS="your-google-app-password"
```

### 2. Run Main Sync Script
Execute the primary transfer script to copy folders and email archives from iCloud to Gmail:

```bash
python3 sync_icloud.py
```

### 3. Purge Corrupted mUTF-7 Folders
Run the duplicate cleanup script to remove redundant or orphaned mUTF-7 folder structures:

```bash
python3 force_delete_dupes.py
```

### 4. Restore Historical Mail Timestamps
After the folder structure is clean, execute the timestamp repair script to fix internal email web display dates:

```bash
python3 fix_dates.py
```

---

## ⏱️ Execution Time & Performance Considerations

Please be aware that IMAP operations on large historical email archives are **time-intensive**:

* **Estimated Speed:** Expect roughly **1 to 3 hours per Gigabyte** (or per ~10,000 emails), depending on your account size and server limits.
* **Why does it take so long?** It is not strictly limited by your local internet speed. Major providers (like Google and Apple) enforce strict **IMAP Rate Limits (Throttling)** to prevent server overload. Every single folder and email header requires direct server-side verification.
* **Universal Issue (Not just German/Apple):** While this repository focuses on Apple-to-Gmail migrations, folder encoding issues with mUTF-7 affect **all non-ASCII languages** (e.g., Spanish accents like `ñ`, `á`, `é`, French, Cyrillic, etc.) and apply to almost any cross-provider IMAP migration.
* **Recommendation:** Let the scripts run uninterrupted in a background terminal session.

---

## 💡 Troubleshooting & AI Assistance

If you encounter unexpected errors, missing modules, or server timeouts while running these scripts:
* **Don't hesitate to use an AI (like Gemini or ChatGPT):** Paste the error message and the respective script into the chat.
* These scripts are intentionally written in a clean, modular, and compact format specifically so that AIs can easily read, debug, and adapt them for your individual mailbox structure within seconds.

---

## 📜 License

Licensed under the [MIT License](LICENSE). Free to use, adapt, and share.