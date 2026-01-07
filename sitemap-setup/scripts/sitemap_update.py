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
        
        # Check existing
        existing = [url.find('ns:loc', namespace).text for url in urls if url.find('ns:loc', namespace) is not None]
        
        p1 = f"https://{domain}/partners/"
        p2 = f"https://{domain}/partners-1/"
        
        if p1 in existing and p2 in existing:
            print("✅ Already exists")
            return None
        
        # Create entries
        def make_entry(path):
            url = ET.Element("url")
            ET.SubElement(url, "loc").text = f"https://{domain}/{path}"
            ET.SubElement(url, "lastmod").text = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")
            ET.SubElement(url, "priority").text = "0.80"
            return url
        
        pos = last_080 + 1 if last_080 >= 0 else len(urls)
        
        if p1 not in existing:
            root.insert(pos, make_entry("partners/"))
            print(f"✨ Added {p1}")
        
        if p2 not in existing:
            root.insert(pos + 1, make_entry("partners-1/"))
            print(f"✨ Added {p2}")
        
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode')
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    domain = os.environ.get("CURRENT_DOMAIN")
    user = os.environ.get("FTP_USER", "all@studentconsultancy.co.uk")
    password = os.environ.get("FTP_PASS", "A4tech@1234")
    
    if user == "${FTP_USER}": user = "all@studentconsultancy.co.uk"
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
