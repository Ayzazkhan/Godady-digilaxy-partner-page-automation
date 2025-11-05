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
    """Remove duplicate partner blocks intelligently based on domain (ignore protocol, www, and path)"""
    soup = BeautifulSoup(html, "html.parser")
    seen_domains = set()
    removed = 0

    wrappers = soup.find_all("div", class_="client-wrapper")
    print(f"[DEBUG] Found {len(wrappers)} partner wrappers")

    for wrapper in wrappers:
        a_tag = wrapper.find("a", href=True)
        if a_tag:
            href = a_tag["href"].strip()

            # Normalize and parse the domain
            parsed = urlparse(href)
            domain = parsed.netloc.lower().replace("www.", "")

            # If URL doesn't have scheme (e.g., starts with // or relative path)
            if not domain and href:
                # try extracting domain manually
                if "//" in href:
                    domain = href.split("//")[-1].split("/")[0].replace("www.", "")
                else:
                    domain = href.split("/")[0].replace("www.", "")

            # Skip empty domains
            if not domain:
                continue

            print(f"[DEBUG] Found domain: {domain}")

            if domain in seen_domains:
                parent_block = wrapper.find_parent("div", class_=lambda c: c and "col-" in c)
                (parent_block or wrapper).decompose()
                removed += 1
            else:
                seen_domains.add(domain)

    print(f"[INFO] Removed {removed} duplicate partner blocks (by domain, ignoring protocol)")
    return str(soup)


def process_domain(domain, host, ftp_user, ftp_pass):
    print(f"🔹 Processing {domain} ({host})")

    ftp = FTP(host, timeout=15)
    ftp.login(ftp_user, ftp_pass)

    # ⚠️ No need to change directory — FTP already opens in /partners

    # Step 1: Backup existing index.html
    backup_file(ftp, "index.html")

    # Step 2: Fetch rollback.html (or index if rollback missing)
    html = fetch_html(ftp)

    # Step 3: Remove duplicates
    updated_html = detect_and_remove_duplicates(html)

    # Step 4: Upload updated file
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
        ftp_pass = os.environ.get("FTP_PASS")


        if not ftp_pass:
            print(f"[❌] Missing FTP_PASS for {domain}")
            continue

        process_domain(domain, host, ftp_user, ftp_pass)

if __name__ == "__main__":
    main()
