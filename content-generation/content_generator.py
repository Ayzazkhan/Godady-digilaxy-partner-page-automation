import json
import os
import google.generativeai as genai
import random
import time

print("🚀 Starting content generator...")
print(f"📁 Current directory: {os.getcwd()}")

# Gemini API Setup
GEMINI_API_KEY = os.environ.get('GEMINI_KEY')
if not GEMINI_API_KEY:
    print("❌ ERROR: GEMINI_KEY not found!")
    exit(1)

print("✅ Gemini API Key found")

try:
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Available models check karo
    print("🔍 Checking available models...")
    models = genai.list_models()
    available_models = [model.name for model in models]
    print(f"✅ Available models: {available_models}")
    
    # Gemini Pro ya Gemini 1.0 Pro use karo
    if 'models/gemini-1.0-pro' in available_models:
        model_name = 'models/gemini-1.0-pro'
    elif 'models/gemini-pro' in available_models:
        model_name = 'models/gemini-pro'
    else:
        print("❌ No suitable Gemini model found!")
        print("Available models:", available_models)
        exit(1)
        
    model = genai.GenerativeModel(model_name)
    print(f"✅ Using model: {model_name}")
    
except Exception as e:
    print(f"❌ Error configuring Gemini: {e}")
    exit(1)

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
            "content_count": 5  # Testing ke liye kam content
        }

def generate_content_with_links():
    """Generate content pieces with links"""
    
    content_data = load_content_data()
    
    # Testing ke liye 3 content pieces banate hain
    CONTENT_COUNT = 3
    print(f"🎯 Generating {CONTENT_COUNT} content pieces for testing...")
    
    all_generated_content = []
    
    for i in range(CONTENT_COUNT):
        try:
            keyword = random.choice(KEYWORDS)
            
            prompt = f"""
            Create a short, SEO-optimized article about {keyword} for nursing students.
            
            Requirements:
            - Include this exact link 2 times: <a href='https://{DOMAIN}'>{DOMAIN}</a>
            - Content should be 100-150 words
            - SEO friendly and educational
            - Natural link placement
            
            Format links exactly like: <a href='https://{DOMAIN}'>{DOMAIN}</a>
            """
            
            print(f"📝 Generating {i+1}/{CONTENT_COUNT}: {keyword}")
            response = model.generate_content(prompt)
            content = response.text
            
            link_count = content.count(f"<a href='https://{DOMAIN}'>{DOMAIN}</a>")
            
            all_generated_content.append({
                "id": i+1,
                "keyword": keyword,
                "content": content,
                "links_count": link_count
            })
            
            print(f"✅ Generated {i+1}/{CONTENT_COUNT} - Links: {link_count}")
            
            time.sleep(1)  # Avoid rate limiting
            
        except Exception as e:
            print(f"❌ Error {i+1}: {e}")
            continue
    
    # Save results
    if all_generated_content:
        with open('generated_content.json', 'w', encoding='utf-8') as f:
            json.dump(all_generated_content, f, indent=2, ensure_ascii=False)
        
        print(f"🎉 Completed! Generated {len(all_generated_content)} content pieces")
        print(f"💾 Saved to: generated_content.json")
    else:
        print("❌ No content generated!")
        # Create empty file
        with open('generated_content.json', 'w', encoding='utf-8') as f:
            json.dump([], f)
        print("💾 Created empty generated_content.json")

if __name__ == "__main__":
    generate_content_with_links()
