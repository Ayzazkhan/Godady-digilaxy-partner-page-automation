import requests

# Your API Configuration
API_KEY = "your-openrouter-api-key"
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# Model Rotation System
FREE_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "deepseek/deepseek-r1:free", 
    "deepseek/deepseek-v3:free",
    "openai/gpt-4o-mini:free",
    "anthropic/claude-3-haiku:free",
    "openrouter/auto"
]

# ✅ MUST BE ABOVE generate_content()
def build_prompt(keyword):
    return f"""Create a comprehensive, SEO-optimized article about {keyword}. 
    The article should be well-structured with headings, subheadings, and engaging content.
    Write in a natural, conversational tone and provide valuable information."""

# ✅ FIXED generate_content() with Auto-Fallback
def generate_content(keyword):
    prompt = build_prompt(keyword)

    for model in FREE_MODELS:
        print(f"⚡ Trying model: {model}")

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "HTTP-Referer": "http://localhost",
            "X-Title": "SEO Content Generator"
        }

        try:
            response = requests.post(BASE_URL, json=payload, headers=headers, timeout=40)
        except Exception as e:
            print(f"❌ Network/Timeout Error on {model}: {e}")
            continue

        if response.status_code != 200:
            print(f"❌ Model {model} Error:", response.text[:200])  # First 200 chars only

            # QUOTA HIT → try next model
            if "insufficient_quota" in response.text.lower():
                print("➡ Switching model due to quota...")
                continue

            # Other API errors → try next model
            continue

        data = response.json()

        try:
            content = data["choices"][0]["message"]["content"].strip()
            print(f"✅ Model {model} succeeded!")
            return content
        except (KeyError, IndexError, TypeError):
            print(f"⚠ Invalid response structure from {model}, trying next...")
            continue

    return "GENERATION FAILED"  # This will only show if ALL models fail

# Usage Example
if __name__ == "__main__":
    keyword = "digital marketing"
    content = generate_content(keyword)
    print(f"\n📝 Generated Content:\n{content}")
