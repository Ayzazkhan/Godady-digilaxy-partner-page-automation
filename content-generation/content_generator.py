import json
import os
import requests
import random
import time
import re

print("🚀 Starting SEO content generator (Hugging Face Version)...")
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

# Hugging Face API Configuration
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")

if not HUGGINGFACE_API_KEY:
    print("❌ ERROR: HUGGINGFACE_API_KEY not found!")
    exit(1)

print("🔥 Hugging Face API Key Loaded")

# Extract links
links = re.findall(r"<a href='https://[^']+'[^>]*>[^<]+</a>", base_content)

if len(links) == 0:
    print("❌ ERROR: No links found inside base_content!")
    exit(1)

print(f"🔗 Found {len(links)} links in base content")

# ---------------------------
# HUGGING FACE CONTENT GENERATOR FUNCTION
# ---------------------------
def generate_single_content(keyword):
    prompt = f"""
You are an SEO expert and professional human content writer.

Write a short promotional SEO paragraph (35-45 words) based on the topic: **{keyword}**.

STYLE + RULES:
- Natural human tone, no robotic or AI pattern.
- Tone must match Hesiexamtaker services (exam help, guided preparation, confidentiality, expert support).
- Domain name **{domain}** ko exact repeat nahi karna, but concept of "HESI exam help, expert assistance, nursing test support" ko naturally use karna.

MANDATORY:
- Include these links exactly once each inside the content:
{chr(10).join(links)}

OUTPUT:
Only the final content. No explanation. No formatting.
"""

    try:
        headers = {
            "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Hugging Face Inference API - using a good free model
        API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 200,
                "temperature": 0.8,
                "do_sample": True,
                "return_full_text": False
            },
            "options": {
                "wait_for_model": True
            }
        }
        
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                content = result[0].get('generated_text', '').strip()
                if content:
                    return content
                else:
                    print(f"⚠️ Empty content from API for {keyword}")
            else:
                print(f"⚠️ Unexpected API response format for {keyword}")
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ API Call Failed for {keyword}: {e}")
    
    # Fallback content if API fails
    fallback_content = f"Looking for expert {keyword} assistance? Get comprehensive support and professional guidance for your nursing exam preparation. {links[0] if len(links) > 0 else ''} {links[1] if len(links) > 1 else ''}"
    return fallback_content

# ---------------------------
# MAIN LOOP
# ---------------------------
TOTAL = 50  # Safe limit for free tier
generated_data = []

print(f"🎯 Generating {TOTAL} SEO contents with Hugging Face...")

for i in range(TOTAL):
    try:
        keyword = random.choice(keywords)
        print(f"📝 {i+1}/{TOTAL} Generating for keyword: {keyword}")

        content = generate_single_content(keyword)

        # Ensure all required links are included
        links_included = 0
        for link in links:
            if link in content:
                links_included += 1
            else:
                content += f" {link}"

        generated_data.append({
            "id": i + 1,
            "keyword": keyword,
            "content": content,
            "word_count": len(content.split()),
            "links_included": links_included
        })

        print(f"✅ Generated item {i+1}/{TOTAL} - Links: {links_included}")

        time.sleep(2)  # Rate limiting for free API

    except Exception as e:
        print(f"❌ Error in item {i+1}: {e}")
        continue

# SAVE OUTPUT
print("💾 Saving to output.json...")
try:
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(generated_data, f, indent=2, ensure_ascii=False)

    print(f"🎉 SUCCESS! {len(generated_data)} SEO contents saved in output.json")
    print(f"📊 Total links included: {sum(item['links_included'] for item in generated_data)}")

except Exception as e:
    print(f"❌ Error saving file: {e}")
