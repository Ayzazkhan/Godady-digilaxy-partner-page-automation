#!/usr/bin/env python3
import os, json, io
from ftplib import FTP
from bs4 import BeautifulSoup

DOMAINS_FILE = "partners-1-init/data/domains.json"
TEMPLATE_FILE = "partners-1-init/templates/index_template.html"

def process_domain(domain, host, ftp_user, ftp_pass):
    print(f"\n🔹 Processing {domain}")

    ftp = FTP(host, timeout=20)
    ftp.login(ftp_user, ftp_pass)
    print("✅ FTP login successful (already in partners-1)")

    html = ""

    # 1️⃣ Try reading index.html
    try:
        bio = io.BytesIO()
        ftp.retrbinary("RETR index.html", bio.write)
        html = bio.getvalue().decode("utf-8", "ignore")
        print("📄 index.html found")
    except:
        print("🆕 index.html not found, creating new one")
        tpl = open(TEMPLATE_FILE, "r").read()
        html = tpl.replace("{{DOMAIN}}", domain)

    soup = BeautifulSoup(html, "html.parser")

    # 2️⃣ Remove existing canonical if any
    for tag in soup.find_all("link", rel="canonical"):
        tag.decompose()

    # 3️⃣ Insert correct canonical
    canonical_url = f"https://www.{domain}/partners-1/"
    new_canonical = soup.new_tag(
        "link",
        rel="canonical",
        href=canonical_url
    )
    soup.head.append(new_canonical)

    # 4️⃣ Upload back
    out = io.BytesIO(str(soup).encode("utf-8"))
    ftp.storbinary("STOR index.html", out)

    print(f"✅ Canonical updated → {canonical_url}")
    ftp.quit()

def main():
    domain = os.environ.get("CURRENT_DOMAIN")
    ftp_user = os.environ.get("FTP_USER")
    ftp_pass = os.environ.get("FTP_PASS")

    domains = json.load(open(DOMAINS_FILE))
    host = domains[domain]["host"]

    process_domain(domain, host, ftp_user, ftp_pass)

if __name__ == "__main__":
    main()
