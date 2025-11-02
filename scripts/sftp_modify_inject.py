#!/usr/bin/env python3
import os, json, time
from datetime import datetime
from bs4 import BeautifulSoup
import paramiko
import requests

DOMAINS_FILE = "data/domains.json"
TEMPLATE_FILE = "templates/partner_block_template.html"

def inject_into_html(original_html, snippet_html):
    soup = BeautifulSoup(original_html, "html.parser")
    row = soup.find("div", class_="row align-center justify-content-center")
    fragment = BeautifulSoup(snippet_html, "html.parser")
    if row:
        row.append(fragment)
    else:
        soup.body.append(fragment)
    return str(soup)

def handle(domain, host, ftp_user, ftp_pass):
    print(f"[INFO] Processing {domain} @ {host}")
    transport = paramiko.Transport((host, 22))
    transport.connect(username=ftp_user, password=ftp_pass)
    sftp = paramiko.SFTPClient.from_transport(transport)

    remote_file = "index.html"   # because FTP user opens into partners/
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    backup_name = f"index_old_{ts}.html"

    # try backup (rename if exists)
    try:
        sftp.stat(remote_file)
        sftp.rename(remote_file, backup_name)
        print(f"[OK] Remote backup created: {backup_name}")
    except IOError:
        print("[INFO] Remote index.html not found — will create new")

    # try download backup or create scaffold
    local_tmp = f"/tmp/{domain}_base.html"
    try:
        # if backup exists get it, else try remote (if rename failed)
        sftp.get(backup_name, local_tmp)
    except Exception:
        try:
            sftp.get(remote_file, local_tmp)
        except Exception:
            # create minimal scaffold
            with open(local_tmp, "w", encoding="utf-8") as f:
                f.write("<html><body><section id='clients'><div class='row align-center justify-content-center'></div></section></body></html>")
            print("[INFO] Created local scaffold")

    with open(local_tmp, "r", encoding="utf-8") as f:
        base_html = f.read()
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        snippet = f.read()

    updated_html = inject_into_html(base_html, snippet)

    new_local = f"/tmp/{domain}_new.html"
    with open(new_local, "w", encoding="utf-8") as f:
        f.write(updated_html)

    # upload new file
    sftp.put(new_local, remote_file)
    print(f"[OK] Uploaded new index.html for {domain}")

    # optional HTTP check
    try:
        url = f"https://{domain}/partners/index.html"
        r = requests.get(url, timeout=8)
        print(f"[CHECK] {url} -> {r.status_code}")
    except Exception as e:
        print(f"[WARN] HTTP validation failed: {e}")

    sftp.close()
    transport.close()

def main():
    current = os.environ.get("CURRENT_DOMAIN")
    ftp_user = os.environ.get("FTP_USER")
    ftp_pass = os.environ.get("FTP_PASS")
    if not current or not ftp_user or not ftp_pass:
        print("Env vars CURRENT_DOMAIN, FTP_USER, FTP_PASS required")
        return

    with open(DOMAINS_FILE, "r", encoding="utf-8") as f:
        domains = json.load(f)

    if current not in domains:
        print(f"{current} not defined in {DOMAINS_FILE}")
        return

    host = domains[current]["host"]
    handle(current, host, ftp_user, ftp_pass)

if __name__ == "__main__":
    main()
