#!/usr/bin/env python3
import os, json, io
from datetime import datetime
from ftplib import FTP
import xml.etree.ElementTree as ET

DOMAINS_FILE = "sitemap-setup/data/domains.json"

def create_new_sitemap(domain, ftp):
    """Create a brand new sitemap by scanning folder files"""
    print("🔍 Scanning folder for files...")
    
    try:
        # Get all files in folder
        all_items = []
        ftp.retrlines('LIST', all_items.append)
        
        # Filter for HTML/PHP files
        pages = []
        for item in all_items:
            parts = item.split()
            if len(parts) >= 9:
                filename = parts[-1]
                # Check if it's a file (not directory) and is HTML/PHP
                if not item.startswith('d') and (filename.endswith('.html') or filename.endswith('.php') or filename.endswith('.htm')):
                    pages.append(filename)
        
        print(f"📄 Found {len(pages)} pages: {pages[:10]}")
        
        # Start building sitemap
        urlset = ET.Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")
        
        # Add homepage
        home_url = ET.SubElement(urlset, 'url')
        ET.SubElement(home_url, 'loc').text = f"https://{domain}/"
        ET.SubElement(home_url, 'lastmod').text = timestamp
        ET.SubElement(home_url, 'priority').text = "1.00"
        print(f"✅ Added homepage: https://{domain}/")
        
        # Add found pages
        for page in pages:
            if page == 'index.html' or page == 'index.php':
                continue  # Already added as homepage
            
            # Create URL entry
            url_elem = ET.SubElement(urlset, 'url')
            page_path = page.replace('.html', '').replace('.php', '').replace('.htm', '')
            if page_path == 'index':
                continue
            
            ET.SubElement(url_elem, 'loc').text = f"https://{domain}/{page}"
            ET.SubElement(url_elem, 'lastmod').text = timestamp
            ET.SubElement(url_elem, 'priority').text = "0.80"
        
        print(f"✅ Added {len(pages)} site pages")
        
        # Add partners page
        partners_url = ET.SubElement(urlset, 'url')
        ET.SubElement(partners_url, 'loc').text = f"https://{domain}/partners/"
        ET.SubElement(partners_url, 'lastmod').text = timestamp
        ET.SubElement(partners_url, 'priority').text = "0.80"
        print(f"✅ Added partners page: https://{domain}/partners/")
        
        # Add partners-1 page
        partners1_url = ET.SubElement(urlset, 'url')
        ET.SubElement(partners1_url, 'loc').text = f"https://{domain}/partners-1/"
        ET.SubElement(partners1_url, 'lastmod').text = timestamp
        ET.SubElement(partners1_url, 'priority').text = "0.80"
        print(f"✅ Added partners-1 page: https://{domain}/partners-1/")
        
        # Convert to string
        xml_str = ET.tostring(urlset, encoding='unicode', method='xml')
        sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
        
        total_urls = len(urlset.findall('url'))
        print(f"✨ Generated sitemap with {total_urls} URLs total")
        
        return sitemap
        
    except Exception as e:
        print(f"⚠️  Could not scan folder: {e}")
        print("🔧 Creating basic sitemap instead...")
        
        # Fallback to basic sitemap
        sitemap = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://{domain}/</loc>
    <lastmod>{datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")}</lastmod>
    <priority>1.00</priority>
  </url>
  <url>
    <loc>https://{domain}/partners/</loc>
    <lastmod>{datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")}</lastmod>
    <priority>0.80</priority>
  </url>
  <url>
    <loc>https://{domain}/partners-1/</loc>
    <lastmod>{datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")}</lastmod>
    <priority>0.80</priority>
  </url>
</urlset>'''
        print(f"✅ Created basic sitemap with homepage, partners/ and partners-1/")
        return sitemap

def update_sitemap(content, domain):
    try:
        root = ET.fromstring(content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        ET.register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        urls = root.findall('.//ns:url', namespace)
        
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
        
        # NOW recalculate position AFTER removing duplicates
        # Get all URL elements
        url_elements = root.findall('.//ns:url', namespace)
        
        print(f"📊 URLs in sitemap after cleanup: {len(url_elements)}")
        
        # Find the actual position of the last <url> element in root's children
        last_url_pos = -1
        for idx, child in enumerate(root):
            if child.tag == '{http://www.sitemaps.org/schemas/sitemap/0.9}url' or child.tag == 'url':
                last_url_pos = idx
        
        print(f"📍 Last <url> element at position: {last_url_pos}")
        
        # Find last 0.80 priority (for reference, but we'll insert after last URL)
        last_080 = -1
        for idx, url in enumerate(url_elements):
            priority = url.find('ns:priority', namespace)
            if priority is not None and priority.text == "0.80":
                last_080 = idx
        
        print(f"📍 Last 0.80 priority URL index: {last_080}")
        
        # Create fresh entries
        def make_entry(path):
            url = ET.Element("{http://www.sitemaps.org/schemas/sitemap/0.9}url")
            loc = ET.SubElement(url, "{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
            loc.text = f"https://{domain}/{path}"
            lastmod = ET.SubElement(url, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
            lastmod.text = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")
            priority = ET.SubElement(url, "{http://www.sitemaps.org/schemas/sitemap/0.9}priority")
            priority.text = "0.80"
            return url
        
        # Insert after the last URL element (or at end if no URLs)
        insert_pos = last_url_pos + 1 if last_url_pos >= 0 else len(root)
        print(f"📍 Inserting at position: {insert_pos}")
        
        # Add partners entry
        partners_entry = make_entry("partners/")
        root.insert(insert_pos, partners_entry)
        print(f"✅ Inserted partners/ at position {insert_pos}")
        
        # Add partners-1 entry
        partners1_entry = make_entry("partners-1/")
        root.insert(insert_pos + 1, partners1_entry)
        print(f"✅ Inserted partners-1/ at position {insert_pos + 1}")
        
        # Verify insertion
        final_url_count = len(root.findall('.//ns:url', namespace))
        print(f"✨ Final sitemap has {final_url_count} URLs")
        
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode')
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    domain = os.environ.get("CURRENT_DOMAIN")
    user = os.environ.get("FTP_USER", "all@63u.9b4.mytemp.website")
    password = os.environ.get("FTP_PASS", "A4tech@1234")
    
    if user == "${FTP_USER}": user = "all@63u.9b4.mytemp.website"
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
        
        # Check if sitemap.xml exists
        files = ftp.nlst()
        sitemap_exists = "sitemap.xml" in files
        
        if not sitemap_exists:
            print("⚠️  sitemap.xml not found")
            print("🔧 Generating new sitemap.xml...")
            
            # Create new sitemap by scanning folder
            new_sitemap = create_new_sitemap(domain, ftp)
            
            # Upload new sitemap
            ftp.storbinary("STOR sitemap.xml", io.BytesIO(new_sitemap.encode()))
            print("✅ Uploaded new sitemap.xml")
            print("🎉 SUCCESS - New sitemap created with partners/ and partners-1/")
            
            ftp.quit()
            exit(0)
        
        # Download existing sitemap
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
        print("🎉 SUCCESS - Updated with partners/ and partners-1/")
        
    except Exception as e:
        print(f"❌ {e}")
        exit(0)

if __name__ == "__main__":
    main()
