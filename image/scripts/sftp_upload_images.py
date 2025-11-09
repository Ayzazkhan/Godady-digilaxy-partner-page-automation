#!/usr/bin/env python3
import os, json
from ftplib import FTP
from pathlib import Path

DOMAINS_FILE = "../../data/domains.json"
LOCAL_IMAGES_FOLDER = "partners-logo"  # corrected folder name
REMOTE_FOLDER = "partners-logo"        # remote folder to upload images

def upload_images(domain, host, ftp_user, ftp_pass):
    print(f"\n🔹 Processing {domain} @ {host}")
    ftp = FTP(host, timeout=20)
    ftp.login(ftp_user, ftp_pass)
    print("[OK] FTP login successful")

    # Ensure remote folder exists
    try:
        ftp.mkd(REMOTE_FOLDER)
        print(f"[INFO] Created remote folder: {REMOTE_FOLDER}")
    except Exception:
        print(f"[INFO] Remote folder {REMOTE_FOLDER} exists")

    ftp.cwd(REMOTE_FOLDER)

    # upload all images
    local_images = Path(LOCAL_IMAGES_FOLDER).glob("*.*")
    for img_path in local_images:
        with open(img_path, "rb") as f:
            ftp.storbinary(f"STOR {img_path.name}", f)
            print(f"[OK] Uploaded: {img_path.name}")

    ftp.quit()
    print(f"[OK] All images uploaded for {domain}")

def main():
    current = os.environ.get("CURRENT_DOMAIN")
    ftp_user = os.environ.get("FTP_USER")
    ftp_pass = os.environ.get("FTP_PASS")
    if not current or not ftp_user or not ftp_pass:
        print("❌ Env vars CURRENT_DOMAIN, FTP_USER, FTP_PASS required")
        return

    # load domains.json to get host
    with open(DOMAINS_FILE, "r", encoding="utf-8") as f:
        domains_obj = json.load(f)

    if current not in domains_obj:
        print(f"❌ {current} not found in {DOMAINS_FILE}")
        return

    host = domains_obj[current].get("host")
    if not host:
        print(f"❌ Host not defined for {current}")
        return

    upload_images(current, host, ftp_user, ftp_pass)

if __name__ == "__main__":
    main()
