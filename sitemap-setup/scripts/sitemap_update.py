#!/usr/bin/env python3
import os, json, io
from datetime import datetime
from ftplib import FTP
import xml.etree.ElementTree as ET

DOMAINS_FILE = "sitemap-setup/data/domains.json"

def create_new_sitemap(domain, ftp):
    """Create a new sitemap by scanning folder files or fallback to basic."""
    print("🔍 Scanning folder for files...")
    try:
        all_items = []
        ftp.retrlines('LIST', all_items.append)

        # Filter for HTML/PHP/HTM files
        pages = [item.split()[-1] for item in all_items if len(item.split()) >= 9
                 and not item.startswith('d')
                 and item.split()[-1].endswith(('.html', '.php', '.htm'))]

        print(f"📄 Found {len(pages)} pages: {pages[:10]}")

        urlset = ET.Element('urlset', xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")

        def add_url(path, priority):
            url = ET.SubElement(urlset, 'url')
            ET.SubElement(url, 'loc').text = f"https://{domain}/{path}"
            ET.SubElement(url, 'lastmod').text = timestamp
            ET.SubElement(url, 'priority').text = f"{priority:.2f}"
            return url

        # Homepage
        add_url("", 1.0)
        print(f"✅ Added homepage: https://{domain}/")

        # Pages found
        for page in pages:
            if page.lower() in ('index.html', 'index.php', 'index.htm'):
                continue
            add_url(page, 0.8)
        print(f"✅ Added {len(pages)} site pages")

        # Always add partners pages
        add_url("partners/", 0.8)
        add_url("partners-1/", 0.8)
        print(f"✅ Added partners/ and partners-1/")

        xml_str = ET.tostring(urlset, encoding='unicode', method='xml')
        sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
        return sitemap

    except Exception as e:
        print(f"⚠️ Could not scan folder: {e}")
        print("🔧 Creating basic sitemap instead...")
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")
        sitemap = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://{domain}/</loc>
    <lastmod>{timestamp}</lastmod>
    <priority>1.00</priority>
  </url>
  <url>
    <loc>https://{domain}/partners/</loc>
    <lastmod>{timestamp}</lastmod>
    <priority>0.80</priority>
  </url>
  <url>
    <loc>https://{domain}/partners-1/</loc>
    <lastmod>{timestamp}</lastmod>
    <priority>0.80</priority>
  </url>
</urlset>'''
        print(f"✅ Created basic sitemap with homepage, partners/ and partners-1/")
        return sitemap

def update_sitemap(content, domain):
    """Update existing sitemap to ensure partners/ and partners-1/ exist once."""
    try:
        ET.register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        root = ET.fromstring(content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        urls = root.findall('.//ns:url', namespace)
        partners_links = [f"https://{domain}/partners/", f"https://{domain}/partners-1/"]

        # Remove duplicates
        for url in urls:
            loc = url.find('ns:loc', namespace)
            if loc is not None and loc.text in partners_links:
                root.remove(url)
                print(f"🗑️ Removed duplicate: {loc.text}")

        # Function to create URL entry
        def make_entry(path):
            url_elem = ET.Element("{http://www.sitemaps.org/schemas/sitemap/0.9}url")
            ET.SubElement(url_elem, "{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text = f"https://{domain}/{path}"
            ET.SubElement(url_elem, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod").text = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")
            ET.SubElement(url_elem, "{http://www.sitemaps.org/schemas/sitemap/0.9}priority").text = "0.80"
            return url_elem

        # Append partners pages at the end
        root.append(make_entry("partners/"))
        root.append(make_entry("partners-1/"))
        print(f"✅ Added partners/ and partners-1/ at the end")

        final_count = len(root.findall('.//ns:url', namespace))
        print(f"✨ Final sitemap has {final_count} URLs")

        return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode')

    except Exception as e:
        print(f"❌ Error updating sitemap: {e}")
        return None

def main():
    domain = os.environ.get("CURRENT_DOMAIN")
    user = os.environ.get("FTP_USER", "all@63u.9b4.mytemp.website")
    password = os.environ.get("FTP_PASS", "A4tech@1234")
    
    # Hardcoded fallback
    if user == "${FTP_USER}":
        user = "all@63u.9b4.mytemp.website"
    if password == "${FTP_PASS}":
        password = "A4tech@1234"

    if not domain:
        print("❌ No CURRENT_DOMAIN")
        exit(1)
    
    # Show credentials being used
    print("\n" + "="*70)
    print("🔐 CREDENTIALS CHECK:")
    print("="*70)
    print(f"Username: {user}")
    print(f"Password: {password}")
    print("="*70 + "\n")

    with open(DOMAINS_FILE) as f:
        config = json.load(f)[domain]

    try:
        print(f"\n{'='*70}\n🔹 {domain}\n{'='*70}")

        ftp = FTP(config["host"], timeout=30)
        ftp.login(user, password)
        print("✅ Login successful")
        
        # Check current directory
        current_dir = ftp.pwd()
        print(f"📂 Current directory: {current_dir}")
        
        # List available folders
        try:
            all_items = ftp.nlst()
            folders = []
            for item in all_items:
                try:
                    ftp.cwd(item)
                    folders.append(item)
                    ftp.cwd(current_dir)  # Go back
                except:
                    pass
            print(f"📁 Available folders: {folders[:20]}")
        except Exception as e:
            print(f"⚠️  Could not list folders: {e}")
        
        # Try to change to domain folder
        folder_to_try = config["folder"]
        print(f"🔍 Trying folder: {folder_to_try}")
        
        try:
            ftp.cwd(folder_to_try)
            print(f"✅ Folder: {folder_to_try}")
        except Exception as e:
            print(f"❌ Cannot access folder '{folder_to_try}': {e}")
            print(f"⚠️  Skipping {domain} - folder not found")
            ftp.quit()
            exit(0)

        files = ftp.nlst()
        sitemap_exists = "sitemap.xml" in files

        if not sitemap_exists:
            print("⚠️ sitemap.xml not found. Generating new sitemap...")
            sitemap = create_new_sitemap(domain, ftp)
            ftp.storbinary("STOR sitemap.xml", io.BytesIO(sitemap.encode()))
            print("✅ Uploaded new sitemap.xml")
            ftp.quit()
            print("🎉 SUCCESS - New sitemap created with partners/ and partners-1/")
            exit(0)

        # Download existing sitemap
        bio = io.BytesIO()
        ftp.retrbinary("RETR sitemap.xml", bio.write)
        content = bio.getvalue().decode("utf-8")
        print(f"✅ Downloaded ({len(content)} bytes)")

        # Backup
        ftp.storbinary("STOR backup-sitemap.xml", io.BytesIO(content.encode()))
        print("✅ Backup created")

        # Update
        updated = update_sitemap(content, domain)
        if not updated:
            ftp.quit()
            exit(1)

        # Upload
        ftp.storbinary("STOR sitemap.xml", io.BytesIO(updated.encode()))
        print("✅ Sitemap updated")
        ftp.quit()
        print("🎉 SUCCESS - Updated with partners/ and partners-1/")

    except Exception as e:
        print(f"❌ {e}")
        exit(1)

if __name__ == "__main__":
    main()
