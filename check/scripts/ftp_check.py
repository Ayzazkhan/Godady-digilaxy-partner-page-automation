import ftplib
import os
import json

# ✅ Make sure 'check' folder exists
os.makedirs("check", exist_ok=True)

# ✅ Load domains from JSON
with open("data/domains.json") as f:
    data = json.load(f)
    domains = list(data.keys())

accessible = []
inaccessible = []

def check_ftp(domain):
    try:
        ftp = ftplib.FTP(domain, timeout=5)
        ftp.quit()
        return True
    except Exception:
        return False

# ✅ Process each domain
for d in domains:
    print(f"Checking FTP access for: {d}")
    if check_ftp(d):
        accessible.append(d)
    else:
        inaccessible.append(d)

# ✅ Create report.txt
with open("check/report.txt", "w") as report:
    report.write("✅ Accessible Domains:\n")
    for d in accessible:
        report.write(f"{d}\n")
    report.write("\n❌ Inaccessible Domains:\n")
    for d in inaccessible:
        report.write(f"{d}\n")

# ✅ Print summary in console
print("\n📄 Report generated: check/report.txt\n")

if inaccessible:
    print("❌ FTP FAILED for the following domains:")
    for domain in inaccessible:
        print(f" - {domain}")
else:
    print("✅ All domains are accessible via FTP!")

# ✅ Show totals
print(f"\nSummary: {len(accessible)} accessible | {len(inaccessible)} failed")
