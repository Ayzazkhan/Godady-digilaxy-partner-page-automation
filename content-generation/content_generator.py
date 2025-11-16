import os
import json
import requests

API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "tngtech/deepseek-r1t2-chimera:free"

print("🚀 Starting SEO content generator (DeepSeek Free Model)...")

if not API_KEY:
    print("❌ ERROR: No API Key Found in Environment Variable: DEEPSEEK_API_KEY")
    exit()

# --------------------------
# Load Base Content JSON
# --------------------------
with open("content.json", "r") as f:
    base_content = json.load(f)

links = base_content.get("links", [])
tone = base_content.get("tone", "natural")
domain = base_content.get("domain", "")
keywords = base_content.get("keywords", [])

print("🔗 Loaded links:", len(links))
print("🎯 Keywords to process:", len(keywords))


# --------------------------
# Generate Content Function
# --------------------------
def generate_content(keyword):
    prompt = f"""
You are an SEO expert and human-like content writer.

Write a short, natural, human-sounding promotional paragraph (35–45 words).
Topic: {keyword}

RULES:
- Use simple English only.
- Tone: friendly, educational, helpful, SEO-focused.
- Must sound 100% human, not AI.
- Insert hyperlinks naturally on meaningful rewritten phrases.
- Domain name ({domain}) must ONLY appear inside <a href=""> tag.
- Do NOT use exact match keywords for anchor text.
- Style must be smooth, clear, helpful, natural.
- Follow this writing style:
  “Get expert <a href='https://www.economicsassignmenthelp.co.uk'>economics assignment help</a> from UK PhD <a href='https://www.economicsassignmenthelp.co.uk'>economics assignment experts</a>…”
- Output ONLY the paragraph. No explanation.
"""

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "http://localhost",
        "X-Title": "SEO Content Generator"
    }

    response = requests.post(BASE_URL, json=payload, headers=headers)

    if response.status_code != 200:
        print("❌ API Error:", response.text)
        return None

    data = response.json()

    try:
        return data["choices"][0]["message"]["content"].strip()
    except:
        print("❌ Unexpected API Response:", data)
        return None


# --------------------------
# Generate 10 content per keyword
# --------------------------
results = []

for keyword in keywords:
    print("\n==============================")
    print(f"🔍 Keyword: {keyword}")
    print("==============================")

    keyword_contents = []

    for i in range(1, 11):
        print(f"📝 Generating {i}/10 for: {keyword}")
        content = generate_content(keyword)

        if content:
            keyword_contents.append(content)
        else:
            print(f"❌ Failed to generate {i} for: {keyword}")

    results.append({
        "keyword": keyword,
        "contents": keyword_contents
    })


# --------------------------
# Save Output JSON
# --------------------------
with open("output_content.json", "w") as f:
    json.dump(results, f, indent=2)

print("✅ Finished! Saved output_content.json")
