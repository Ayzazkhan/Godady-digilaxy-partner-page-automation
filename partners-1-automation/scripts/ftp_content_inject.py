#!/usr/bin/env python3
import os, json, io
from ftplib import FTP, error_perm
from bs4 import BeautifulSoup

DOMAINS_FILE = "partners-1-automation/data/domains.json"
CONTENTS_FILE = "partners-1-automation/data/contents.json"
TEMPLATE_FILE = "partners-1-automation/templates/partner_block_template.html"

def inject_into_html(original_html, snippet_html):
    """Inject partner block into existing HTML"""
    soup = BeautifulSoup(original_html, "html.parser")
    
    # Find the row container
    row = soup.find("div", class_="row align-center justify-content-center")
    
    # Parse snippet
    fragment = BeautifulSoup(snippet_html, "html.parser")
    
    if row:
        row.append(fragment)
        print("✅ Content injected into row container")
    elif soup.body:
        soup.body.append(fragment)
        print("⚠️ No row container found, appended to body")
    else:
        print("❌ No suitable location found for injection")
        return original_html
    
    return str(soup)

def handle_domain(domain, host, ftp_user, ftp_pass, content):
    """Process single domain - content injection only"""
    try:
        print(f"\n{'='*60}")
        print(f"🔹 Processing: {domain}")
        print(f"🌐 Host: {host}")
        print(f"👤 User: {ftp_user}")
        print(f"{'='*60}")
        
        # FTP connect
        ftp = FTP(host, timeout=30)
        ftp.login(ftp_user, ftp_pass)
        print("✅ FTP login successful")
        
        # Verify directory
        current_dir = ftp.pwd()
        print(f"📂 Current directory: {current_dir}")
        
        remote_file = "index.html"
        backup_file = "rollback.html"
        
        # Download existing index.html
        bio = io.BytesIO()
        
        try:
            ftp.retrbinary(f"RETR {remote_file}", bio.write)
            bio.seek(0)
            base_html = bio.read().decode("utf-8", errors="ignore")
            print(f"✅ Downloaded index.html ({len(base_html)} bytes)")
        except:
            print("❌ index.html not found on server!")
            ftp.quit()
            return False
        
        # Create backup before modification
        try:
            backup_bytes = io.BytesIO(base_html.encode("utf-8"))
            ftp.storbinary(f"STOR {backup_file}", backup_bytes)
            print(f"✅ Backup created: {backup_file}")
        except Exception as e:
            print(f"⚠️ Backup creation failed: {e}")
        
        # Load template
        with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
            snippet = f.read()
        
        # Replace {{content}} with actual content
        snippet = snippet.replace("{{content}}", content)
        print(f"✅ Template loaded and content replaced")
        
        # Inject snippet into HTML
        updated_html = inject_into_html(base_html, snippet)
        
        if updated_html == base_html:
            print("❌ Injection failed - HTML unchanged")
            ftp.quit()
            return False
        
        # Upload updated HTML
        updated_bytes = io.BytesIO(updated_html.encode("utf-8"))
        ftp.storbinary(f"STOR {remote_file}", updated_bytes)
        print(f"✅ Uploaded {remote_file} ({len(updated_html)} bytes)")
        
        ftp.quit()
        print(f"🎉 COMPLETED: {domain}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {domain}")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    # Get environment variables
    current_domain = os.environ.get("CURRENT_DOMAIN")
    ftp_user = os.environ.get("FTP_USER")  # ✅ This comes from Jenkins credentials
    ftp_pass = os.environ.get("FTP_PASS")
    
    if not current_domain or not ftp_user or not ftp_pass:
        print("❌ Missing environment variables:")
        print(f"   CURRENT_DOMAIN: {current_domain}")
        print(f"   FTP_USER: {ftp_user}")
        print(f"   FTP_PASS: {'***' if ftp_pass else 'None'}")
        exit(1)
    
    # Load domains
    with open(DOMAINS_FILE, "r", encoding="utf-8") as f:
        domains_obj = json.load(f)
    
    domains = list(domains_obj.keys())
    
    if current_domain not in domains:
        print(f"❌ {current_domain} not found in {DOMAINS_FILE}")
        exit(1)
    
    # Load contents
    with open(CONTENTS_FILE, "r", encoding="utf-8") as f:
        contents_list = json.load(f)
        if not isinstance(contents_list, list) or len(contents_list) == 0:
            print("❌ contents.json must be a non-empty JSON array")
            exit(1)
    
    # Get domain index and corresponding content
    idx = domains.index(current_domain)
    content = contents_list[idx % len(contents_list)]
    
    print(f"📝 Content index: {idx % len(contents_list)}")
    print(f"📄 Content preview: {content[:100]}...")
    
    # Get host
    host = domains_obj[current_domain].get("host")
    if not host:
        print(f"❌ Host not defined for {current_domain}")
        exit(1)
    
    # ✅ FTP_USER already has correct format from Jenkins credentials
    # Process domain
    success = handle_domain(current_domain, host, ftp_user, ftp_pass, content)
    
    if not success:
        exit(1)

if __name__ == "__main__":
    main()
