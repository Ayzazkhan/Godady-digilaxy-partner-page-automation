#!/usr/bin/env python3
import os, json, io
from ftplib import FTP
from bs4 import BeautifulSoup

# Updated path for your domain list file
DOMAINS_FILE = "duplication/urls.json"

def backup_file(ftp, remote_file):
    """Rename current index.html -> rollback.html (fixed name)"""
    try:
        ftp.rename(remote_file, "rollback.html")
        print("[OK] Renamed old index.html to rollback.html")
    except Exception as e:
        print(f"[INFO] No existing index.html found or rename failed: {e}")

def fetch_html(ftp, remote_file="rollback.html"):
    """Fetch rollback.html or index.html if rollback doesn't exist"""
    bio = io.BytesIO()
    try:
        ftp.retrbinary(f"RETR rollback.html", bio.write)
        print("[OK] Downloaded rollback.html for modification")
    except:
        try:
            ftp.retrbinary(f"RETR index.html", bio.write)
            print("[OK] Downloaded index.html for modification")
        except Exception as e:
            print(f"[WARN] No base file found: {e}")
            bio.write("<html><body><section id='clients'><div class='row align-center justify-content-center'></div></section></body></html>".encode())

    bio.seek(0)
    return bio.read().decode("utf-8", errors="ignore")

def detect_and_remove_duplicates(html):
    """Remove duplicate partner blocks intelligently based on link href"""
    soup = BeautifulSoup(html, "html.parser")
    seen_links = set()
    removed = 0

    for wrapper in soup.find_all("div", class_="client-wrapper"):
        a_tag = wrapper.find("a", href=True)
        if a_tag:
            href = a_tag["href"].strip()
            if href in seen_links:
                parent_block = wrapper.find_parent("div", class_=lambda c: c and "col-" in c)
                (parent_block or wrapper).decompose()
                removed += 1
            else:
                seen_links.add(href)

    print(f"[INFO] Removed {removed} duplicate blocks")
    return str(soup)

def process_domain(domain, host, ftp_user, ftp_pass):
    print(f"🔹 Processing {domain} ({host})")

    ftp = FTP(host, timeout=15)
    ftp.login(ftp_user, ftp_pass)
    ftp.cwd("partners")

    # Step 1: Backup index.html -> rollback.html
    backup_file(ftp, "index.html")

    # Step 2: Fetch latest HTML (rollback or index)
    html = fetch_html(ftp)

    # Step 3: Clean duplicates
    updated_html = detect_and_remove_duplicates(html)

    # Step 4: Upload updated HTML
    updated_bytes = io.BytesIO(updated_html.encode("utf-8"))
    ftp.storbinary("STOR index.html", updated_bytes)
    print(f"[✅] Uploaded cleaned index.html for {domain}")

    ftp.quit()

def main():
    with open(DOMAINS_FILE, "r", encoding="utf-8") as f:
        domains = json.load(f)

    for domain, data in domains.items():
        host = data["host"]
        ftp_user = f"cicd@{domain}"
        ftp_pass = os.environ.get(f"FTP_PASS_{domain.replace('.', '_').upper()}")

        if not ftp_pass:
            print(f"[❌] Missing FTP_PASS for {domain}")
            continue

        process_domain(domain, host, ftp_user, ftp_pass)

if __name__ == "__main__":
    main()
