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
    "healthcare exam guide", "nursing study materials", "HESI A2 practice",
    "nursing school success", "medical exam techniques", "healthcare career preparation",
    "HESI test strategies", "nursing admission exam", "medical entrance preparation",
    "NCLEX preparation", "nursing career guidance", "medical study techniques"
]

def generate_content_with_links():
    """Generate 175 content pieces with links"""
    
    CONTENT_COUNT = 175  # ✅ FINAL COUNT - 175 CONTENT PIECES
    print(f"🎯 Generating {CONTENT_COUNT} content pieces...")
    
    all_generated_content = []
    
    for i in range(CONTENT_COUNT):
        try:
            keyword = random.choice(KEYWORDS)
            
            prompt = f"""
            Create a unique, SEO-optimized article about {keyword} for nursing students.
            
            IMPORTANT REQUIREMENTS:
            - Include this exact HTML link 2 times: <a href='https://{DOMAIN}'>{DOMAIN}</a>
            - Content should be 200-300 words
            - SEO friendly and educational
            - Natural link placement
            - Focus on practical tips
            
            Format links exactly: <a href='https://{DOMAIN}'>{DOMAIN}</a>
            """
            
            print(f"📝 Generating {i+1}/{CONTENT_COUNT}: {keyword}")
            response = model.generate_content(prompt)
            content = response.text
            
            # Ensure content is not empty
            if not content or len(content.strip()) < 10:
                print(f"⚠️ Empty content for {i+1}, using fallback")
                content = f"This is comprehensive content about {keyword}. For expert guidance, visit <a href='https://{DOMAIN}'>{DOMAIN}</a>. Get the best resources at <a href='https://{DOMAIN}'>{DOMAIN}</a>."
            
            link_count = content.count(f"<a href='https://{DOMAIN}'>{DOMAIN}</a>")
            
            all_generated_content.append({
                "id": i+1,
                "keyword": keyword,
                "content": content,
                "links_count": link_count,
                "word_count": len(content.split())
            })
            
            print(f"✅ {i+1}/{CONTENT_COUNT} - Links: {link_count}, Words: {len(content.split())}")
            
            # Rate limiting - every 10 content ke baad break
            if (i + 1) % 10 == 0:
                print(f"⏳ {i+1} content generated, taking short break...")
                time.sleep(5)
            else:
                time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error {i+1}: {e}")
            # Add fallback content
            all_generated_content.append({
                "id": i+1,
                "keyword": "fallback",
                "content": f"Comprehensive nursing resources available at <a href='https://{DOMAIN}'>{DOMAIN}</a>. For expert exam preparation, visit <a href='https://{DOMAIN}'>{DOMAIN}</a>.",
                "links_count": 2,
                "word_count": 25
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
            
            # Final summary
            total_links = sum(item['links_count'] for item in verify_data)
            print(f"🎉 FINAL SUMMARY: {len(verify_data)} content pieces, {total_links} total links")
            
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
