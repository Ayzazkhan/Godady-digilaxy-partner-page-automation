import json
import os
import google.generativeai as genai
import random

# Gemini API Setup
GEMINI_API_KEY = os.environ.get('GEMINI_KEY')
genai.configure(api_key=GEMINI_API_KEY)

# Load content.json
with open('content.json', 'r', encoding='utf-8') as f:
    content_data = json.load(f)

# Domain and keywords
DOMAIN = "hesiexamtaker.com"
KEYWORDS = ["HESI exam", "nursing exam", "medical test", "healthcare exam", "nursing preparation"]

def generate_content_with_links():
    """Generate content with natural link placement"""
    
    model = genai.GenerativeModel('gemini-pro')
    
    # Different link styles
    link_styles = [
        f"Visit <a href='https://{DOMAIN}'>{DOMAIN}</a> for expert guidance",
        f"Get professional help from <a href='https://{DOMAIN}'>{DOMAIN}</a>",
        f"Experts at <a href='https://{DOMAIN}'>{DOMAIN}</a> can assist you",
        f"Check out <a href='https://{DOMAIN}'>{DOMAIN}</a> for comprehensive resources",
        f"<a href='https://{DOMAIN}'>{DOMAIN}</a> offers the best preparation materials"
    ]
    
    all_generated_content = []
    
    for i in range(175):
        try:
            # Random keyword selection
            keyword = random.choice(KEYWORDS)
            
            prompt = f"""
            Create a unique, SEO-optimized article about {keyword} for nursing students.
            
            Requirements:
            - Include the domain {DOMAIN} naturally 2 times in the content
            - Use different link styles naturally
            - Content should be 300-400 words
            - SEO friendly and engaging
            - Focus on educational value
            
            Format the links like this: <a href='https://{DOMAIN}'>{DOMAIN}</a>
            Make sure links look natural and contextual.
            """
            
            response = model.generate_content(prompt)
            generated_text = response.text
            
            # Ensure exactly 2 links
            link_count = generated_text.count(f"<a href='https://{DOMAIN}'>{DOMAIN}</a>")
            
            if link_count < 2:
                # Add missing links naturally
                sentences = generated_text.split('. ')
                if len(sentences) > 3:
                    # Add first link
                    insert_pos = random.randint(1, len(sentences)//3)
                    sentences.insert(insert_pos, random.choice(link_styles))
                    
                    # Add second link  
                    insert_pos = random.randint(2*len(sentences)//3, len(sentences)-1)
                    sentences.insert(insert_pos, random.choice(link_styles))
                    
                    generated_text = '. '.join(sentences)
            
            all_generated_content.append({
                "id": i+1,
                "keyword": keyword,
                "content": generated_text,
                "links_count": generated_text.count(f"<a href='https://{DOMAIN}'>{DOMAIN}</a>")
            })
            
            print(f"Generated content {i+1}/175")
            
        except Exception as e:
            print(f"Error generating content {i+1}: {str(e)}")
            continue
    
    # Save all generated content
    with open('generated_content.json', 'w', encoding='utf-8') as f:
        json.dump(all_generated_content, f, indent=2, ensure_ascii=False)
    
    print("✅ Content generation completed!")
    print(f"📊 Total generated: {len(all_generated_content)}")

if __name__ == "__main__":
    generate_content_with_links()
