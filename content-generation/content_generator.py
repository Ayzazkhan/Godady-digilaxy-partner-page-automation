import json
import os
import google.generativeai as genai
import random
import time

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

# Required link structure from base_content
import re
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
You are an SEO and content writing expert.
Write a **high quality**, **natural**, **human-like** mini article (60–80 words).
The article must be based on the topic: **{keyword}**.

IMPORTANT RULES:
- Content MUST sound 100% natural. No AI pattern, no robotic tone.
- Use the tone: **{tone}**.
- Include these exact links inside the content exactly once each:
  {json.dumps(links, indent=2)}
- Domain name **{domain}** ko exact repeat nahi karna. Us se related keywords use karo.
- Content must be unique, logically structured, and not detectable as AI.
- Output ONLY the final content, no explanation.

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

        # Re-check links
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
    with open("generated_content.json", "w", encoding="utf-8") as f:
        json.dump(generated_data, f, indent=2, ensure_ascii=False)

    print("🎉 SUCCESS! 175 SEO contents saved in output.json")

except Exception as e:
    print(f"❌ Error saving file: {e}")
