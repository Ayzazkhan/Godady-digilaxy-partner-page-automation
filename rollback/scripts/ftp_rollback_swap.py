#!/usr/bin/env python3
import os, json
from ftplib import FTP, error_perm

# ✅ CORRECT PATH
DOMAINS_FILE = "rollback/data/domains.json"

def swap_files(domain, host, ftp_user, ftp_pass):
    print(f"\n🔄 Rolling Back: {domain} @ {host}")

    ftp = FTP(host, timeout=20)
    ftp.login(ftp_user, ftp_pass)
    print("✅ FTP Login Success")

    try:
        # ✅ Safe 3-step swap
        ftp.rename("rollback.html", "rollback_tmp.html")
        print("✅ rollback.html -> rollback_tmp.html")

        ftp.rename("index.html", "rollback.html")
        print("✅ index.html -> rollback.html")

        ftp.rename("rollback_tmp.html", "index.html")
        print("✅ rollback_tmp.html -> index.html")

        print(f"✅ Rollback SUCCESS for {domain}")

    except error_perm as e:
        print(f"❌ Rollback FAILED for {domain}: {e}")

    ftp.quit()


def main():
    current = os.environ.get("CURRENT_DOMAIN")
    ftp_user = os.environ.get("FTP_USER")
    ftp_pass = os.environ.get("FTP_PASS")

    if not current or not ftp_user or not ftp_pass:
        print("❌ Missing env vars CURRENT_DOMAIN / FTP_USER / FTP_PASS")
        return

    with open(DOMAINS_FILE, "r", encoding="utf-8") as f:
        domains_obj = json.load(f)

    if current not in domains_obj:
        print(f"❌ {current} not found in rollback/domains.json")
        return

    host = domains_obj[current].get("host")
    if not host:
        print(f"❌ Host missing for {current}")
        return

    swap_files(current, host, ftp_user, ftp_pass)


if __name__ == "__main__":
    main()
