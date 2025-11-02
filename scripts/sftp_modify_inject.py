#!/usr/bin/env python3
import os, json
from datetime import datetime
from ftplib import FTP, error_perm
from bs4 import BeautifulSoup
import requests
import io

# --- File locations ---
DOMAINS_FILE = "data/domains.json"
TEMPLATE_FILE = "templates/partner_block_template.html"

def inject_into_html(original_html, snippet_html):
    """Injects partner block before section closing."""
    soup = BeautifulSoup(original_html, "html.parser")

    # Try to find partner row
    row = soup.find("div", class_="row align-center justify-content-center")

    fragment = BeautifulSoup(snippet_html, "html.parser")

    if row:
        row.append(fragment)
    else:
        # If structure not found, just append inside <body>
        if soup.body:
            soup.body.append(fragment)
        else:
            soup.append(fragment)

    return str(soup)


def handle(domain, host, ftp_user, ftp_pass):
    print(f"[INFO] Connecting to {domain} @ {host} via FTP...")
    ftp = FTP(host, timeout=20)
    ftp.login(ftp_user, ftp_pass)
    print("[OK] FTP login successful")

    remote_file = "index.html"  # since user opens inside /partners/
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    backup_name = f"index_old_{ts}.html"

    # --- Backup existing file ---
    try:
        ftp.rename(remote_file, backup_name)
        print(f"[OK] Remote backup created: {backup_name}")
    except error_perm:
        print("[INFO] No existing index.html found, will create a new one")

    # --- Try to download a base HTML ---
    base_html = ""
    bio = io.BytesIO()

    try:
        ftp.retrbinary(f"RETR {backup_name}", bio.write)
        print("[OK] Downloaded backup for modification")
    except Exception:
        try:
            bio = io.BytesIO()
            ftp.retrbinary(f"RETR {remote_file}", bio.write)
            print("[OK] Downloaded current index.html")
        except Exception:
            print("[WARN] No index.html found — creating new scaffold")
            base_html = "<html><body><section id='clients'><div class='row align-center justify-content-center'></div></section></body></html>"

    if not base_html:
        bio.seek(0)
        base_html = bio.read().decode("utf-8", errors="ignore")

    # --- Read HTML template ---
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        snippet = f.read()

    # --- Replace content placeholder if content exists ---
    content_file = "data/contents.json"
    if os.path.exists(content_file):
        with open(content_file, "r", encoding="utf-8") as cf:
            contents = json.load(cf)
        if domain in contents and len(contents[domain]) > 0:
            # pick the next or first line
            text = contents[domain][0]
            snippet = snippet.replace("{{content}}", text)
            print(f"[OK] Injecting content: {text}")
        else:
            snippet = snippet.replace("{{content}}", "LawEssayHelp Default Text")
    else:
        snippet = snippet.replace("{{content}}", "LawEssayHelp Default Text")

    # --- Inject block and upload ---
    updated_html = inject_into_html(base_html, snippet)
    updated_bytes = io.BytesIO(updated_html.encode("utf-8"))
    ftp.storbinary(f"STOR {remote_file}", updated_bytes)
    print(f"[OK] Uploaded new {remote_file} for {domain}")

    ftp.quit()

    # --- Optional HTTP validation ---
    try:
        url = f"https://{domain}/partners/index.html"
        r = requests.get(url, timeout=8)
        print(f"[CHECK] {url} -> {r.status_code}")
    except Exception as e:
        print(f"[WARN] HTTP validation failed: {e}")


def main():
    current = os.environ.get("CURRENT_DOMAIN")
    ftp_user = os.environ.get("FTP_USER")
    ftp_pass = os.environ.get("FTP_PASS")

    if not current or not ftp_user or not ftp_pass:
        print("❌ Missing environment vars: CURRENT_DOMAIN, FTP_USER, FTP_PASS")
        return

    with open(DOMAINS_FILE, "r", encoding="utf-8") as f:
        domains = json.load(f)

    if current not in domains:
        print(f"❌ {current} not defined in {DOMAINS_FILE}")
        return

    host = domains[current]["host"]
    handle(current, host, ftp_user, ftp_pass)


if __name__ == "__main__":
    main()
