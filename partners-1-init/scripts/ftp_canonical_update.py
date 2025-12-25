#!/usr/bin/env python3
import json, io, os
from ftplib import FTP
from bs4 import BeautifulSoup

DOMAINS_FILE = "partners-1-init/data/domains.json"
TEMPLATE_FILE = "partners-1-init/templates/partners1_index_template.html"

SUCCESS = []
FAILED = []

def generate_base_html():
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        return f.read()

def update_canonical(html, domain):
    soup = BeautifulSoup(html, "html.parser")
    head = soup.find("head")

    if not head:
        return html

    # check existing canonical
    existing = head.find("link", rel="canonical")
    if existing:
        print("ℹ️ Canonical already exists — skipping")
        return str(soup)

    canonical_url = f"https://www.{domain}/partners-1/"
    new_tag = soup.new_tag("link", rel="canonical", href=canonical_url)
    head.append(new_tag)
    print(f"✅ Canonical added: {canonical_url}")

    return str(soup)

def handle_domain(domain, host, ftp_user, ftp_pass):
    try:
        print(f"\n🔹 Processing {domain}")

        ftp = FTP(host, timeout=20)
        ftp.login(ftp_user, ftp_pass)
        print("✅ FTP login success")

        remote_file = "index.html"
        bio = io.BytesIO()

        try:
            ftp.retrbinary(f"RETR {remote_file}", bio.write)
            html = bio.getvalue().decode("utf-8", errors="ignore")
            print("✅ index.html loaded")
        except:
            print("⚠️ index.html not found — creating new")
            html = generate_base_html()

        updated_html = update_canonical(html, domain)

        ftp.storbinary(
            f"STOR {remote_file}",
            io.BytesIO(updated_html.encode("utf-8"))
        )

        ftp.quit()
        SUCCESS.append(domain)
        print(f"🎉 DONE: {domain}")

    except Exception as e:
        FAILED.append({"domain": domain, "error": str(e)})
        print(f"❌ FAILED: {domain} | {e}")

def main():
    ftp_user = os.environ.get("FTP_USER")
    ftp_pass = os.environ.get("FTP_PASS")

    if not ftp_user or not ftp_pass:
        print("❌ FTP credentials missing")
        return

    with open(DOMAINS_FILE, "r") as f:
        domains = json.load(f)

    for domain, data in domains.items():
        handle_domain(domain, data["host"], ftp_user, ftp_pass)

    print("\n========== FINAL SUMMARY ==========")
    print(f"✅ SUCCESS ({len(SUCCESS)})")
    for d in SUCCESS:
        print(f"  ✔ {d}")

    print(f"\n❌ FAILED ({len(FAILED)})")
    for f in FAILED:
        print(f"  ✖ {f['domain']} | {f['error']}")

    print("=================================")

if __name__ == "__main__":
    main()
