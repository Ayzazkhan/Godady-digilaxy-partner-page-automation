#!/usr/bin/env python3
import os
import json
import io
from ftplib import FTP
from bs4 import BeautifulSoup
from urllib.parse import urlparse

DOMAINS_FILE = "duplication/urls.json"
TARGET_FILE = "duplication/targeturl.json"

def backup_file(ftp, remote_file="index.html"):
    try:
        ftp.rename(remote_file, "rollback.html")
        print("[OK] Renamed old index.html to rollback.html")
    except Exception as e:
        print(f"[INFO] No existing index.html found or rename failed: {e}")

def fetch_html(ftp):
    bio = io.BytesIO()
    try:
        ftp.retrbinary("RETR rollback.html", bio.write)
        print("[OK] Downloaded rollback.html for modification")
    except:
        try:
            ftp.retrbinary("RETR index.html", bio.write)
            print("[OK] Downloaded index.html for modification")
        except Exception as e:
            print(f"[WARN] No base file found: {e}")
            bio.write("<html><body><section id='clients'><div class='row align-center justify-content-center'></div></section></body></html>".encode())
    bio.seek(0)
    return bio.read().decode("utf-8", errors="ignore")

def remove_target_duplicates_keep_last(html, target_domains):
    """Remove duplicates of target domains but keep last occurrence"""
    soup = BeautifulSoup(html, "html.parser")
    seen_domains = {}
    removed = 0

    wrappers = soup.find_all("div", class_="client-wrapper")
    print(f"[DEBUG] Found {len(wrappers)} partner wrappers")

    # Reverse loop: last occurrence will be kept
    for wrapper in reversed(wrappers):
        a_tag = wrapper.find("a", href=True)
        if a_tag:
            href = a_tag["href"].strip()
            parsed = urlparse(href)
            domain = parsed.netloc.lower().replace("www.", "")

            # Handle links without scheme
            if not domain and href:
                if "//" in href:
                    domain = href.split("//")[-1].split("/")[0].replace("www.", "")
                else:
                    domain = href.split("/")[0].replace("www.", "")

            if domain in target_domains:
                if domain in seen_domains:
                    parent_block = wrapper.find_parent("div", class_=lambda c: c and "col-" in c)
                    (parent_block or wrapper).decompose()
                    removed += 1
                else:
                    seen_domains[domain] = True

    print(f"[INFO] Removed {removed} duplicate partner blocks (kept last one)")
    return str(soup)

def process_domain(domain, host, ftp_user, ftp_pass, target_domains):
    print(f"\n🔹 Processing {domain} ({host})")
    try:
        ftp = FTP(host, timeout=15)
        ftp.login(ftp_user, ftp_pass)
    except Exception as e:
        print(f"[❌] FTP connection failed for {domain}: {e}")
        return

    backup_file(ftp)
    html = fetch_html(ftp)
    updated_html = remove_target_duplicates_keep_last(html, target_domains)

    try:
        updated_bytes = io.BytesIO(updated_html.encode("utf-8"))
        ftp.storbinary("STOR index.html", updated_bytes)
        print(f"[✅] Uploaded cleaned index.html for {domain}")
    except Exception as e:
        print(f"[❌] Failed to upload updated index.html for {domain}: {e}")

    ftp.quit()

def main():
    # Load FTP info
    try:
        with open(DOMAINS_FILE, "r", encoding="utf-8") as f:
            all_domains = json.load(f)
    except Exception as e:
        print(f"[❌] Failed to load {DOMAINS_FILE}: {e}")
        return

    # Load target domains
    try:
        with open(TARGET_FILE, "r", encoding="utf-8") as f:
            target_domains = [d.lower().replace("www.", "") for d in json.load(f)]
    except Exception as e:
        print(f"[❌] Failed to load {TARGET_FILE}: {e}")
        return

    ftp_pass = os.environ.get("FTP_PASS")
    if not ftp_pass:
        print("[❌] Missing FTP_PASS environment variable!")
        return

    for domain, data in all_domains.items():
        host = data.get("host")
        if not host:
            print(f"[❌] Missing host for {domain}, skipping...")
            continue

        ftp_user = f"cicd@{domain}"
        process_domain(domain, host, ftp_user, ftp_pass, target_domains)

if __name__ == "__main__":
    main()
