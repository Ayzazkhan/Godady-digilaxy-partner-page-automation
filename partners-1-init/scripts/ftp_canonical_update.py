#!/usr/bin/env python3
import io, os
from ftplib import FTP
from bs4 import BeautifulSoup

def generate_base_html():
    return """<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Partners-1</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"/>
<meta name="robots" content="index, follow"/>
<style>
.client-wrapper {
  text-align: center;
  padding: 10px;
  border: 1px solid #f1ecec;
  height: 400px;
}
</style>
</head>
<body>
<section class="container pt-5">
  <h1 class="text-center">Partners-1</h1>
</section>
</body>
</html>"""

def update_html_content(html, domain):
    """Update HTML with canonical, custom styles, and section"""
    soup = BeautifulSoup(html, "html.parser")
    
    # ====================================
    # 1. ADD CANONICAL TAG
    # ====================================
    head = soup.find("head")
    if not head:
        print("⚠️ No <head> tag found")
        return html
    
    existing_canonical = head.find("link", rel="canonical")
    if existing_canonical:
        print(f"ℹ️ Canonical already exists: {existing_canonical.get('href')}")
    else:
        canonical_url = f"https://www.{domain}/partners-1/"
        canonical_tag = soup.new_tag("link", rel="canonical", href=canonical_url)
        head.append(canonical_tag)
        print(f"✅ Canonical added: {canonical_url}")
    
    # ====================================
    # 2. ADD CSS TO EXISTING <style> TAG
    # ====================================
    additional_css = """
.cid-qKT6knwV2G .wrap-img img {
  max-width: 60%;
  width: 150px;
}
.cid-qKT6knwV2G .client-name {
  color: #8d97ad;
}
.display-5 {
  font-family: 'Montserrat', sans-serif;
  font-size: 0.9rem;
  margin-bottom: 0px;
  padding-top: 10px;
}
.client-wrapper {
  text-align: center;
  padding: 10px;
  border: 1px solid #f1ecec;
  height: 280px;
}
.wrap-img p {
  margin-bottom: 0;
}
.pt-5 {
  padding-top: 5rem !important;
}
.card-box a {
  font-size: 13px;
}
"""
    
    style_tag = head.find("style")
    if style_tag:
        current_styles = style_tag.string or ""
        # Check if already added
        if ".cid-qKT6knwV2G" not in current_styles:
            # Append to existing styles
            style_tag.string = current_styles + additional_css
            print("✅ Custom CSS added to existing <style> tag")
        else:
            print("ℹ️ Custom CSS already exists in <style> tag")
    else:
        # Create new style tag if not exists
        new_style = soup.new_tag("style")
        new_style.string = additional_css
        head.append(new_style)
        print("✅ Created new <style> tag with custom CSS")
    
    # ====================================
    # 3. ADD SECTION BEFORE </body>
    # ====================================
    body = soup.find("body")
    if not body:
        print("⚠️ No <body> tag found")
        return str(soup)
    
    # Check if section already exists
    existing_section = body.find("section", id="clients2-2p")
    if existing_section:
        print("ℹ️ Custom section already exists")
    else:
        # Create new section
        new_section_html = """<section class="features3 cid-qKT6knwV2G" id="clients2-2p" style="background: #cdcdcd2e;">
<div class="container">
<div class="row align-center justify-content-center">

</div>
</div>
</section>"""
        
        # Parse and insert before closing body
        section_soup = BeautifulSoup(new_section_html, "html.parser")
        new_section = section_soup.find("section")
        body.append(new_section)
        print("✅ Custom section added before </body>")
    
    return str(soup)

def main():
    domain = os.environ.get("CURRENT_DOMAIN")
    host = os.environ.get("FTP_HOST")
    ftp_user = os.environ.get("FTP_USER")
    ftp_pass = os.environ.get("FTP_PASS")
    
    if not domain or not host or not ftp_user or not ftp_pass:
        print("❌ Missing environment variables:")
        print(f"   CURRENT_DOMAIN: {domain}")
        print(f"   FTP_HOST: {host}")
        print(f"   FTP_USER: {ftp_user}")
        print(f"   FTP_PASS: {'***' if ftp_pass else 'None'}")
        exit(1)
    
    try:
        print(f"\n🔹 Processing: {domain}")
        print(f"🌐 Host: {host}")
        print(f"👤 User: {ftp_user}")
        
        ftp = FTP(host, timeout=30)
        ftp.login(ftp_user, ftp_pass)
        print("✅ FTP login successful")
        
        # Verify current directory
        current_dir = ftp.pwd()
        print(f"📂 Current directory: {current_dir}")
        
        remote_file = "index.html"
        bio = io.BytesIO()
        
        try:
            ftp.retrbinary(f"RETR {remote_file}", bio.write)
            html = bio.getvalue().decode("utf-8", errors="ignore")
            print(f"✅ Loaded existing index.html ({len(html)} bytes)")
        except:
            print("⚠️ index.html not found — creating new from template")
            html = generate_base_html()
        
        # Update HTML with all modifications
        updated_html = update_html_content(html, domain)
        
        # Upload updated file
        ftp.storbinary(
            f"STOR {remote_file}",
            io.BytesIO(updated_html.encode("utf-8"))
        )
        print(f"✅ Uploaded index.html ({len(updated_html)} bytes)")
        print(f"✅ File location: {current_dir}/{remote_file}")
        
        ftp.quit()
        print(f"🎉 COMPLETED: {domain}")
        
    except Exception as e:
        print(f"❌ ERROR: {domain}")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()
