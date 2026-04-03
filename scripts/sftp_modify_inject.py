#!/usr/bin/env python3
import os
import json
import io
from ftplib import FTP
from bs4 import BeautifulSoup

# ── Paths ──────────────────────────────────────────────────────────────────────
DOMAINS_FILE    = "data/domains.json"     # jin cards hatane hain
ALLDOMAINS_FILE = "data/alldomains.json"  # server pe jo site folders hain
PARTNER_FOLDERS = ["partners", "partners-1"]

report = {
    "target_domains"  : [],
    "server_sites"    : [],
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
    Remove cards whose any anchor href contains any of the target domains.
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
                    card_details.append(f"{domain} -> {a['href'].strip()}")
                    card.decompose()
                    removed += 1
                    break
            else:
                continue
            break

    return str(soup), removed, card_details


def process_partner_folder(ftp, site, folder_name, target_domains):
    """Process one partner folder inside a site."""
    index_path    = f"{site}/{folder_name}/index.html"
    rollback_path = f"{site}/{folder_name}/rollback.html"

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
        result["status"] = "NOT FOUND"
        print(f"         NOT FOUND: {e}")
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

    print(f"[1] TARGET DOMAINS (cards to remove) -- Total: {len(report['target_domains'])}")
    for d in report["target_domains"]:
        print(f"      * {d}")

    print(f"\n[2] SERVER SITES (folders processed) -- Total: {len(report['server_sites'])}")
    for d in report["server_sites"]:
        print(f"      * {d}")

    print(f"\n{sep}")
    print(f"{'SITE-WISE PROCESSING DETAILS':^65}")
    print(f"{sep}")

    overall_success     = 0
    overall_failed      = 0
    total_cards_removed = 0

    for site, folders in report["results"].items():
        statuses  = [v["status"] for v in folders.values()]
        site_ok   = all(s in ("SUCCESS", "NO_CARDS_MATCHED", "NOT FOUND") for s in statuses)

        icon = "SUCCESS" if site_ok else "FAILED"
        print(f"\n  [{icon}] SITE : {site}")
        print(f"  {sep2}")

        for folder, res in folders.items():
            s = res["status"]
            if s == "SUCCESS":
                status_str = "SUCCESS"
            elif s == "NO_CARDS_MATCHED":
                status_str = "NO CARDS MATCHED"
            elif s == "NOT FOUND":
                status_str = "FOLDER NOT FOUND"
            else:
                status_str = f"FAILED - {s}"

            backup_str = "CREATED" if res["backup"] == "CREATED" else f"{res['backup']}"

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

        if site_ok:
            overall_success += 1
        else:
            overall_failed += 1

    print(f"\n{sep}")
    print(f"{'FINAL SUMMARY':^65}")
    print(f"{sep}")
    print(f"  Target Domains (cards)   : {len(report['target_domains'])}")
    print(f"  Sites Processed          : {len(report['server_sites'])}")
    print(f"  Sites OK                 : {overall_success}")
    print(f"  Sites Failed             : {overall_failed}")
    print(f"  Total Cards Removed      : {total_cards_removed}")
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

    print("=" * 65)
    print(f"{'DIGILAXY PARTNER CARD REMOVAL PIPELINE':^65}")
    print("=" * 65)

    # ── Load domains.json (LOCAL) ─────────────────────────────────────────────
    with open(DOMAINS_FILE, "r", encoding="utf-8") as f:
        target_domains = json.load(f)
    report["target_domains"] = target_domains
    print(f"\n  Cards to remove from  : {len(target_domains)} domain(s)")
    for d in target_domains:
        print(f"    * {d}")

    # ── Load alldomains.json (LOCAL) ──────────────────────────────────────────
    with open(ALLDOMAINS_FILE, "r", encoding="utf-8") as f:
        server_sites = json.load(f)
    report["server_sites"] = server_sites
    print(f"\n  Server sites to scan  : {len(server_sites)}")
    for d in server_sites:
        print(f"    * {d}")

    # ── FTP Connect ───────────────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"  Connecting to FTP")
    print(f"  Host : {ftp_host}")
    print(f"  User : {ftp_user}")
    print(f"{'='*65}")

    try:
        ftp = FTP(ftp_host, timeout=30)
        ftp.login(ftp_user, ftp_pass)
        print(f"  OK FTP LOGIN SUCCESSFUL")
        print(f"  Root directory : {ftp.pwd()}")
    except Exception as e:
        print(f"  FAILED FTP connection: {e}")
        exit(1)

    # ── Process each server site ──────────────────────────────────────────────
    for site in server_sites:
        print(f"\n{'='*65}")
        print(f"  SCANNING SITE : {site}")
        print(f"{'='*65}")
        report["results"][site] = {}

        for folder in PARTNER_FOLDERS:
            res = process_partner_folder(ftp, site, folder, target_domains)
            report["results"][site][folder] = res

    ftp.quit()
    print(f"\n  OK FTP connection closed")

    all_ok = print_full_report()
    exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
