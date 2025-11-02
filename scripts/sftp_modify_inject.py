#!/usr/bin/env python3
import os, json, io
from datetime import datetime
from ftplib import FTP, error_perm
from bs4 import BeautifulSoup
import requests

DOMAINS_FILE = "data/domains.json"
CONTENTS_FILE = "data/contents.json"
TEMPLATE_FILE = "templates/partner_block_template.html"

def inject_into_html(original_html, snippet_html):
    soup = BeautifulSoup(original_html, "html.parser")
    row = soup.find("div", class_="row align-center justify-content-center")
    fragment = BeautifulSoup(snippet_html, "html.parser")
    if row:
        row.append(fragment)
    elif soup.body:
        soup.body.append(fragment)
    else:
        soup.append(fragment)
    return str(soup)

def handle(domain, host, ftp_user, ftp_pass, content):
    print(f"\n🔹 Processing {domain} @ {host}")
    ftp = FTP(host, timeout=20)
    ftp.login(ftp_user, ftp_pass)
    print("[OK] FTP login successful")

    remote_file = "index.html"
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    backup_name = f"index_old_{ts}.html"

    try:
        ftp.rename(remote_file, backup_name)
        print(f"[OK] Backup created: {backup_name}")
    except error_perm:
        print("[INFO] No existing index.html to backup; will create new one")

    # download base
    bio = io.BytesIO()
    base_html = ""
    try:
        ftp.retrbinary(f"RETR {backup_name}", bio.write)
        print("[OK] Downloaded backup for modification")
    except Exception:
        try:
            bio = io.BytesIO()
            ftp.retrbinary(f"RETR {remote_file}", bio.write)
            print("[OK] Downloaded current index.html")
        except Exception:
            print("[WARN] No index.html found — creating scaffold")
            base_html = "<html><body><section id='clients'><div class='row align-center justify-content-center'></div></section></body></html>"

    if not base_html:
        bio.seek(0)
        base_html = bio.read().decode("utf-8", errors="ignore")

    # template
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        snippet = f.read()

    # replace placeholder with content chosen by Jenkins (content passed as arg)
    snippet = snippet.replace("{{content}}", content)
    print(f"[OK] Using content: {content}")

    # inject & upload
    updated_html = inject_into_html(base_html, snippet)
    updated_bytes = io.BytesIO(updated_html.encode("utf-8"))
    ftp.storbinary(f"STOR {remote_file}", updated_bytes)
    print(f"[OK] Uploaded new {remote_file} for {domain}")

    ftp.quit()

    # optional check
    try:
        url = f"https://{domain}/partners/index.html"
        r = requests.get(url, timeout=8)
        print(f"[CHECK] {url} -> {r.status_code}")
    except Exception as e:
        print(f"[WARN] HTTP validation failed: {e}")

def main():
    # Jenkins will set CURRENT_DOMAIN, FTP_USER, FTP_PASS
    current = os.environ.get("CURRENT_DOMAIN")
    ftp_user = os.environ.get("FTP_USER")
    ftp_pass = os.environ.get("FTP_PASS")
    if not current or not ftp_user or not ftp_pass:
        print("❌ Env vars CURRENT_DOMAIN, FTP_USER, FTP_PASS required")
        return

    # load domains (ordered)
    with open(DOMAINS_FILE, "r", encoding="utf-8") as f:
        domains_obj = json.load(f)
    domains = list(domains_obj.keys())  # preserves order in modern Python

    if current not in domains:
        print(f"❌ {current} not found in {DOMAINS_FILE}")
        return

    # load contents (expects a list/array)
    with open(CONTENTS_FILE, "r", encoding="utf-8") as f:
        contents_list = json.load(f)
        if not isinstance(contents_list, list) or len(contents_list) == 0:
            print("❌ contents.json must be a non-empty JSON array")
            return

    # find index of current domain and pick content by index (cycle if needed)
    idx = domains.index(current)
    content = contents_list[idx % len(contents_list)]

    # host from domains.json
    host = domains_obj[current].get("host")
    if not host:
        print(f"❌ Host not defined for {current} in {DOMAINS_FILE}")
        return

    handle(current, host, ftp_user, ftp_pass, content)

if __name__ == "__main__":
    main()
