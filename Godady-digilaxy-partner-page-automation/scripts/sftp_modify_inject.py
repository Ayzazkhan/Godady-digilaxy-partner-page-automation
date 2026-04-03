#!/usr/bin/env python3
import os
import json
import io
from ftplib import FTP
from bs4 import BeautifulSoup

# ── Paths ──────────────────────────────────────────────────────────────────────
DOMAINS_FILE    = "data/domains.json"     # LOCAL - jin cards hatane hain
ALLDOMAINS_FILE = "data/alldomains.json"  # LOCAL - server pe jo domains hain
PARTNER_FOLDERS = ["partners", "partners-1"]

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
                    card_details.append(f"{domain} -> {a['href'].strip()}")
                    card.decompose()
                    removed += 1
                    break
            else:
                continue
            break

    return str(soup), removed, card_details


def process_partner_folder(ftp, domain, folder_name, target_domains):
    index_path    = f"{domain}/{folder_name}/index.html"
    rollback_path = f"{domain}/{folder_name}/rollback.html"

    result = {
        "status"        : "FAILED",
        "backup"        : "NOT CREATED",
        "cards_removed" : 0,
        "card_details"  : [],
        "error"         : None
    }

    print(f"\n      [{folder_name}/index.html]")

    # 1. Download
    try:
        html = ftp_read_file(ftp, index_path)
        print(f"         OK Downloaded ({len(html)} bytes)")
    except Exception as e:
        result["error"]  = f"Download failed: {e}"
        result["status"] = "FAILED"
        print(f"         FAILED Download: {e}")
        return result

    # 2. Backup
    try:
        ftp_write_file(ftp, rollback_path, html)
        result["backup"] = "CREATED"
        print(f"         OK Backup rollback.html created")
    except Exception as e:
        result["backup"] = f"FAILED: {e}"
        print(f"         WARNING Backup failed: {e}")

    # 3. Remove cards
    updated_html, removed_count, card_details = remove_cards_for_domains(html, target_domains)
    result["cards_removed"] = removed_count
    result["card_details"]  = card_details

    if removed_count == 0:
        print(f"         INFO No matching cards found - skipping upload")
        result["status"] = "NO_CARDS_MATCHED"
        return result

    print(f"         REMOVED {removed_count} card(s):")
    for cd in card_details:
        print(f"              * {cd}")

    # 4. Upload
    try:
        ftp_write_file(ftp, index_path, updated_html)
        print(f"         OK Uploaded updated index.html ({len(updated_html)} bytes)")
        result["status"] = "SUCCESS"
    except Exception as e:
        result["error"]  = f"Upload failed: {e}"
        result["status"] = "UPLOAD_FAILED"
        print(f"         FAILED Upload: {e}")

    return result


def print_full_report():
    sep  = "=" * 65
    sep2 = "-" * 65

    print(f"\n\n{sep}")
    print(f"{'FULL PIPELINE REPORT':^65}")
    print(f"{sep}\n")

    print(f"[1] TARGET DOMAINS (domains.json) -- Total: {len(report['target_domains'])}")
    for d in report["target_domains"]:
        print(f"      * {d}")

    print(f"\n[2] SERVER DOMAINS (alldomains.json) -- Total: {len(report['server_domains'])}")
    for d in report["server_domains"]:
        print(f"      * {d}")

    print(f"\n[3] MATCHED (processed) -- {len(report['matched_domains'])}")
    for d in report["matched_domains"]:
        print(f"      OK  {d}")

    print(f"\n[4] NOT ON SERVER (skipped) -- {len(report['not_on_server'])}")
    if report["not_on_server"]:
        for d in report["not_on_server"]:
            print(f"      SKIP  {d}")
    else:
        print(f"      (none)")

    print(f"\n{sep}")
    print(f"{'DOMAIN-WISE PROCESSING DETAILS':^65}")
    print(f"{sep}")

    overall_success     = 0
    overall_failed      = 0
    total_cards_removed = 0

    for domain, folders in report["results"].items():
        statuses  = [v["status"] for v in folders.values()]
        domain_ok = all(s in ("SUCCESS", "NO_CARDS_MATCHED") for s in statuses)

        icon = "SUCCESS" if domain_ok else "FAILED"
        print(f"\n  [{icon}] DOMAIN : {domain}")
        print(f"  {sep2}")

        for folder, res in folders.items():
            s = res["status"]
            if s == "SUCCESS":
                status_str = "SUCCESS"
            elif s == "NO_CARDS_MATCHED":
                status_str = "NO CARDS MATCHED"
            else:
                status_str = f"FAILED - {s}"

            backup_str = "CREATED" if res["backup"] == "CREATED" else f"FAILED: {res['backup']}"

            print(f"\n    {folder}/index.html")
            print(f"        Status        : {status_str}")
            print(f"        Backup        : {backup_str}")
            print(f"        Cards Removed : {res['cards_removed']}")
            total_cards_removed += res["cards_removed"]

            if res["card_details"]:
                print(f"        Removed Cards :")
                for cd in res["card_details"]:
                    print(f"                        * {cd}")
            if res["error"]:
                print(f"        Error         : {res['error']}")

        if domain_ok:
            overall_success += 1
        else:
            overall_failed += 1

    print(f"\n{sep}")
    print(f"{'FINAL SUMMARY':^65}")
    print(f"{sep}")
    print(f"  Target Domains       : {len(report['target_domains'])}")
    print(f"  Found on Server      : {len(report['matched_domains'])}")
    print(f"  Not on Server        : {len(report['not_on_server'])}")
    print(f"  Domains OK           : {overall_success}")
    print(f"  Domains Failed       : {overall_failed}")
    print(f"  Total Cards Removed  : {total_cards_removed}")
    print(f"{sep}\n")

    return overall_failed == 0


