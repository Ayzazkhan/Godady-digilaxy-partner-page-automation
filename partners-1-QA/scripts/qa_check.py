#!/usr/bin/env python3
import os, json
import requests
from ftplib import FTP
from bs4 import BeautifulSoup

DOMAINS_FILE = "partners-1-QA/data/domains.json"

def check_ftp_connection(domain, host, ftp_user, ftp_pass):
    """Test FTP connection and check if index.html exists"""
    try:
        print(f"\n{'='*60}")
        print(f"🔹 QA Check: {domain}")
        print(f"🌐 Host: {host}")
        print(f"{'='*60}")
        
        # FTP Connection Test
        ftp = FTP(host, timeout=30)
        ftp.login(ftp_user, ftp_pass)
        print("✅ FTP login successful")
        
        # Check current directory
        current_dir = ftp.pwd()
        print(f"📂 Current directory: {current_dir}")
        
        # Check if index.html exists
        files = []
        ftp.retrlines('LIST', files.append)
        
        index_exists = any('index.html' in f for f in files)
        
        if index_exists:
            print("✅ index.html found")
        else:
            print("❌ index.html NOT found")
            ftp.quit()
            return False
        
        # Check if partners-logo folder exists
        logo_exists = any('partners-logo' in f for f in files)
        
        if logo_exists:
            print("✅ partners-logo folder found")
        else:
            print("⚠️ partners-logo folder NOT found")
        
        ftp.quit()
        return True
        
    except Exception as e:
        print(f"❌ FTP Error: {type(e).__name__}: {str(e)}")
        return False

def check_http_access(domain):
    """Test HTTP access and check page structure"""
    try:
        url = f"https://{domain}/partners-1/index.html"
        print(f"\n🌐 Testing HTTP: {url}")
        
        response = requests.get(url, timeout=10, verify=False)
        
        if response.status_code == 200:
            print(f"✅ HTTP Status: {response.status_code}")
            
            # Parse HTML
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Check for canonical tag
            canonical = soup.find("link", rel="canonical")
            if canonical:
                print(f"✅ Canonical tag found: {canonical.get('href')}")
            else:
                print("⚠️ Canonical tag NOT found")
            
            # Check for row container
            row = soup.find("div", class_="row align-center justify-content-center")
            if row:
                print("✅ Row container found")
                
                # Count partner blocks
                blocks = row.find_all("div", class_="client-wrapper")
                print(f"📊 Partner blocks found: {len(blocks)}")
            else:
                print("❌ Row container NOT found")
            
            # Check for custom section
            section = soup.find("section", id="clients2-2p")
            if section:
                print("✅ Custom section found")
            else:
                print("⚠️ Custom section NOT found")
            
            # Check for custom CSS
            style_tags = soup.find_all("style")
            has_custom_css = any('.cid-qKT6knwV2G' in str(tag) for tag in style_tags)
            
            if has_custom_css:
                print("✅ Custom CSS found")
            else:
                print("⚠️ Custom CSS NOT found")
            
            return True
        else:
            print(f"❌ HTTP Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ HTTP Error: {type(e).__name__}: {str(e)}")
        return False

def run_qa(domain, host, ftp_user, ftp_pass):
    """Run complete QA checks"""
    try:
        print(f"\n{'#'*70}")
        print(f"  QA REPORT: {domain}")
        print(f"{'#'*70}")
        
        ftp_ok = check_ftp_connection(domain, host, ftp_user, ftp_pass)
        http_ok = check_http_access(domain)
        
        print(f"\n{'='*60}")
        if ftp_ok and http_ok:
            print(f"🎉 QA PASSED: {domain}")
            print(f"{'='*60}")
            return True
        else:
            print(f"❌ QA FAILED: {domain}")
            print(f"{'='*60}")
            return False
            
    except Exception as e:
        print(f"❌ QA ERROR: {domain}")
        print(f"   {type(e).__name__}: {str(e)}")
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
    
    success = run_qa(current_domain, host, ftp_user, ftp_pass)
    
    if not success:
        exit(1)

if __name__ == "__main__":
    main()
