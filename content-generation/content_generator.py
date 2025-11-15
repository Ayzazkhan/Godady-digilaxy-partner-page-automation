import json
import os
import google.generativeai as genai
import random
import time
import re

print("🚀 Starting SEO content generator...")
print(f"📁 Current directory: {os.getcwd()}")

# Load content.json
try:
    with open("content.json", "r") as f:
        config = json.load(f)
except Exception as e:
    print(f"❌ ERROR reading content.json: {e}")
    exit(1)

base_content = config.get("base_content")
domain = config.get("target_domain")
keywords = config.get("keywords", [])
tone = config.get("tone", "professional and educational")

if not base_content or not domain:
    print("❌ ERROR: base_content or domain missing in content.json")
    exit(1)

print("✅ Loaded base content config")

# Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ ERROR: GEMINI_API_KEY not found!")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro-latest")
print("✅ Gemini model initialized (gemini-pro-latest)")

# Extract links
links = re.findall(r"<a href='https://[^']+'[^>]*>[^<]+</a>", base_content)

if len(links) == 0:
    print("❌ ERROR: No links found inside base_content!")
    exit(1)

print(f"🔗 Found {len(links)} links in base content")


# ---------------------------
# CONTENT GENERATOR FUNCTION
# ---------------------------
def generate_single_content(keyword):
    prompt = f"""
You are an SEO expert and professional human content writer.

Write a short promotional SEO paragraph (35–45 words) based on the topic: **{keyword}**.

STYLE + RULES:
- Natural human tone, no robotic or AI pattern.
- Tone must match Hesiexamtaker services (exam help, guided preparation, confidentiality, expert support).
- Domain name **{domain}** ko exact repeat nahi karna, but concept of "HESI exam help, expert assistance, nursing test support" ko naturally use karna.
- The content should feel like a short promotional description, similar in style to:

Examples:
1. "Pass your HESI pharmacology practice exam with ideal grades. Our platform offers confidential test-taking and focused practice to master this difficult section for your nursing school success."
2. "Pay someone to take my HESI exam is a service that connects nursing students with expert professionals who provide guided help, preparation, and personalized support for better exam performance."

MANDATORY:
- Include these links exactly once each inside the content:
  {json.dumps(links, indent=2)}

OUTPUT:
Only the final content. No explanation. No formatting.

Base content reference:
{base_content}
"""

    response = model.generate_content(prompt)
    return response.text.strip()


# ---------------------------
# MAIN LOOP
# ---------------------------
TOTAL = 175
generated_data = []

print(f"🎯 Generating {TOTAL} SEO contents...")

for i in range(TOTAL):
    try:
        keyword = random.choice(keywords)
        print(f"📝 {i+1}/{TOTAL} Generating for keyword: {keyword}")

        content = generate_single_content(keyword)

        # Ensure all required links are included
        for link in links:
            if link not in content:
                content += f" {link}"

        generated_data.append({
            "id": i + 1,
            "keyword": keyword,
            "content": content,
            "word_count": len(content.split())
        })

        print(f"✅ Generated item {i+1}/{TOTAL}")

        time.sleep(1.5)

    except Exception as e:
        print(f"❌ Error in item {i+1}: {e}")
        continue

# SAVE OUTPUT
print("💾 Saving to output.json...")
try:
    OUTPUT_PATH = os.path.join(os.getcwd(), "output.json")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(generated_data, f, indent=2, ensure_ascii=False)

    print("🎉 SUCCESS! 175 SEO contents saved in output.json")

except Exception as e:
    print(f"❌ Error saving file: {e}")
