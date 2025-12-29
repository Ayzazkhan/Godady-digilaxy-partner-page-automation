#!/usr/bin/env python3
import os, json
from ftplib import FTP

DOMAINS_FILE = "partners-1-QA/data/domains.json"

def test_ftp_login(domain, host, ftp_user, ftp_pass):
    """Test FTP login only"""
    try:
        print(f"🔹 Testing: {domain}")
        print(f"   Host: {host}")
        print(f"   User: {ftp_user}")
        
        ftp = FTP(host, timeout=30)
        ftp.login(ftp_user, ftp_pass)
        
        current_dir = ftp.pwd()
        print(f"   ✅ Login successful - Directory: {current_dir}")
        
        ftp.quit()
        return True
        
    except Exception as e:
        print(f"   ❌ Login failed - {type(e).__name__}: {str(e)}")
        return False

def main():
    current_domain = os.environ.get("CURRENT_DOMAIN")
    ftp_user = os.environ.get("FTP_USER")
    ftp_pass = os.environ.get("FTP_PASS")
    
    if not current_domain or not ftp_user or not ftp_pass:
        print("❌ Missing environment variables")
        exit(1)
    
    # Load domains
    with open(DOMAINS_FILE, "r", encoding="utf-8") as f:
        domains_obj = json.load(f)
    
    if current_domain not in domains_obj:
        print(f"❌ {current_domain} not found in domains.json")
        exit(1)
    
    host = domains_obj[current_domain].get("host")
    if not host:
        print(f"❌ Host not defined for {current_domain}")
        exit(1)
    
    success = test_ftp_login(current_domain, host, ftp_user, ftp_pass)
    
    if not success:
        exit(1)

if __name__ == "__main__":
    main()
