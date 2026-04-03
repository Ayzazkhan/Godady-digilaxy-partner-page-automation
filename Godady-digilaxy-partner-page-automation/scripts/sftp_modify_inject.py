#!/usr/bin/env python3
"""
Script: sftp_modify_inject.py
Purpose: Connect to target domain server via FTP, compare alldomains.json with
         domains.json, and remove matching domain cards from partners/index.html
         and partners-1/index.html after creating rollback backups.
"""

import os
import json
import io
from ftplib import FTP
from bs4 import BeautifulSoup

# ── Paths ──────────────────────────────────────────────────────────────────────
DOMAINS_FILE      = "data/domains.json"
ALLDOMAINS_REMOTE = "data/alldomains.json"
PARTNER_FOLDERS   = ["partners", "partners-1"]

# ── Report collector ───────────────────────────────────────────────────────────
report = {
    "target_domains"  : [],
    "server_domains"  : [],
    "matched_domains" : [],
    "not_on_server"   : [],
    "results"         : {}
}


def ftp_read_file(ftp, remote_path):
    buf = io.BytesIO()
    ftp.retrbinary(f"RETR {remote_path}", buf.write)
    buf.seek(0)
    return buf.read().decode("utf-8", errors="ignore")


def ftp_write_file(ftp, remote_path, content_str):
    data = io.BytesIO(content_str.encode("utf-8"))
    ftp.storbinary(f"STOR {remote_path}", data)


def remove_cards_for_domains(html_content, target_domains):
    """
    Remove partner card divs whose anchor href contains any of the target domains.
    Returns (updated_html, removed_count, removed_card_details).
    """
    soup         = BeautifulSoup(html_content, "html.parser")
    removed      = 0
    card_details = []

    cards = soup.find_all("div", class_=lambda c: c and
                          "p-3" in c and "col-12" in c and "col-lg-3" in c)

    for card in cards:
        anchors = card.find_all("a", href=True)
        for a in anchors:
            href = a["href"].strip().lower()
            for domain in target_domains:
                if domain.lower() in href:
                    card_details.append(f"{domain} → {a['href'].strip()}")
                    card.decompose()
                    removed += 1
                    break
            else:
                continue
            break

    return str(soup), removed, card_details


def process_partner_folder(ftp, domain, folder_name, target_domains):
    """Process one partner folder. Returns result dict for reporting."""
    index_path    = f"{domain}/{folder_name}/index.html"
    rollback_path = f"{domain}/{folder_name}/rollback.html"

    result = {
        "status"        : "FAILED",
        "backup"        : "NOT CREATED",
        "cards_removed" : 0,
        "card_details"  : [],
        "error"         : None
    }

    print(f"\n      📂 [{folder_name}/index.html]")

    # 1. Download index.html
    try:
        html = ftp_read_file(ftp, index_path)
        print(f"         ✅ Downloaded ({len(html)} bytes)")
    except Exception as e:
        result["error"]  = f"Download failed: {e}"
        result["status"] = "FAILED"
        print(f"         ❌ Download failed: {e}")
        return result

    # 2. Backup
    try:
        ftp_write_file(ftp, rollback_path, html)
        result["backup"] = "CREATED"
        print(f"         ✅ Backup (rollback.html) created")
    except Exception as e:
        result["backup"] = f"FAILED: {e}"
        print(f"         ⚠️  Backup failed: {e}")

    # 3. Remove cards
    updated_html, removed_count, card_details = remove_cards_for_domains(html, target_domains)
    result["cards_removed"] = removed_count
    result["card_details"]  = card_details

    if removed_count == 0:
        print(f"         ℹ️  No matching cards found — skipping upload")
        result["status"] = "NO_CARDS_MATCHED"
        return result

    print(f"         🗑️  {removed_count} card(s) removed:")
    for cd in card_details:
        print(f"              • {cd}")

    # 4. Upload updated file
    try:
        ftp_write_file(ftp, index_path, updated_html)
        print(f"         ✅ Uploaded updated index.html ({len(updated_html)} bytes)")
        result["status"] = "SUCCESS"
    except Exception as e:
        result["error"]  = f"Upload failed: {e}"
        result["status"] = "UPLOAD_FAILED"
        print(f"         ❌ Upload failed: {e}")

    return result


