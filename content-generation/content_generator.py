def generate_single_content(keyword):
    prompt = f"""
Write a short promotional SEO paragraph (35-45 words) about {keyword} for nursing students.
Include these links naturally: {chr(10).join(links)}
Tone: {tone}
Make it sound human and professional.
"""

    try:
        headers = {
            "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # ✅ OPTION 1: New official endpoint
        API_URL = "https://router.huggingface.co/hf-inference/models/microsoft/DialoGPT-large"
        
        # ✅ OPTION 2: Alternative endpoint format
        # API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 200,
                "temperature": 0.8,
                "do_sample": True,
                "return_full_text": False
            }
        }
        
        print(f"  📡 Calling Hugging Face API...")
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        print(f"  📊 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                content = result[0].get('generated_text', '').strip()
                if content:
                    print(f"  ✅ Generated content length: {len(content)}")
                    return content
            else:
                print(f"⚠️ Unexpected API response format: {result}")
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")
            
            # ✅ Agar new endpoint fail ho to old endpoint try karo
            if "no longer supported" in response.text:
                print("  🔄 Trying alternative endpoint...")
                API_URL_ALT = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
                response_alt = requests.post(API_URL_ALT, headers=headers, json=payload, timeout=60)
                
                if response_alt.status_code == 200:
                    result_alt = response_alt.json()
                    if isinstance(result_alt, list) and len(result_alt) > 0:
                        content = result_alt[0].get('generated_text', '').strip()
                        if content:
                            print(f"  ✅ Generated via alternative endpoint: {len(content)}")
                            return content
            
    except Exception as e:
        print(f"❌ API Call Failed for {keyword}: {e}")
    
    # Fallback content if all API calls fail
    fallback_content = f"Get expert {keyword} assistance with comprehensive nursing exam preparation and professional guidance. {links[0] if len(links) > 0 else ''} {links[1] if len(links) > 1 else ''}"
    print(f"  🔄 Using fallback content")
    return fallback_content
