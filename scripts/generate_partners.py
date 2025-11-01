import csv
from pathlib import Path

# File paths
template_path = Path("../templates/partner_block_template.html")
domains_path = Path("../data/domains.csv")
contents_path = Path("../data/contents.csv")
output_dir = Path("../output")
output_dir.mkdir(exist_ok=True)

# Load template
template = template_path.read_text()

# Load domains and contents
domains = [row['domain'] for row in csv.DictReader(open(domains_path))]
contents = [row['content'] for row in csv.DictReader(open(contents_path))]

for domain, content in zip(domains, contents):
    new_html = template.replace("{{content}}", content)
    (output_dir / f"{domain}_partner.html").write_text(new_html)
    print(f"✅ Partner block created for {domain}")

