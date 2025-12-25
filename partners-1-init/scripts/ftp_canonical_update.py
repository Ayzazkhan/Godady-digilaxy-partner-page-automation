#!/usr/bin/env python3
import io, os
from ftplib import FTP
from bs4 import BeautifulSoup

TEMPLATE_FILE = "partners-1-init/templates/partners1_index_template.html"

def generate_base_html():
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        return f.read()

def update_canonical(html, domain):
    soup = BeautifulSoup(html, "html.parser")
    head = soup.find("head")
    if not head:
        print("⚠️ No <head> tag found")
        return html
    
    existing = head.find("link", rel="canonical")
    if existing:
        print(f"ℹ️ Canonical already exists: {existing.get('href')}")
        return str(soup)
    
    canonical_url = f"https://www.{domain}/partners-1/"
    new_tag = soup.new_tag("link", rel="canonical", href=canonical_url)
    head.append(new_tag)
    print(f"✅ Canonical added: {canonical_url}")
    return str(soup)

def main():
    domain = os.environ.get("CURRENT_DOMAIN")
    host = os.environ.get("FTP_HOST")
    ftp_user = os.environ.get("FTP_USER")
    ftp_pass = os.environ.get("FTP_PASS")
    
    if not domain or not host or not ftp_user or not ftp_pass:
        print("❌ Missing environment variables:")
        print(f"   CURRENT_DOMAIN: {domain}")
        print(f"   FTP_HOST: {host}")
        print(f"   FTP_USER: {ftp_user}")
        print(f"   FTP_PASS: {'***' if ftp_pass else 'None'}")
        exit(1)
    
    try:
        print(f"\n🔹 Processing: {domain}")
        print(f"🌐 Host: {host}")
        print(f"👤 User: {ftp_user}")
        
        ftp = FTP(host, timeout=30)
        ftp.login(ftp_user, ftp_pass)
        print("✅ FTP login successful")
        
        # Navigate to partners-1 directory if needed
        try:
            ftp.cwd("partners-1")
            print("✅ Changed to /partners-1 directory")
        except:
            print("⚠️ /partners-1 directory not found, using root")
        
        remote_file = "index.html"
        bio = io.BytesIO()
        
        try:
            ftp.retrbinary(f"RETR {remote_file}", bio.write)
            html = bio.getvalue().decode("utf-8", errors="ignore")
            print(f"✅ Loaded existing index.html ({len(html)} bytes)")
        except:
            print("⚠️ index.html not found — creating new from template")
            html = generate_base_html()
        
        updated_html = update_canonical(html, domain)
        
        ftp.storbinary(
            f"STOR {remote_file}",
            io.BytesIO(updated_html.encode("utf-8"))
        )
        print(f"✅ Uploaded index.html ({len(updated_html)} bytes)")
        
        ftp.quit()
        print(f"🎉 COMPLETED: {domain}")
        
    except Exception as e:
        print(f"❌ ERROR: {domain}")
        print(f"   {type(e).__name__}: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
