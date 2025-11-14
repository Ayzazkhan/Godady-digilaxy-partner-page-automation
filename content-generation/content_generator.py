import json
import os
import google.generativeai as genai
import random
import time

print("🚀 Starting content generator...")
print(f"📁 Current directory: {os.getcwd()}")

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
KEYWORDS = [
    "HESI exam preparation", "nursing exam tips", "medical test strategies",
    "healthcare exam guide", "nursing study materials", "HESI A2 practice"
]

def generate_content_with_links():
    """Generate content pieces with links"""
    
    CONTENT_COUNT = 10  # Testing ke liye 10 pieces
    print(f"🎯 Generating {CONTENT_COUNT} content pieces...")
    
    all_generated_content = []
    
    for i in range(CONTENT_COUNT):
        try:
            keyword = random.choice(KEYWORDS)
            
            prompt = f"""
            Create a 150-word article about {keyword} for nursing students.
            Include this link 2 times: <a href='https://{DOMAIN}'>{DOMAIN}</a>
            Make it educational and practical.
            """
            
            print(f"📝 Generating {i+1}/{CONTENT_COUNT}: {keyword}")
            response = model.generate_content(prompt)
            content = response.text.strip()
            
            # Ensure content has links
            if f"<a href='https://{DOMAIN}'>{DOMAIN}</a>" not in content:
                content += f" For more resources, visit <a href='https://{DOMAIN}'>{DOMAIN}</a>. Get expert help at <a href='https://{DOMAIN}'>{DOMAIN}</a>."
            
            link_count = content.count(f"<a href='https://{DOMAIN}'>{DOMAIN}</a>")
            
            all_generated_content.append({
                "id": i+1,
                "keyword": keyword,
                "content": content,
                "links_count": link_count,
                "word_count": len(content.split())
            })
            
            print(f"✅ {i+1}/{CONTENT_COUNT} - Links: {link_count}")
            
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error {i+1}: {e}")
            continue
    
    # SAVE WITH STRICT ERROR HANDLING
    try:
        print("💾 Saving to generated_content.json...")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname('generated_content.json'), exist_ok=True)
        
        # Save with explicit encoding
        with open('generated_content.json', 'w', encoding='utf-8') as f:
            json.dump(all_generated_content, f, indent=2, ensure_ascii=False)
        
        # Force write to disk
        f.flush()
        os.fsync(f.fileno())
        
        # Verify file was created and has content
        if os.path.exists('generated_content.json'):
            file_size = os.path.getsize('generated_content.json')
            print(f"✅ File saved! Size: {file_size} bytes")
            
            # Read and verify content
            with open('generated_content.json', 'r', encoding='utf-8') as f:
                saved_content = f.read()
                verify_data = json.loads(saved_content)
            
            print(f"✅ Verification: {len(verify_data)} items, {len(saved_content)} characters")
            
            if len(verify_data) > 0:
                print(f"🎉 SUCCESS: Generated {len(verify_data)} content pieces!")
                print(f"📊 Total links: {sum(item['links_count'] for item in verify_data)}")
            else:
                print("❌ WARNING: File is empty!")
                
        else:
            print("❌ ERROR: File was not created!")
            
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        # Create backup with simple content
        backup_data = [{"id": 1, "keyword": "backup", "content": "Test content with <a href='https://hesiexamtaker.com'>hesiexamtaker.com</a> links.", "links_count": 1}]
        with open('generated_content.json', 'w') as f:
            json.dump(backup_data, f)
        print("⚠️ Created backup file")

if __name__ == "__main__":
    generate_content_with_links()
