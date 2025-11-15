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

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

print("✅ Gemini model loaded")

def generate_seo_contents():
    CONTENT_COUNT = 175
    print(f"🎯 Generating {CONTENT_COUNT} SEO contents...")

    results = []

    for i in range(1, CONTENT_COUNT + 1):
        try:
            keyword = random.choice(KEYWORDS)

            prompt = f"""
You are a senior SEO expert and professional medical content writer.
Your job is to generate unique SEO-optimized content for the domain: {DOMAIN}

RULES:
- Length: 120–160 words.
- Tone: {TONE}
- Use SEO-rich variations of the keyword: "{keyword}"
- Do NOT repeat the exact domain name inside text.
- But include this link EXACTLY 2 times inside content:
  <a href='https://{DOMAIN}'>{keyword}</a>

- Every article must be 100% unique.
- NO bullet points. Only paragraph.
- Keep it educational, helpful, and human-like.

Base sample content for your reference:
{BASE_CONTENT}

Return ONLY the article paragraph. No explanation.
"""

            print(f"📝 Generating {i}/{CONTENT_COUNT}: {keyword}")

            response = model.generate_content(prompt)
            content = response.text.strip()

            # Verify links count
            required_link = f"<a href='https://{DOMAIN}'>{keyword}</a>"
            link_count = content.count(required_link)

            # If less than 2 links → force add
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

            time.sleep(1)

        except Exception as e:
            print(f"❌ Error generating content {i}: {e}")
            continue

    return results


# MAIN GENERATION
generated = generate_seo_contents()

# SAVE FILE
try:
    with open("generated_content.json", "w", encoding="utf-8") as f:
        json.dump(generated, f, indent=2, ensure_ascii=False)

    print(f"🎉 SUCCESS! Generated {len(generated)} articles.")
    print("📁 File saved: generated_content.json")

except Exception as e:
    print(f"❌ Error saving output: {e}")
