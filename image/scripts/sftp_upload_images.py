#!/usr/bin/env python3
import os, json
from ftplib import FTP
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]  # 2 folders up from image/scripts/
DOMAINS_FILE = BASE_DIR / "data/domains.json"
LOCAL_IMAGES_FOLDER = BASE_DIR / "image/partners-logo"
REMOTE_FOLDER = "partners-logo"

def upload_images(domain, host, ftp_user, ftp_pass):
    """Upload images to FTP server"""
    try:
        print(f"\n{'='*60}")
        print(f"🔹 Processing: {domain}")
        print(f"🌐 Host: {host}")
        print(f"👤 User: {ftp_user}")
        print(f"{'='*60}")
        
        ftp = FTP(host, timeout=30)
        ftp.login(ftp_user, ftp_pass)
        print("✅ FTP login successful")
        
        # Verify current directory
        current_dir = ftp.pwd()
        print(f"📂 Current directory: {current_dir}")
        
        # Ensure remote folder exists
        try:
            ftp.mkd(REMOTE_FOLDER)
            print(f"✅ Created remote folder: {REMOTE_FOLDER}")
        except Exception:
            print(f"ℹ️ Remote folder {REMOTE_FOLDER} already exists")
        
        ftp.cwd(REMOTE_FOLDER)
        print(f"📂 Changed to: {REMOTE_FOLDER}")
        
        # Upload all images
        local_images = list(Path(LOCAL_IMAGES_FOLDER).glob("*.*"))
        
        if not local_images:
            print(f"⚠️ No images found in {LOCAL_IMAGES_FOLDER}")
            ftp.quit()
            return False
        
        print(f"📊 Found {len(local_images)} images to upload")
        
        uploaded_count = 0
        for img_path in local_images:
            try:
                with open(img_path, "rb") as f:
                    ftp.storbinary(f"STOR {img_path.name}", f)
                    uploaded_count += 1
                    print(f"✅ [{uploaded_count}/{len(local_images)}] Uploaded: {img_path.name}")
            except Exception as e:
                print(f"❌ Failed to upload {img_path.name}: {e}")
        
        ftp.quit()
        print(f"🎉 COMPLETED: {domain} ({uploaded_count}/{len(local_images)} images)")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {domain}")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

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
    
    # Load domains.json to get host
    with open(DOMAINS_FILE, "r", encoding="utf-8") as f:
        domains_obj = json.load(f)
    
    if current not in domains_obj:
        print(f"❌ {current} not found in {DOMAINS_FILE}")
        exit(1)
    
    host = domains_obj[current].get("host")
    if not host:
        print(f"❌ Host not defined for {current}")
        exit(1)
    
    success = upload_images(current, host, ftp_user, ftp_pass)
    
    if not success:
        exit(1)

if __name__ == "__main__":
    main()
