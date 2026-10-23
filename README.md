# Apple iCloud Mail to Gmail / Workspace Migration Tools

> **Background & Purpose:** I created this all-in-one tool after going through the process of migrating an Apple Mail / iCloud IMAP archive to Google Workspace on Linux (Ubuntu Budgie). My goal is to save you time, trial-and-error, and frustrating roadblocks.

---

<p align="center">
  <a href="https://www.buymeacoffee.com/agent47.scripts" target="_blank" rel="noopener noreferrer">
    <img src="https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Donate-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black" alt="Buy Me A Coffee">
  </a>
</p>

---

## 🚀 Key Features & Problem Solvers

- **All-in-One Pipeline (`icloud_to_gmail_migrator.py`):** Handles synchronization, mUTF-7 duplicate purging, and historical timestamp fixing in a single, streamlined execution flow.
- **Resumable & Fault-Tolerant:** Interrupted by an IMAP timeout or network drop? Simply re-run the script. It automatically detects existing messages via `Message-ID` checking and resumes exactly where it left off.
- **mUTF-7 Folder Encoding Fix:** Apple Mail uses specialized mUTF-7 encoding for non-ASCII characters and umlauts (`ä`, `ö`, `ü`, `ß`). Standard IMAP tools often create duplicated, corrupted folder trees, which are automatically cleaned up.
- **Historical Timestamp Fixer:** Re-applies the original internal `Date:` header to historical emails, ensuring correct chronological order in the target web interface.
- **Security First (No Hardcoded Credentials):** Credentials are passed strictly via system environment variables (`os.getenv`) — no hardcoded passwords in the source code.

---

## 🔑 Prerequisites & Authentication

For security reasons, modern email providers do not allow standard account passwords for automated script access. You need **App-Specific Passwords**.

### Target Account (e.g., Google Workspace / Gmail)
1. Go to your <a href="https://myaccount.google.com/security" target="_blank" rel="noopener noreferrer">Google Account Settings</a> (**Security** -> **2-Step Verification** must be enabled).
2. Direct link to generate: <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener noreferrer">Google App Passwords</a>.
3. Create a new app password (named e.g. "IMAP Migration").
4. Copy the **16-digit code** (without spaces/hyphens, e.g. `abcd1234efgh5678`).

### Source Account (e.g., Apple iCloud)
1. Go to your <a href="https://appleid.apple.com/" target="_blank" rel="noopener noreferrer">Apple ID Account Management</a>.
2. Under **Sign-In and Security**, select **App-Specific Passwords**.
3. Generate a password for this migration tool.
4. Copy the **19-character code** (formatted in 4-character blocks separated by hyphens, e.g. `abcd-efgh-ijkl-mnop`).

---

## ⚙️ Usage

### 1. Set Environment Variables
Set your source and target credentials securely in your Linux terminal before running the script:

```bash
# Source Account (Apple iCloud - 19 chars with hyphens)
export SRC_USER="your-apple-id@icloud.com"
export SRC_PASS="abcd-efgh-ijkl-mnop"

# Target Account (Google Workspace / Gmail - 16 digits without spaces)
export TGT_USER="your-email@gmail.com"
export TGT_PASS="abcd1234efgh5678"
```

### 2. Run the All-in-One Migration Pipeline
Execute the main script to start the transfer, cleanup, and timestamp restoration:

```bash
python3 icloud_to_gmail_migrator.py
```

---

## ⏱️ Execution Time & Performance Considerations

Please be aware that IMAP operations on large historical email archives are **time-intensive**:

- **Estimated Speed:** Expect roughly **1 to 3 hours per Gigabyte** (or per ~10,000 emails), depending on your account size and server limits.
- **Why does it take so long?** Major providers (like Google and Apple) enforce strict **IMAP Rate Limits (Throttling)** to prevent server overload. Every single folder and email header requires direct server-side verification.
- **Universal Issue:** Folder encoding issues with mUTF-7 affect **all non-ASCII languages** (e.g., Spanish accents, French, German umlauts, etc.) and apply to almost any cross-provider IMAP migration.
- **Recommendation:** Let the script run uninterrupted in a background terminal session. If it drops, re-run it—thanks to resume-logic, it picks up right where it stopped.

---

## 💡 Troubleshooting & AI Assistance

If you encounter unexpected errors, missing modules, or server timeouts:
- Paste the error message and the respective script into an AI assistant.
- These scripts are written in a clean, modular format so they can be easily debugged and adapted.

---

## 📜 License
Licensed under the <a href="LICENSE" target="_blank" rel="noopener noreferrer">MIT License</a>. Free to use, adapt, and share.