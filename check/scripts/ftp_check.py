import ftplib
import os
import json

# Make sure report folder exists
os.makedirs("check", exist_ok=True)

# Load domains (JSON format)
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

for d in domains:
    print(f"Checking FTP access for: {d}")
    if check_ftp(d):
        accessible.append(d)
    else:
        inaccessible.append(d)

# Write report file
with open("check/report.txt", "w") as r:
    r.write("✅ Accessible Domains:\n")
    for d in accessible:
        r.write(f"{d}\n")
    r.write("\n❌ Inaccessible Domains:\n")
    for d in inaccessible:
        r.write(f"{d}\n")

# Print in console for Jenkins visibility
print("\n📄 Report generated: check/report.txt")

if inaccessible:
    print("\n❌ FTP login failed for these domains:")
    for d in inaccessible:
        print(f" - {d}")
else:
    print("\n✅ All domains are accessible via FTP!")
