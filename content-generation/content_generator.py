import json
import os
import requests
import random
import time
import re

print("🚀 Starting SEO content generator (DeepSeek Version)...")
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
tone = config.get("tone", "natural and educational")

if not base_content or not domain:
    print("❌ ERROR: base_content or domain missing in content.json")
    exit(1)

print("✅ Loaded base content config")

# DeepSeek API
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

if not DEEPSEEK_API_KEY:
    print("❌ ERROR: DEEPSEEK_API_KEY not found!")
    exit(1)

print("🔥 DeepSeek API Key Loaded")

# Extract links
links = re.findall(r"<a href='https://[^']+'[^>]*>[^<]+</a>", base_content)

if len(links) == 0:
    print("❌ ERROR: No links found inside base_content!")
    exit(1)

print(f"🔗 Found {len(links)} links in base content")


# ---------------------------
# DEEPSEEK REQUEST FUNCTION
# ---------------------------
def deepseek_generate(prompt):
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    res = requests.post(url, json=payload, headers=headers)
    out = res.json()

    return out["choices"][0]["message"]["content"]


# ---------------------------
# CONTENT GENERATOR FUNCTION
# ---------------------------
def generate_single_content(keyword):
    prompt = f"""
You are an SEO expert and professional human content writer.

Write a short promotional SEO paragraph (35–45 words) based on: **{keyword}**.

STYLE:
- Natural human tone
- Nursing exam support type tone
- Unique, human-like, non-AI text
- Must include these links exactly once:
  {json.dumps(links)}

Output only the final paragraph.
"""

    url = "https://api.deepseek.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(url, headers=headers, json=body).json()

    # New DeepSeek output style
    try:
        return response["choices"][0]["message"]["content"].strip()
    except:
        # fallback for DeepSeek-R1 / DeepSeek V3 output format
        if "output_text" in response:
            return response["output_text"].strip()

        raise Exception("Invalid DeepSeek API Response: " + str(response))


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

        time.sleep(0.5)  # DeepSeek is fast, delay can be lower

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
