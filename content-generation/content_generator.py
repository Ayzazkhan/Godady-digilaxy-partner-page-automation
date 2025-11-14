import json
import os
import google.generativeai as genai
import random
import time

print("🚀 Starting content generator...")
print(f"📁 Current directory: {os.getcwd()}")
print(f"📁 Files here: {os.listdir('.')}")

# Gemini API Setup
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("❌ ERROR: GEMINI_KEY not found!")
    exit(1)

print("✅ Gemini API Key found")
genai.configure(api_key=GEMINI_API_KEY)

DOMAIN = "hesiexamtaker.com"
KEYWORDS = [
    "HESI exam preparation", "nursing exam tips", "medical test strategies", 
    "healthcare exam guide", "nursing study materials", "HESI A2 practice"
]

def load_content_data():
    """Load content.json"""
    try:
        with open('content.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            print("✅ content.json loaded successfully")
            return data
    except Exception as e:
        print(f"❌ Error loading content.json: {e}")
        return {
            "target_domain": DOMAIN,
            "keywords": KEYWORDS,
            "content_count": 175
        }

def generate_content_with_links():
    """Generate 175 content pieces with links"""
    
    model = genai.GenerativeModel('gemini-pro')
    content_data = load_content_data()
    
    all_generated_content = []
    
    for i in range(175):
        try:
            keyword = random.choice(KEYWORDS)
            
            prompt = f"""
            Create a unique, SEO-optimized article about {keyword} for nursing students.
            
            Requirements:
            - Include this exact link 2 times: <a href='https://{DOMAIN}'>{DOMAIN}</a>
            - Content should be 250-350 words
            - SEO friendly and educational
            - Natural link placement
            - Professional tone
            
            Format links exactly like: <a href='https://{DOMAIN}'>{DOMAIN}</a>
            """
            
            print(f"📝 Generating {i+1}/175: {keyword}")
            response = model.generate_content(prompt)
            content = response.text
            
            all_generated_content.append({
                "id": i+1,
                "keyword": keyword,
                "content": content,
                "links_count": content.count(f"<a href='https://{DOMAIN}'>{DOMAIN}</a>")
            })
            
            print(f"✅ Generated {i+1}/175 - Links: {content.count(f'<a href=https://{DOMAIN}>{DOMAIN}</a>')}")
            
            time.sleep(2)  # Avoid rate limiting
            
        except Exception as e:
            print(f"❌ Error {i+1}: {e}")
            continue
    
    # Save results
    with open('generated_content.json', 'w', encoding='utf-8') as f:
        json.dump(all_generated_content, f, indent=2, ensure_ascii=False)
    
    print(f"🎉 Completed! Generated {len(all_generated_content)} content pieces")

if __name__ == "__main__":
    generate_content_with_links()
