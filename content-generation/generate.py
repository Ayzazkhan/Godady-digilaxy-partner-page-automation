#!/usr/bin/env python3
import json
import random
import time
import os
import google.generativeai as genai

# -----------------------------
# CONFIG
# -----------------------------
INPUT_FILE = "content.json"
OUTPUT_FILE = "generated_content.json"
TOTAL_CONTENT = 175

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# -----------------------------
# HELPER: EXTRACT DOMAIN FROM SEED CONTENT
# -----------------------------
def extract_domain(seed_text: str):
    start = seed_text.find("href='") + 6
    end = seed_text.find("'", start)
    link = seed_text[start:end]

    # domain extract (without http, https, www)
    domain = link.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
    return domain, link


# -----------------------------
# GEMINI PROMPT
# -----------------------------
def generate_content(seed, domain, link):
    prompt = f"""
Generate 100% unique SEO friendly content.

RULES:
- Do NOT write the domain name "{domain}" in the content.
- Use keyword-based anchor text.
- Add EXACTLY 2 links in the content.
- BOTH links must point to: {link}
- Each link must have a different anchor keyword.
- Anchor text MUST NOT contain the domain name.
- Make it natural, human-written, SEO optimized.
- Output ONLY JSON list with 1 string.

Example format:
[
  "This is sample <a href='{link}'>keyword anchor</a> text and another <a href='{link}'>different keyword anchor</a>."
]

Now generate a new unique content based on this idea:
\"\"\"{seed}\"\"\"
    """

    response = model.generate_content(prompt)
    return response.text


# -----------------------------
# MAIN GENERATION PROCESS
# -----------------------------
def main():
    with open(INPUT_FILE, "r") as f:
        data = json.load(f)

    seed_text = data["seed_content"][0]
    domain, link = extract_domain(seed_text)

    print("Extracted Domain:", domain)
    print("Original Link:", link)

    final_list = []

    for i in range(1, TOTAL_CONTENT + 1):
        print(f"Generating content {i}/{TOTAL_CONTENT}...")

        output = generate_content(seed_text, domain, link)

        try:
            json_output = json.loads(output)
            final_list.extend(json_output)
        except:
            print("[WARN] Output parsing failed, retrying...")
            continue

        time.sleep(1)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(final_list, f, indent=2)

    print("DONE! Generated:", len(final_list))


if __name__ == "__main__":
    main()