def print_full_report():
    """Print complete summary report."""
    sep  = "=" * 65
    sep2 = "-" * 65

    print(f"\n\n{sep}")
    print(f"{'FULL PIPELINE REPORT':^65}")
    print(f"{sep}\n")

    # ── 1. Domain Overview ────────────────────────────────────────────────────
    print(f"[1] TARGET DOMAINS  (domains.json)  ──  Total: {len(report['target_domains'])}")
    for d in report["target_domains"]:
        print(f"      • {d}")

    print(f"\n[2] SERVER DOMAINS  (alldomains.json) ── Total: {len(report['server_domains'])}")
    for d in report["server_domains"]:
        print(f"      • {d}")

    print(f"\n[3] MATCHED  (will be / were processed) ── {len(report['matched_domains'])}")
    for d in report["matched_domains"]:
        print(f"      ✔  {d}")

    print(f"\n[4] NOT ON SERVER  (skipped) ── {len(report['not_on_server'])}")
    if report["not_on_server"]:
        for d in report["not_on_server"]:
            print(f"      ✖  {d}")
    else:
        print(f"      (none)")

    # ── 2. Per-domain results ─────────────────────────────────────────────────
    print(f"\n{sep}")
    print(f"{'DOMAIN-WISE PROCESSING DETAILS':^65}")
    print(f"{sep}")

    overall_success = 0
    overall_failed  = 0
    total_cards_removed = 0

    for domain, folders in report["results"].items():
        statuses = [v["status"] for v in folders.values()]
        domain_ok = all(s in ("SUCCESS", "NO_CARDS_MATCHED") for s in statuses)

        icon = "✅" if domain_ok else "❌"
        print(f"\n  {icon} DOMAIN : {domain}")
        print(f"  {sep2}")

        for folder, res in folders.items():
            s = res["status"]
            if s == "SUCCESS":
                status_icon = "✅ SUCCESS"
            elif s == "NO_CARDS_MATCHED":
                status_icon = "ℹ️  NO CARDS MATCHED"
            else:
                status_icon = f"❌ {s}"

            backup_icon = "✅ CREATED" if res["backup"] == "CREATED" else f"⚠️  {res['backup']}"

            print(f"\n    📁  {folder}/index.html")
            print(f"        Status         : {status_icon}")
            print(f"        Backup         : {backup_icon}")
            print(f"        Cards Removed  : {res['cards_removed']}")
            total_cards_removed += res["cards_removed"]

            if res["card_details"]:
                print(f"        Removed Cards  :")
                for cd in res["card_details"]:
                    print(f"                         • {cd}")
            if res["error"]:
                print(f"        Error          : {res['error']}")

        if domain_ok:
            overall_success += 1
        else:
            overall_failed += 1

    # ── 3. Final totals ───────────────────────────────────────────────────────
    print(f"\n{sep}")
    print(f"{'FINAL SUMMARY':^65}")
    print(f"{sep}")
    print(f"  Target Domains          : {len(report['target_domains'])}")
    print(f"  Found on Server         : {len(report['matched_domains'])}")
    print(f"  Not Found on Server     : {len(report['not_on_server'])}")
    print(f"  Domains Processed OK    : {overall_success}")
    print(f"  Domains Failed          : {overall_failed}")
    print(f"  Total Cards Removed     : {total_cards_removed}")
    print(f"{sep}\n")

    return overall_failed == 0


def main():
    # ── Env vars ───────────────────────────────────────────────────────────────
    ftp_host = os.environ.get("FTP_HOST")
    ftp_user = os.environ.get("FTP_USER")
    ftp_pass = os.environ.get("FTP_PASS")

    if not ftp_host or not ftp_user or not ftp_pass:
        print("❌ Missing environment variables:")
        print(f"   FTP_HOST : {ftp_host}")
        print(f"   FTP_USER : {ftp_user}")
        print(f"   FTP_PASS : {'***' if ftp_pass else 'None'}")
        exit(1)

    # ── Load domains.json ─────────────────────────────────────────────────────
    with open(DOMAINS_FILE, "r", encoding="utf-8") as f:
        target_domains = json.load(f)

    if not isinstance(target_domains, list) or len(target_domains) == 0:
        print(f"❌ {DOMAINS_FILE} must be a non-empty JSON array")
        exit(1)

    report["target_domains"] = target_domains

    print("=" * 65)
    print(f"{'DIGILAXY PARTNER CARD REMOVAL PIPELINE':^65}")
    print("=" * 65)
    print(f"\n📋 Target domains loaded: {len(target_domains)}")
    for d in target_domains:
        print(f"   • {d}")

    # ── FTP Connect ───────────────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"🔌 Connecting to FTP")
    print(f"   Host : {ftp_host}")
    print(f"   User : {ftp_user}")
    print(f"{'='*65}")

    try:
        ftp = FTP(ftp_host, timeout=30)
        ftp.login(ftp_user, ftp_pass)
        print(f"✅ FTP login successful")
        print(f"📂 Root directory : {ftp.pwd()}")
    except Exception as e:
        print(f"❌ FTP connection failed: {e}")
        exit(1)

    # ── Read alldomains.json ──────────────────────────────────────────────────
    print(f"\n📥 Reading server domain list: {ALLDOMAINS_REMOTE}")
    try:
        raw         = ftp_read_file(ftp, ALLDOMAINS_REMOTE)
        all_domains = json.loads(raw)
        report["server_domains"] = all_domains
        print(f"✅ alldomains.json read — {len(all_domains)} domains on server")
    except Exception as e:
        print(f"❌ Could not read alldomains.json: {e}")
        ftp.quit()
        exit(1)

    # ── Compare ───────────────────────────────────────────────────────────────
    matched       = [d for d in target_domains if d in all_domains]
    not_on_server = [d for d in target_domains if d not in all_domains]

    report["matched_domains"] = matched
    report["not_on_server"]   = not_on_server

    print(f"\n🔍 Comparison result:")
    print(f"   Matched      : {len(matched)}")
    print(f"   Not on server: {len(not_on_server)}")

    if not_on_server:
        print(f"\n⚠️  These domains are NOT on this server (will be skipped):")
        for d in not_on_server:
            print(f"   ✖  {d}")

    if not matched:
        print("\nℹ️  No matching domains found — nothing to process.")
        ftp.quit()
        print_full_report()
        exit(0)

    print(f"\n✔  Domains to process:")
    for d in matched:
        print(f"   → {d}")

    # ── Process each matched domain ───────────────────────────────────────────
    for domain in matched:
        print(f"\n{'='*65}")
        print(f"  PROCESSING : {domain}")
        print(f"{'='*65}")
        report["results"][domain] = {}

        for folder in PARTNER_FOLDERS:
            res = process_partner_folder(ftp, domain, folder, target_domains)
            report["results"][domain][folder] = res

    ftp.quit()
    print(f"\n✅ FTP connection closed")

    # ── Print Full Report ─────────────────────────────────────────────────────
    all_ok = print_full_report()

    exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