def main():
    ftp_host = os.environ.get("FTP_HOST")
    ftp_user = os.environ.get("FTP_USER")
    ftp_pass = os.environ.get("FTP_PASS")

    if not ftp_host or not ftp_user or not ftp_pass:
        print("FAILED Missing environment variables:")
        print(f"   FTP_HOST : {ftp_host}")
        print(f"   FTP_USER : {ftp_user}")
        print(f"   FTP_PASS : {'***' if ftp_pass else 'None'}")
        exit(1)

    # ── Load domains.json LOCAL ────────────────────────────────────────────────
    with open(DOMAINS_FILE, "r", encoding="utf-8") as f:
        target_domains = json.load(f)

    if not isinstance(target_domains, list) or len(target_domains) == 0:
        print(f"FAILED {DOMAINS_FILE} must be a non-empty JSON array")
        exit(1)

    report["target_domains"] = target_domains

    # ── Load alldomains.json LOCAL ─────────────────────────────────────────────
    with open(ALLDOMAINS_FILE, "r", encoding="utf-8") as f:
        all_domains = json.load(f)

    if not isinstance(all_domains, list) or len(all_domains) == 0:
        print(f"FAILED {ALLDOMAINS_FILE} must be a non-empty JSON array")
        exit(1)

    report["server_domains"] = all_domains

    print("=" * 65)
    print(f"{'DIGILAXY PARTNER CARD REMOVAL PIPELINE':^65}")
    print("=" * 65)
    print(f"\n  Target domains  : {len(target_domains)}")
    for d in target_domains:
        print(f"    * {d}")
    print(f"\n  Server domains  : {len(all_domains)}")
    for d in all_domains:
        print(f"    * {d}")

    # ── Compare ────────────────────────────────────────────────────────────────
    matched       = [d for d in target_domains if d in all_domains]
    not_on_server = [d for d in target_domains if d not in all_domains]

    report["matched_domains"] = matched
    report["not_on_server"]   = not_on_server

    print(f"\n  Matched      : {len(matched)}")
    print(f"  Not on server: {len(not_on_server)}")

    if not_on_server:
        print(f"\n  WARNING - These will be skipped (not on server):")
        for d in not_on_server:
            print(f"    SKIP {d}")

    if not matched:
        print("\n  INFO No matching domains - nothing to process.")
        print_full_report()
        exit(0)

    print(f"\n  Domains to process:")
    for d in matched:
        print(f"    -> {d}")

    # ── FTP Connect ────────────────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"  Connecting to FTP")
    print(f"  Host : {ftp_host}")
    print(f"  User : {ftp_user}")
    print(f"{'='*65}")

    try:
        ftp = FTP(ftp_host, timeout=30)
        ftp.login(ftp_user, ftp_pass)
        print(f"  OK FTP login successful")
        print(f"  Root directory : {ftp.pwd()}")
    except Exception as e:
        print(f"  FAILED FTP connection: {e}")
        exit(1)

    # ── Process each matched domain ────────────────────────────────────────────
    for domain in matched:
        print(f"\n{'='*65}")
        print(f"  PROCESSING : {domain}")
        print(f"{'='*65}")
        report["results"][domain] = {}

        for folder in PARTNER_FOLDERS:
            res = process_partner_folder(ftp, domain, folder, target_domains)
            report["results"][domain][folder] = res

    ftp.quit()
    print(f"\n  OK FTP connection closed")

    all_ok = print_full_report()
    exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
