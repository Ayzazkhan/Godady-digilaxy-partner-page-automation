#!/usr/bin/env python3
import os, io
from ftplib import FTP
from datetime import datetime
from bs4 import BeautifulSoup

domain = os.environ.get("CURRENT_DOMAIN")
ftp_user = os.environ.get("FTP_USER")
ftp_pass = os.environ.get("FTP_PASS")

if not domain or not ftp_user or not ftp_pass:
    print("❌ Missing env vars")
    exit(1)

print(f"\n🔹 Processing {domain}")

ftp = FTP(domain, timeout=30)
ftp.login(ftp_user, ftp_pass)
print("[OK] FTP login successful")

bio = io.BytesIO()
ftp.retrbinary("RETR index.html", bio.write)
html = bio.getvalue().decode("utf-8", errors="ignore")

# Create rollback backup
timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
rollback_name = f"rollback_{timestamp}.html"
ftp.storbinary(f"STOR rollback/{rollback_name}", io.BytesIO(html.encode("utf-8")))
print(f"[OK] Backup created: rollback/{rollback_name}")

soup = BeautifulSoup(html, "html.parser")
wrappers = soup.find_all("div", class_="client-wrapper")

seen = set()
removed = 0
for w in wrappers:
    link = w.find("a")
    href = link.get("href") if link else None
    if href:
        if href in seen:
            w.decompose()
            removed += 1
        else:
            seen.add(href)

if removed == 0:
    print("[INFO] No duplicates found.")
else:
    print(f"[OK] Removed {removed} duplicate blocks.")

ftp.storbinary("STOR index.html", io.BytesIO(str(soup).encode("utf-8")))
ftp.quit()
print("✅ Cleanup complete and uploaded successfully.")

