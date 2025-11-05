#!/usr/bin/env python3
import ftplib
import json
import socket
import traceback

DOMAINS_FILE = "data/domains.json"

def check_ftp(domain, host):
    try:
        ftp = ftplib.FTP(host, timeout=8)
        ftp.quit()
        return True, "Connection successful"
    except socket.gaierror:
        return False, "Invalid hostname or DNS resolution failed"
    except ftplib.error_perm as e:
        return False, f"Permission error: {e}"
    except ftplib.error_temp as e:
        return False, f"Temporary FTP error: {e}"
    except ftplib.all_errors as e:
        return False, f"FTP error: {e}"
    except Exception as e:
        return False, f"Unknown error: {e}"

def main():
    with open(DOMAINS_FILE, "r", encoding="utf-8") as f:
        domains_data = json.load(f)

    accessible = []
    failed = {}

    print("🔍 Starting FTP connectivity check...\n")

    for domain, info in domains_data.items():
        host = info.get("host", domain)
        print(f"➡️ Checking FTP for: {domain} ({host})")

        ok, msg = check_ftp(domain, host)
        if ok:
            print(f"✅ Success: {msg}\n")
            accessible.append(domain)
        else:
            print(f"❌ Failed: {msg}\n")
            failed[domain] = msg

    # Print summary
    print("\n==================== SUMMARY ====================")
    print(f"✅ Accessible Domains: {len(accessible)}")
    for d in accessible:
        print(f"   - {d}")

    print(f"\n❌ Inaccessible Domains: {len(failed)}")
    for d, reason in failed.items():
        print(f"   - {d} → {reason}")

    # Save to report.txt (optional)
    with open("check/report.txt", "w") as r:
        r.write("✅ Accessible Domains:\n")
        for d in accessible:
            r.write(f"{d}\n")
        r.write("\n❌ Inaccessible Domains:\n")
        for d, reason in failed.items():
            r.write(f"{d} → {reason}\n")

    print("\n📄 Report generated at: check/report.txt")

if __name__ == "__main__":
    main()
