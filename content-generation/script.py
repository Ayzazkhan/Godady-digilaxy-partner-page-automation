import json
import argparse
import google.generativeai as genai

parser = argparse.ArgumentParser()
parser.add_argument("--key", required=True)
args = parser.parse_args()

genai.configure(api_key=args.key)

def generate_seo_content(base_content):
    prompt = f"""
You are an SEO expert.
The input content contains 1-2 links with anchor texts.
You must generate 175 unique SEO optimized contents.

RULES:
- Links ka structure bilkul same rehna chahiye (same <a href='...'>)
- Domain name ko exact repeat na karo.
- Us domain se related SEO keywords create karo.
- Har content aik doosray se different ho.
- Tone: professional SEO article line.
- Output in JSON array only.

Base content:
{base_content}
"""

    model = genai.GenerativeModel("gemini-pro")  
    response = model.generate_content(prompt)

    try:
        data = json.loads(response.text)
        return data
    except:
        print("Error parsing AI response")
        return []

# ---- MAIN ----

with open("content.json", "r") as f:
    content_list = json.load(f)

base = content_list[0]  # taking only first content
output = generate_seo_content(base)

with open("output.json", "w") as f:
    json.dump(output, f, indent=2)

print("Generated 175 SEO contents saved in output.json")
