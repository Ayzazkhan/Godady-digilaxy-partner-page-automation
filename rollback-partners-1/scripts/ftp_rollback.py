#!/usr/bin/env python3
import os, json
from ftplib import FTP, error_perm

# ✅ CORRECT PATH
DOMAINS_FILE = "rollback-partners-1/data/domains.json"

def swap_files(domain, host, ftp_user, ftp_pass):
    print(f"\n🔄 Rolling Back: {domain} @ {host}")
    
    try:
        ftp = FTP(host, timeout=20)
        ftp.login(ftp_user, ftp_pass)
        print("✅ FTP Login Success")
        
        # List files for debug
        print(f"📂 Current dir: {ftp.pwd()}")
        
        try:
            files = ftp.nlst()
            print(f"📄 Files on server: {files}")
        except:
            pass
        
        try:
            # ✅ Safe 3-step swap
            ftp.rename("rollback.html", "rollback_tmp.html")
            print("✅ rollback.html -> rollback_tmp.html")

            ftp.rename("index.html", "rollback.html")
            print("✅ index.html -> rollback.html")

            ftp.rename("rollback_tmp.html", "index.html")
            print("✅ rollback_tmp.html -> index.html")

            print(f"🎉 Rollback SUCCESS for {domain}")
            return True

        except error_perm as e:
            print(f"❌ Rollback FAILED for {domain}: {e}")
            return False

    except Exception as e:
        print(f"❌ FTP Connection FAILED for {domain}: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        try:
            ftp.quit()
        except:
            pass

def main():
    current = os.environ.get("CURRENT_DOMAIN")
    ftp_user = os.environ.get("FTP_USER")
    ftp_pass = os.environ.get("FTP_PASS")

    if not current or not ftp_user or not ftp_pass:
        print("❌ Missing environment variables:")
        print(f"   CURRENT_DOMAIN: {current}")
        print(f"   FTP_USER: {ftp_user}")
        print(f"   FTP_PASS: {'***' if ftp_pass else 'None'}")
        exit(1)

    with open(DOMAINS_FILE, "r", encoding="utf-8") as f:
        domains_obj = json.load(f)

    if current not in domains_obj:
        print(f"❌ {current} not found in {DOMAINS_FILE}")
        exit(1)

    host = domains_obj[current].get("host")
    if not host:
        print(f"❌ Host missing for {current}")
        exit(1)

    success = swap_files(current, host, ftp_user, ftp_pass)

    if not success:
        exit(1)

if __name__ == "__main__":
    main()
