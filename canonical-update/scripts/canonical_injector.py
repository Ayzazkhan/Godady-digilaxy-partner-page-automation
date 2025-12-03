#!/usr/bin/env python3
import os, json, io
from ftplib import FTP, error_perm
from bs4 import BeautifulSoup

DOMAINS_FILE = "data/domains.json"
CANONICAL_TEMPLATE = '<link rel="canonical" href="https://{domain}/partners/" />'

def normalize_domain(d):
    return d.replace("_", ".")

def inject_canonical(html, domain):
    soup = BeautifulSoup(html, "html.parser")
    head = soup.find("head")

    if not head:
        html = "<html><head></head>" + html + "</html>"
        soup = BeautifulSoup(html, "html.parser")
        head = soup.find("head")

    # Already has canonical?
    if head.find("link", rel="canonical"):
        print("   ✔ Canonical already exists → SKIPPED")
        return str(soup)

    # Inject new tag
    canonical_tag = BeautifulSoup(
        CANONICAL_TEMPLATE.format(domain=domain),
        "html.parser"
    )
    head.append(canonical_tag)
    print("   ✔ Canonical tag inserted")

    return str(soup)

def process(domain_key, host, ftp_user, ftp_pass):
    domain = normalize_domain(domain_key)

    print(f"\n🔵 Processing: {domain}")

    ftp = FTP(host, timeout=25)
    ftp.login(ftp_user, ftp_pass)
    print("   ✔ FTP Login OK")

    remote = "index.html"
    backup = "rollback.html"

    # Backup old index.html
    try:
        ftp.rename(remote, backup)
        print(f"   ✔ Backup saved → {backup}")
    except error_perm:
        print("   ℹ No existing index.html found")

    # Download HTML
    content = ""
    for f in [backup, remote]:
        try:
            buff = io.BytesIO()
            ftp.retrbinary(f"RETR {f}", buff.write)
            buff.seek(0)
            content = buff.read().decode("utf-8", errors="ignore")
            print(f"   ✔ Downloaded: {f}")
            break
        except:
            pass

    if not content:
        print("   ⚠ No HTML found, creating new file")
        content = "<html><head></head><body></body></html>"

    updated = inject_canonical(content, domain)

    buff = io.BytesIO(updated.encode("utf-8"))
    ftp.storbinary(f"STOR {remote}", buff)
    print("   ✔ Uploaded updated index.html")
    ftp.quit()

def main():
    current = os.environ.get("CURRENT_DOMAIN")
    ftp_user = os.environ.get("FTP_USER")
    ftp_pass = os.environ.get("FTP_PASS")

    if not current or not ftp_user or not ftp_pass:
        print("❌ Missing CURRENT_DOMAIN / FTP_USER / FTP_PASS")
        return

    with open(DOMAINS_FILE) as f:
        domains = json.load(f)

    if current not in domains:
        print(f"❌ {current} not found in domains.json")
        return

    host = domains[current].get("host")
    process(current, host, ftp_user, ftp_pass)

if __name__ == "__main__":
    main()
