#!/usr/bin/env python3
import io, os
from ftplib import FTP
from bs4 import BeautifulSoup

# ✅ Hardcoded template - no file needed
def generate_base_html():
    return """<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Partners-1</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"/>
<meta name="robots" content="index, follow"/>
<style>
.client-wrapper {
  text-align: center;
  padding: 10px;
  border: 1px solid #f1ecec;
  height: 400px;
}
</style>
</head>
<body>
<section class="container pt-5">
  <h1 class="text-center">Partners-1</h1>
</section>
</body>
</html>"""

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
        print("❌ Missing environment variables")
        exit(1)
    
    try:
        print(f"\n🔹 Processing: {domain}")
        print(f"🌐 Host: {host}")
        print(f"👤 User: {ftp_user}")
        
        ftp = FTP(host, timeout=30)
        ftp.login(ftp_user, ftp_pass)
        print("✅ FTP login successful")
        
        # ✅ Login hote hi partners-1 mein hain, no directory change needed
        print("✅ Already in /partners-1 directory")
        
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
