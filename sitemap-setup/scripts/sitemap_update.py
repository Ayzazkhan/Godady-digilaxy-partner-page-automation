#!/usr/bin/env python3
import os, json, io
from datetime import datetime
from ftplib import FTP, error_perm
from bs4 import BeautifulSoup

DOMAINS_FILE = "sitemap-setup/data/domains.json"

def format_lastmod():
    """Generate current timestamp in sitemap format"""
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")

def create_url_entry(domain, path, priority="0.80"):
    """Create a new URL entry for sitemap"""
    import xml.etree.ElementTree as ET
    url = ET.Element("url")
    
    loc = ET.SubElement(url, "loc")
    loc.text = f"https://{domain}/{path}"
    
    lastmod = ET.SubElement(url, "lastmod")
    lastmod.text = format_lastmod()
    
    prio = ET.SubElement(url, "priority")
    prio.text = priority
    
    return url

def update_sitemap(sitemap_content, domain):
    """Add partners and partners-1 entries to sitemap"""
    try:
        import xml.etree.ElementTree as ET
        
        # Parse XML
        root = ET.fromstring(sitemap_content)
        
        # Define namespace
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        ET.register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        # Find all URL elements
        urls = root.findall('.//ns:url', namespace)
        
        # Find last 0.80 priority entry
        last_080_index = -1
        for idx, url in enumerate(urls):
            priority = url.find('ns:priority', namespace)
            if priority is not None and priority.text == "0.80":
                last_080_index = idx
        
        print(f"📍 Last 0.80 priority entry found at index: {last_080_index}")
        
        # Check if partners entries already exist
        existing_paths = []
        for url in urls:
            loc = url.find('ns:loc', namespace)
            if loc is not None:
                existing_paths.append(loc.text)
        
        partners_url = f"https://{domain}/partners/"
        partners1_url = f"https://{domain}/partners-1/"
        
        if partners_url in existing_paths:
            print(f"⚠️  {partners_url} already exists in sitemap")
        if partners1_url in existing_paths:
            print(f"⚠️  {partners1_url} already exists in sitemap")
        
        # If both already exist, skip
        if partners_url in existing_paths and partners1_url in existing_paths:
            print("✅ Both entries already exist, skipping update")
            return None
        
        # Create new entries
        new_entries = []
        
        if partners_url not in existing_paths:
            partners_entry = create_url_entry(domain, "partners/", "0.80")
            new_entries.append(partners_entry)
            print(f"✨ Created entry: {partners_url}")
        
        if partners1_url not in existing_paths:
            partners1_entry = create_url_entry(domain, "partners-1/", "0.80")
            new_entries.append(partners1_entry)
            print(f"✨ Created entry: {partners1_url}")
        
        # Insert after last 0.80 priority entry
        insert_position = last_080_index + 1 if last_080_index >= 0 else len(urls)
        
        for entry in reversed(new_entries):
            root.insert(insert_position, entry)
        
        # Convert back to string with proper formatting
        xml_string = ET.tostring(root, encoding='unicode', method='xml')
        
        # Add XML declaration
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
        updated_sitemap = xml_declaration + xml_string
        
        print(f"✅ Sitemap updated successfully")
        return updated_sitemap
        
    except Exception as e:
        print(f"❌ Error updating sitemap: {e}")
        import traceback
        traceback.print_exc()
        return None

