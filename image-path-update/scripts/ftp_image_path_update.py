#!/usr/bin/env python3
import io, os
from ftplib import FTP

OLD_PATH = '../partners-logo/'
NEW_PATH = '../partners/partners-logo/'

def main():
    domain   = os.environ.get("CURRENT_DOMAIN")
    host     = os.environ.get("FTP_HOST")
    ftp_user = os.environ.get("FTP_USER")
    ftp_pass = os.environ.get("FTP_PASS")

    if not all([domain, host, ftp_user, ftp_pass]):
        print("❌ Missing environment variables")
        exit(1)

    try:
        print(f"\n🔹 Processing: {domain}")
        print(f"🌐 Host: {host}")
        print(f"👤 User: {ftp_user}")

        ftp = FTP(host, timeout=30)
        ftp.login(ftp_user, ftp_pass)
        print("✅ FTP login successful")

        remote_file = "index.html"
        backup_file = "rollback.html"
        bio = io.BytesIO()

        # Download index.html
        try:
            ftp.retrbinary(f"RETR {remote_file}", bio.write)
            html = bio.getvalue().decode("utf-8", errors="ignore")
            print(f"✅ Downloaded index.html ({len(html)} bytes)")
        except:
            print("❌ index.html not found on server!")
            ftp.quit()
            exit(1)

        # Skip if old path doesn't exist
        if OLD_PATH not in html:
            print(f"ℹ️ Skipping — '{OLD_PATH}' not found in HTML")
            ftp.quit()
            return

        # Create backup
        try:
            ftp.storbinary(f"STOR {backup_file}", io.BytesIO(html.encode("utf-8")))
            print(f"✅ Backup created: {backup_file}")
        except Exception as e:
            print(f"⚠️ Backup failed: {e}")

        # Replace old path with new path
        count = html.count(OLD_PATH)
        updated_html = html.replace(OLD_PATH, NEW_PATH)
        print(f"✅ Replaced {count} occurrence(s)")
        print(f"   OLD: {OLD_PATH}")
        print(f"   NEW: {NEW_PATH}")

        # Upload updated file
        ftp.storbinary(f"STOR {remote_file}", io.BytesIO(updated_html.encode("utf-8")))
        print(f"✅ Uploaded index.html ({len(updated_html)} bytes)")

        ftp.quit()
        print(f"🎉 COMPLETED: {domain}")

    except Exception as e:
        print(f"❌ ERROR: {domain} — {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()
