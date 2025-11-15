import json
import os
import google.generativeai as genai
import random
import time

print("🚀 Starting SEO Content Generator...")
print(f"📁 Current Directory: {os.getcwd()}")

# Load Content.json
try:
    with open("content.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    print("✅ content.json loaded successfully")
except Exception as e:
    print(f"❌ ERROR reading content.json: {e}")
    exit(1)

BASE_CONTENT = config["base_content"]
DOMAIN = config["target_domain"]
KEYWORDS = config["keywords"]
TONE = config["tone"]

# Gemini API Key
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("❌ ERROR: GEMINI_API_KEY not found!")
    exit(1)

# CONFIGURE API
genai.configure(api_key=GEMINI_API_KEY)

# NEW WORKING MODEL
model = genai.GenerativeModel("gemini-1.5-flash")

print("✅ Gemini model loaded: gemini-1.5-flash")

def generate_seo_contents():
    CONTENT_COUNT = 175
    print(f"🎯 Generating {CONTENT_COUNT} SEO contents...")

    results = []

    for i in range(1, CONTENT_COUNT + 1):
        try:
            keyword = random.choice(KEYWORDS)

            prompt = f"""
You are a senior SEO expert and professional medical content writer.
Generate a unique 140–160 word article about "{keyword}".

RULES:
- Use tone: {TONE}
- Insert this link EXACTLY 2 times inside natural sentences:
  <a href='https://{DOMAIN}'>{keyword}</a>

- Do NOT repeat the domain name in naked form.
- No bullet points.
- 100% unique content.
- Educational & helpful.
- Single paragraph only.

Base sample content for understanding:
{BASE_CONTENT}

Return only the article paragraph. No extra text.
"""

            print(f"📝 Generating {i}/{CONTENT_COUNT}: {keyword}")

            response = model.generate_content(prompt)
            content = response.text.strip()

            required_link = f"<a href='https://{DOMAIN}'>{keyword}</a>"
            link_count = content.count(required_link)

            # Ensure exactly 2 links
            while link_count < 2:
                content += f" Learn more at <a href='https://{DOMAIN}'>{keyword}</a>."
                link_count += 1

            results.append({
                "id": i,
                "keyword": keyword,
                "content": content,
                "links": link_count,
                "words": len(content.split())
            })

            time.sleep(0.8)

        except Exception as e:
            print(f"❌ Error generating content {i}: {e}")
            continue

    return results


# SAVE RESULTS
generated = generate_seo_contents()

try:
    with open("generated_content.json", "w", encoding="utf-8") as f:
        json.dump(generated, f, indent=2, ensure_ascii=False)

    print(f"🎉 SUCCESS! Generated {len(generated)} articles.")
    print("📁 File saved: generated_content.json")

except Exception as e:
    print(f"❌ Error saving output: {e}")
