import ftplib

def check_ftp(domain):
    try:
        ftp = ftplib.FTP(domain, timeout=5)
        ftp.quit()
        return True
    except Exception:
        return False

with open("data/domains.txt") as f:
    domains = [line.strip() for line in f if line.strip()]

accessible = []
inaccessible = []

for d in domains:
    print(f"Checking FTP access for: {d}")
    if check_ftp(d):
        accessible.append(d)
    else:
        inaccessible.append(d)

with open("check/report.txt", "w") as r:
    r.write("✅ Accessible Domains:\n")
    for d in accessible:
        r.write(f"{d}\n")
    r.write("\n❌ Inaccessible Domains:\n")
    for d in inaccessible:
        r.write(f"{d}\n")

print("\nReport generated: check/report.txt")
