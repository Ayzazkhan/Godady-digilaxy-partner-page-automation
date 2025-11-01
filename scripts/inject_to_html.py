import re
from pathlib import Path

root_dir = Path("../output")
partner_dir = Path("../public_html")

for file in root_dir.glob("*_partner.html"):
    domain = file.name.replace("_partner.html", "")
    partner_html = file.read_text()

    target_html_path = partner_dir / domain / "partners" / "index.html"
    html = target_html_path.read_text()

    # inject before closing </div> of the row container
    updated = re.sub(r'(</div>\s*</div>\s*</section>)',
                     partner_html + r'\n\1', html)

    target_html_path.write_text(updated)
    print(f"✅ Injected partner block into {domain}/partners/index.html")

