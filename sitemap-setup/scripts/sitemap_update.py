#!/usr/bin/env python3
import os, json, io
from datetime import datetime
from ftplib import FTP
import xml.etree.ElementTree as ET

DOMAINS_FILE = "sitemap-setup/data/domains.json"

def update_sitemap(content, domain):
    try:
        root = ET.fromstring(content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        ET.register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        urls = root.findall('.//ns:url', namespace)
        
        # Find last 0.80 priority
        last_080 = -1
        for idx, url in enumerate(urls):
            priority = url.find('ns:priority', namespace)
            if priority is not None and priority.text == "0.80":
                last_080 = idx
        
        p1 = f"https://{domain}/partners/"
        p2 = f"https://{domain}/partners-1/"
        
        # Check for duplicates and remove them first
        urls_to_remove = []
        for url in urls:
            loc = url.find('ns:loc', namespace)
            if loc is not None:
                if loc.text == p1 or loc.text == p2:
                    urls_to_remove.append(url)
                    print(f"🗑️  Found duplicate: {loc.text}")
        
        # Remove duplicates
        for url in urls_to_remove:
            root.remove(url)
            print(f"✅ Removed duplicate")
        
        # Create fresh entries
        def make_entry(path):
            url = ET.Element("url")
            ET.SubElement(url, "loc").text = f"https://{domain}/{path}"
            ET.SubElement(url, "lastmod").text = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")
            ET.SubElement(url, "priority").text = "0.80"
            return url
        
        pos = last_080 + 1 if last_080 >= 0 else len(root)
        
        # Add fresh entries
        root.insert(pos, make_entry("partners/"))
        print(f"✨ Added {p1}")
        
        root.insert(pos + 1, make_entry("partners-1/"))
        print(f"✨ Added {p2}")
        
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode')
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    domain = os.environ.get("CURRENT_DOMAIN")
    user = os.environ.get("FTP_USER", "all@all@nursingassignmenthelps.co.uk")
    password = os.environ.get("FTP_PASS", "A4tech@1234")
    
    if user == "${FTP_USER}": user = "all@all@nursingassignmenthelps.co.uk"
    if password == "${FTP_PASS}": password = "A4tech@1234"
    
    if not domain:
        print("❌ No CURRENT_DOMAIN")
        exit(1)
    
    with open(DOMAINS_FILE) as f:
        config = json.load(f)[domain]
    
    try:
        print(f"\n{'='*70}")
        print(f"🔹 {domain}")
        print(f"{'='*70}")
        
        # Login
        ftp = FTP(config["host"], timeout=30)
        ftp.login(user, password)
        print("✅ Login")
        
        # Go to folder
        ftp.cwd(config["folder"])
        print(f"✅ Folder: {config['folder']}")
        
        # Download
        bio = io.BytesIO()
        ftp.retrbinary("RETR sitemap.xml", bio.write)
        content = bio.getvalue().decode("utf-8")
        print(f"✅ Downloaded ({len(content)} bytes)")
        
        # Backup
        ftp.storbinary("STOR backup-sitemap.xml", io.BytesIO(content.encode()))
        print("✅ Backup")
        
        # Update
        updated = update_sitemap(content, domain)
        if not updated:
            ftp.quit()
            exit(0)
        
        # Upload
        ftp.storbinary("STOR sitemap.xml", io.BytesIO(updated.encode()))
        print("✅ Upload")
        
        ftp.quit()
        print("🎉 SUCCESS")
        
    except Exception as e:
        print(f"❌ {e}")
        exit(0)

if __name__ == "__main__":
    main()
