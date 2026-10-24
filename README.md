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

- **Cross-Platform Compatibility:** Runs natively on **Linux, macOS, and Windows (10/11)** without any third-party dependencies—uses standard Python libraries only.
- **All-in-One Pipeline (`icloud_to_gmail_migrator.py`):** Handles synchronization, mUTF-7 duplicate purging, and historical timestamp fixing in a single, streamlined execution flow.
- **Resumable & Fault-Tolerant:** Interrupted by an IMAP timeout or network drop? Simply re-run the script or set `RESUME_FROM_FOLDER`. It automatically detects existing messages via `Message-ID` checking and resumes exactly where it left off.
- **mUTF-7 Folder Encoding Fix:** Apple Mail uses specialized mUTF-7 encoding for non-ASCII characters and umlauts (`ä`, `ö`, `ü`, `ß`). Standard IMAP tools often create duplicated, corrupted folder trees, which are automatically cleaned up.
- **Historical Timestamp Preservation:** Parses the original internal `Date:` header from email MIME bodies and passes strict RFC3501 `INTERNALDATE` strings during `APPEND`, ensuring correct chronological ordering in Gmail.
- **Security First (No Hardcoded Credentials):** Credentials are passed strictly via system environment variables (`os.getenv`) — no hardcoded passwords in the source code.

---

## 🔑 Prerequisites & Authentication

For security reasons, modern email providers do not allow standard account passwords for automated script access. You need **App-Specific Passwords**.

### Target Account (e.g., Google Workspace / Gmail)
1. Go to your [Google Account Settings](https://myaccount.google.com/security) (**Security** -> **2-Step Verification** must be enabled).
2. Direct link to generate: [Google App Passwords](https://myaccount.google.com/apppasswords).
3. Create a new app password (named e.g. "IMAP Migration").
4. Copy the **16-digit code** (without spaces/hyphens, e.g. `abcd1234efgh5678`).

### Source Account (e.g., Apple iCloud)
1. Go to your [Apple ID Account Management](https://appleid.apple.com/).
2. Under **Sign-In and Security**, select **App-Specific Passwords**.
3. Generate a password for this migration tool.
4. Copy the **19-character code** (formatted in 4-character blocks separated by hyphens, e.g. `abcd-efgh-ijkl-mnop`).

---

## ⚙️ Usage

Set your environment variables before running the script. Choose the commands matching your operating system:

### Option A: Linux / macOS (Terminal)

```bash
# Set credentials (Source & Target)
export SRC_USER="your-apple-id@icloud.com"
export SRC_PASS="abcd-efgh-ijkl-mnop"
export TGT_USER="your-email@gmail.com"
export TGT_PASS="abcd1234efgh5678"

# Run the pipeline
python3 icloud_to_gmail_migrator.py
```

### Option B: Windows CMD (Command Prompt)

```cmd
:: Set credentials (Source & Target)
set SRC_USER=your-apple-id@icloud.com
set SRC_PASS=abcd-efgh-ijkl-mnop
set TGT_USER=your-email@gmail.com
set TGT_PASS=abcd1234efgh5678

:: Run the pipeline
python icloud_to_gmail_migrator.py
```

### Option C: Windows PowerShell

```powershell
# Set credentials (Source & Target)
$env:SRC_USER="your-apple-id@icloud.com"
$env:SRC_PASS="abcd-efgh-ijkl-mnop"
$env:TGT_USER="your-email@gmail.com"
$env:TGT_PASS="abcd1234efgh5678"

# Run the pipeline
python icloud_to_gmail_migrator.py
```

---

## 🛠️ Post-Migration Timestamp Recovery (Edge Cases)

### Real-World Experience & Server Timeouts
Even though timestamp preservation is built directly into `icloud_to_gmail_migrator.py`, real-world testing shows that server-side glitches can still happen. If an IMAP session drops unexpectedly, or if you resume a migration after an interruption using `RESUME_FROM_FOLDER`, Gmail's IMAP servers may occasionally ignore the requested timestamp for specific folders and assign the current upload date instead.

If you notice that certain folders or old emails ended up in Gmail with today's date:
- You **do not need to re-run the entire migration from scratch**.
- Use our dedicated recovery tool: [Gmail-IMAP-Timestamp-Fixer](https://github.com/Agent47-Scripts/Gmail-IMAP-Timestamp-Fixer).
- It scans your target Gmail account, reads the true `Date:` header from affected emails, and updates their timestamps directly in Gmail.

---

## ⏱️ Performance Considerations & Hardware Impact

Execution time varies significantly based on network rate-limiting and—crucially—the underlying **hardware and Linux kernel configuration**.

### Practical Benchmarks

In real-world tests across different hardware configurations under Linux, transfer rates fluctuated widely:

- **Slower Hardware / Suboptimal Driver Stack (e.g., Older Linux desktop setups/iMacs):**
  ~250 emails / ~200 MB per hour.
- **Modern Portable Hardware (e.g., MacBook Pro under Linux):**
  ~2,000 emails / ~1.0 GB per hour.

---

## 📜 License
Licensed under the [MIT License](LICENSE). Free to use, adapt, and share.
