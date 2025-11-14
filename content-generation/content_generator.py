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
    print("❌ ERROR: GEMINI_API_KEY not found!")
    exit(1)

print("✅ Gemini API Key found")

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro-latest')
    print("✅ Using gemini-pro-latest model")
except Exception as e:
    print(f"❌ Error configuring Gemini: {e}")
    exit(1)

DOMAIN = "hesiexamtaker.com"
KEYWORDS = ["HESI exam preparation", "nursing exam tips", "medical test strategies"]

def generate_content_with_links():
    """Generate content pieces with links"""
    
    CONTENT_COUNT = 3
    print(f"🎯 Generating {CONTENT_COUNT} content pieces...")
    
    all_generated_content = []
    
    for i in range(CONTENT_COUNT):
        try:
            keyword = random.choice(KEYWORDS)
            
            prompt = f"""
            Create a short article about {keyword} for nursing students.
            Include this link 2 times: <a href='https://{DOMAIN}'>{DOMAIN}</a>
            Content: 100-150 words, educational tone.
            """
            
            print(f"📝 Generating {i+1}/{CONTENT_COUNT}: {keyword}")
            response = model.generate_content(prompt)
            content = response.text
            
            # Ensure content is not empty
            if not content or len(content.strip()) < 10:
                print(f"⚠️ Empty content for {i+1}, using fallback")
                content = f"This is sample content about {keyword}. Visit <a href='https://{DOMAIN}'>{DOMAIN}</a> for more information. Learn more at <a href='https://{DOMAIN}'>{DOMAIN}</a>."
            
            link_count = content.count(f"<a href='https://{DOMAIN}'>{DOMAIN}</a>")
            
            all_generated_content.append({
                "id": i+1,
                "keyword": keyword,
                "content": content,
                "links_count": link_count,
                "word_count": len(content.split())
            })
            
            print(f"✅ {i+1}/{CONTENT_COUNT} - Links: {link_count}, Words: {len(content.split())}")
            
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error {i+1}: {e}")
            # Add fallback content
            all_generated_content.append({
                "id": i+1,
                "keyword": "fallback",
                "content": f"Fallback content. Visit <a href='https://{DOMAIN}'>{DOMAIN}</a> for resources. Check <a href='https://{DOMAIN}'>{DOMAIN}</a> for help.",
                "links_count": 2,
                "word_count": 20
            })
            continue
    
    # SAVE WITH PROPER ERROR HANDLING
    try:
        print("💾 Saving to generated_content.json...")
        with open('generated_content.json', 'w', encoding='utf-8') as f:
            json.dump(all_generated_content, f, indent=2, ensure_ascii=False)
        
        # Verify the file was written
        if os.path.exists('generated_content.json'):
            file_size = os.path.getsize('generated_content.json')
            print(f"✅ File saved successfully! Size: {file_size} bytes")
            
            # Read back to verify
            with open('generated_content.json', 'r', encoding='utf-8') as f:
                verify_data = json.load(f)
            print(f"✅ File verified: {len(verify_data)} items")
        else:
            print("❌ File not created!")
            
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        # Create minimal backup file
        backup_data = [{"error": "Failed to generate proper content"}]
        with open('generated_content.json', 'w') as f:
            json.dump(backup_data, f)

if __name__ == "__main__":
    generate_content_with_links()
