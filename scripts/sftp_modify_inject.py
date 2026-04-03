#!/usr/bin/env python3
import os, json, io
from ftplib import FTP
from bs4 import BeautifulSoup

DOMAINS_FILE  = "data/domains.json"
CONTENTS_FILE = "data/contents.json"
TEMPLATE_FILE = "templates/partner_block_template.html"

REMOTE_FILE = "index.html"
BACKUP_FILE = "rollback.html"

def inject_into_html(original_html, snippet_html):
    soup     = BeautifulSoup(original_html, "html.parser")
    row      = soup.find("div", class_="row align-center justify-content-center")
    fragment = BeautifulSoup(snippet_html, "html.parser")

    if row:
        row.append(fragment)
        print("[OK] Injected into row container")
    elif soup.body:
        soup.body.append(fragment)
        print("[WARN] No row container — appended to body")
    else:
        print("[ERROR] No valid injection point")
        return original_html

    return str(soup)

def handle(domain, host, ftp_user, ftp_pass, content):
    print(f"\n{'='*55}")
    print(f"🔹 Domain : {domain}")
    print(f"🌐 Host   : {host}")
    print(f"👤 User   : {ftp_user}")
    print(f"📁 Target : /{REMOTE_FILE}")
    print(f"{'='*55}")

    ftp = FTP(host, timeout=20)
    ftp.login(ftp_user, ftp_pass)
    print("[OK] FTP connected")
    print(f"[OK] Current dir: {ftp.pwd()}")

    # Download index.html directly from root
    bio = io.BytesIO()
    try:
        ftp.retrbinary(f"RETR {REMOTE_FILE}", bio.write)
        bio.seek(0)
        base_html = bio.read().decode("utf-8", errors="ignore")
        print(f"[OK] Downloaded {REMOTE_FILE} ({len(base_html)} bytes)")
    except Exception:
        print(f"[ERROR] {REMOTE_FILE} not found")
        ftp.quit()
        return False

    # Backup
    try:
        ftp.storbinary(f"STOR {BACKUP_FILE}", io.BytesIO(base_html.encode("utf-8")))
        print(f"[OK] Backup saved as {BACKUP_FILE}")
    except Exception as e:
        print(f"[WARN] Backup failed: {e}")

    # Load template and inject content
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        snippet = f.read().replace("{{content}}", content)

    updated_html = inject_into_html(base_html, snippet)

    if updated_html == base_html:
        print("[ERROR] HTML unchanged — injection failed")
        ftp.quit()
        return False

    # Upload
    ftp.storbinary(f"STOR {REMOTE_FILE}", io.BytesIO(updated_html.encode("utf-8")))
    print(f"[OK] Uploaded {REMOTE_FILE} ({len(updated_html)} bytes)")

    ftp.quit()
    print(f"[DONE] {domain}")
    return True

def main():
    domain   = os.environ.get("CURRENT_DOMAIN")
    ftp_user = os.environ.get("FTP_USER")
    ftp_pass = os.environ.get("FTP_PASS")

    if not all([domain, ftp_user, ftp_pass]):
        print("❌ Missing: CURRENT_DOMAIN, FTP_USER, FTP_PASS")
        exit(1)

    with open(DOMAINS_FILE, "r", encoding="utf-8") as f:
        domains_obj = json.load(f)
    domains = list(domains_obj.keys())

    if domain not in domains:
        print(f"❌ '{domain}' not found in domains.json")
        exit(1)

    with open(CONTENTS_FILE, "r", encoding="utf-8") as f:
        contents_list = json.load(f)

    if not isinstance(contents_list, list) or not contents_list:
        print("❌ contents.json must be a non-empty array")
        exit(1)

    idx     = domains.index(domain)
    content = contents_list[idx % len(contents_list)]
    host    = domains_obj[domain].get("host")

    if not host:
        print(f"❌ No host defined for {domain}")
        exit(1)

    print(f"📝 Content index : {idx % len(contents_list)}")
    print(f"📄 Preview       : {content[:80]}...")

    success = handle(domain, host, ftp_user, ftp_pass, content)
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