def handle_domain(domain, host, ftp_user, ftp_pass, folder, base_path=None):
    """Process sitemap for a single domain"""
    try:
        print(f"\n{'='*70}")
        print(f"🔹 Processing: {domain}")
        print(f"🌐 Host: {host}")
        print(f"👤 User: {ftp_user}")
        if base_path:
            print(f"📂 Base Path: {base_path}")
        print(f"📁 Domain Folder: {folder}")
        print(f"{'='*70}")
        
        # Connect to FTP
        ftp = FTP(host, timeout=30)
        ftp.login(ftp_user, ftp_pass)
        print("✅ FTP login successful")
        
        # Check initial directory
        initial_dir = ftp.pwd()
        print(f"📂 Initial directory: {initial_dir}")
        
        # Navigate to base path if provided
        if base_path:
            try:
                ftp.cwd(base_path)
                print(f"✅ Navigated to base path: {base_path}")
            except Exception as e:
                print(f"⚠️  Cannot navigate to base path: {base_path}")
                print(f"   Error: {e}")
                print(f"   Skipping this domain...")
                ftp.quit()
                return "skipped"
        
        # Check current directory
        current_dir = ftp.pwd()
        print(f"📂 Current directory: {current_dir}")
        
        # List folders in current directory
        try:
            items = ftp.nlst()
            print(f"📁 Items in directory ({len(items)} total): {items[:10]}...")
        except Exception as e:
            print(f"⚠️  Cannot list directory: {e}")
            print(f"   Skipping this domain...")
            ftp.quit()
            return "skipped"
        
        # Navigate to domain folder
        if folder not in items:
            print(f"⚠️  Folder '{folder}' not found in {current_dir}!")
            print(f"   Skipping this domain...")
            ftp.quit()
            return "skipped"
        
        # Change to domain folder
        ftp.cwd(folder)
        domain_dir = ftp.pwd()
        print(f"✅ Changed to: {domain_dir}")
        
        # List files in domain folder
        try:
            files = ftp.nlst()
            print(f"📁 Files in {folder} ({len(files)} total): {files[:10]}...")
        except Exception as e:
            print(f"⚠️  Cannot list domain folder: {e}")
            print(f"   Skipping this domain...")
            ftp.quit()
            return "skipped"
        
        sitemap_file = "sitemap.xml"
        backup_file = "backup-sitemap.xml"
        
        if sitemap_file not in files:
            print(f"⚠️  {sitemap_file} not found in {folder}!")
            print(f"   Skipping this domain...")
            ftp.quit()
            return "skipped"
        
        # Download sitemap.xml
        bio = io.BytesIO()
        ftp.retrbinary(f"RETR {sitemap_file}", bio.write)
        bio.seek(0)
        sitemap_content = bio.read().decode("utf-8", errors="ignore")
        print(f"✅ Downloaded {sitemap_file} ({len(sitemap_content)} bytes)")
        
        # Create backup
        try:
            backup_bytes = io.BytesIO(sitemap_content.encode("utf-8"))
            ftp.storbinary(f"STOR {backup_file}", backup_bytes)
            print(f"✅ Backup created: {backup_file}")
        except Exception as e:
            print(f"⚠️  Backup creation warning: {e}")
        
        # Update sitemap
        updated_sitemap = update_sitemap(sitemap_content, domain)
        
        if updated_sitemap is None:
            print("⚠️  No changes needed or update failed")
            ftp.quit()
            return "no_change"
        
        # Upload updated sitemap
        updated_bytes = io.BytesIO(updated_sitemap.encode("utf-8"))
        ftp.storbinary(f"STOR {sitemap_file}", updated_bytes)
        print(f"✅ Uploaded updated {sitemap_file} ({len(updated_sitemap)} bytes)")
        
        ftp.quit()
        print(f"🎉 COMPLETED: {domain}")
        return "success"
        
    except Exception as e:
        print(f"❌ ERROR processing {domain}")
        print(f"   {type(e).__name__}: {str(e)}")
        print(f"   Skipping this domain and continuing...")
        import traceback
        traceback.print_exc()
        return "failed"

def main():
    # Get environment variables from Jenkins
    current_domain = os.environ.get("CURRENT_DOMAIN")
    ftp_user = os.environ.get("FTP_USER")
    ftp_pass = os.environ.get("FTP_PASS")
    
    if not current_domain or not ftp_user or not ftp_pass:
        print("❌ Missing environment variables:")
        print(f"   CURRENT_DOMAIN: {current_domain}")
        print(f"   FTP_USER: {ftp_user}")
        print(f"   FTP_PASS: {'***' if ftp_pass else 'None'}")
        exit(1)
    
    # Load domains configuration
    with open(DOMAINS_FILE, "r", encoding="utf-8") as f:
        domains_obj = json.load(f)
    
    if current_domain not in domains_obj:
        print(f"❌ {current_domain} not found in {DOMAINS_FILE}")
        exit(1)
    
    # Get configuration for this domain
    config = domains_obj[current_domain]
    host = config.get("host")
    folder = config.get("folder", current_domain)
    base_path = config.get("base_path")  # Optional
    
    if not host:
        print(f"❌ Host not defined for {current_domain}")
        exit(1)
    
    # Process the domain
    result = handle_domain(current_domain, host, ftp_user, ftp_pass, folder, base_path)
    
    print("\n" + "="*70)
    print("📊 PROCESSING RESULT:")
    print("="*70)
    
    if result == "success":
        print(f"✅ SUCCESS: {current_domain}")
        print("   Sitemap updated with new entries")
        exit(0)
    elif result == "no_change":
        print(f"⚠️  NO CHANGE: {current_domain}")
        print("   Entries already exist, no update needed")
        exit(0)
    elif result == "skipped":
        print(f"⚠️  SKIPPED: {current_domain}")
        print("   Folder or sitemap not found")
        exit(0)
    else:  # failed
        print(f"❌ FAILED: {current_domain}")
        print("   Error occurred during processing")
        exit(0)
    
    print("="*70)

if __name__ == "__main__":
    main()
