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
        return html
    
    existing = head.find("link", rel="canonical")
    if existing:
        print("ℹ️ Canonical already exists — skipping")
        return str(soup)
    
    canonical_url = f"https://www.{domain}/partners-1/"
    new_tag = soup.new_tag("link", rel="canonical", href=canonical_url)
    head.append(new_tag)
    print(f"✅ Canonical added: {canonical_url}")
    return str(soup)

def main():
    domain = os.environ.get("CURRENT_DOMAIN")
    host = os.environ.get("FTP_HOST")  # ✅ YE ADD KIYA
    ftp_user = os.environ.get("FTP_USER")
    ftp_pass = os.environ.get("FTP_PASS")
    
    if not domain or not host or not ftp_user or not ftp_pass:
        print("❌ Missing environment variables")
        exit(1)
    
    try:
        print(f"\n🔹 Processing {domain}")
        print(f"🌐 Connecting to {host}")
        
        ftp = FTP(host, timeout=20)
        ftp.login(ftp_user, ftp_pass)
        print("✅ FTP login success")
        
        remote_file = "index.html"
        bio = io.BytesIO()
        
        try:
            ftp.retrbinary(f"RETR {remote_file}", bio.write)
            html = bio.getvalue().decode("utf-8", errors="ignore")
            print("✅ index.html loaded")
        except:
            print("⚠️ index.html not found — creating new")
            html = generate_base_html()
        
        updated_html = update_canonical(html, domain)
        
        ftp.storbinary(
            f"STOR {remote_file}",
            io.BytesIO(updated_html.encode("utf-8"))
        )
        ftp.quit()
        print(f"🎉 DONE: {domain}")
        
    except Exception as e:
        print(f"❌ FAILED: {domain} | {e}")
        exit(1)

if __name__ == "__main__":
    main()
