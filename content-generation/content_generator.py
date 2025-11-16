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
You are an SEO and content writing expert.
Write a high-quality, natural, human-sounding mini article (30–40 words).
Topic: {keyword}

RULES:
- Content must sound 100% human, natural, and easy to read.
- Use simple English. No tough or complex vocabulary.
- Tone: natural, educational, and SEO-focused.
- Insert these links exactly once each:
  {json.dumps(links)}
- Place hyperlinks on meaningful related phrases (NOT the exact keyword). 
  Example: “Get expert economics assignment help from UK PhD tutors” — hyperlink only on a natural phrase.
- Do NOT repeat the domain name: economicsassignmenthelp.co.uk.
  The domain should appear ONLY inside the hyperlink tag.
- Anchor text must be rewritten in your own natural words (not exact match keywords).
- Links must blend smoothly in the sentence and make the content engaging.
- Style guide:
  • Clear explanation  
  • Helpful tone  
  • Simple English  
  • Light promotion  
  • SEO value  
- Output ONLY the final content. No explanation and no extra wording.

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

    # DEEPSEEK FREE returns result like this:
    #   data["choices"][0]["message"]["content"]

    try:
        return data["choices"][0]["message"]["content"].strip()
    except:
        print("❌ Unexpected API Response:", data)
        return None


# --------------------------
# Start Generation
# --------------------------
results = []
counter = 1

for keyword in keywords:
    print(f"📝 {counter}/{len(keywords)} Generating for: {keyword}")
    content = generate_content(keyword)

    if content:
        results.append({"keyword": keyword, "content": content})
    else:
        print(f"❌ Failed to generate for: {keyword}")

    counter += 1


# --------------------------
# Save Output JSON
# --------------------------
with open("output_content.json", "w") as f:
    json.dump(results, f, indent=2)

print("✅ Finished! Saved output_content.json")
