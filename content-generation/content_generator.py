import os
import json
import requests
import concurrent.futures
import time

API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

FREE_MODELS = [
    "deepseek/deepseek-r1:free",
    "deepseek/deepseek-v3:free",
    "deepseek/deepseek-r1-distill-qwen-32b:free",
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-2.0-flash-lite:free",
    "openai/gpt-oss-20b:free",
    "openai/gpt-4o-mini:free",
    "meta-llama/llama-3.1-8b-instruct:free",
    "qwen/qwen2.5-7b-instruct:free",
    "qwen/qwen2.5-14b-instruct:free",
    "meituan/longcat-flash:free",
    "01-ai/yi-large:free",
    "mistralai/mistral-nemo:free",
    "cognitivecomputations/dolphin-mixtral-8x7b:free"
]

# Auto model scoring storage
model_scores = {m: 0 for m in FREE_MODELS}

# Load base content
with open("content.json", "r") as f:
    base_content = json.load(f)

keywords = base_content.get("keywords", [])
domain = base_content.get("domain", "")

def send_request(model, prompt):
    try:
        response = requests.post(
            BASE_URL,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}]
            },
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "HTTP-Referer": "http://localhost",
                "X-Title": "SEO Generator"
            },
            timeout=20
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"], model
        return None, model
    except:
        return None, model


def generate_with_fallback(prompt):
    # sort by score → best-attempted model first
    sorted_models = sorted(model_scores.keys(), key=lambda m: model_scores[m], reverse=True)

    for model in sorted_models:
        content, used_model = send_request(model, prompt)

        if content:
            model_scores[used_model] += 1   # reward model
            return content

        # penalty if failed
        model_scores[used_model] -= 1

    return None


def build_prompt(keyword):
    return f"""
Write a human-sounding, simple-English promotional paragraph (35–45 words).

Topic: {keyword}
Target domain: {domain}

RULES:
- Paragraph MUST start with one of these words: Best, Get, Need, Our.
- Use simple English only. No hard or complex vocabulary.
- Tone must be friendly, soft, educational, persuasive, and marketing-focused.
- Add EXACTLY two (2) anchor tags.
- Both anchor tags MUST redirect to the domain: {domain}
- Anchor text must be rewritten naturally (not the exact keyword).
- Hyperlinks must be placed on meaningful helpful phrases.
- Domain name must appear ONLY inside the <a href=""> tag.
- Paragraph must sound 100% human.
- Do NOT repeat exact-match keywords.
- Output only the final paragraph. No explanation.
"""



def process_keyword(keyword):
    outputs = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []

        for _ in range(10):  # generate 10 per keyword
            prompt = build_prompt(keyword)
            futures.append(executor.submit(generate_with_fallback, prompt))

        for future in futures:
            result = future.result()
            outputs.append(result if result else "GENERATION FAILED")

    return {"keyword": keyword, "contents": outputs}


# Run the whole pipeline
final_results = []

for keyword in keywords:
    print(f"⚡ Processing keyword: {keyword}")
    data = process_keyword(keyword)
    final_results.append(data)

# Save file
with open("output_content.json", "w") as f:
    json.dump(final_results, f, indent=2)

print("🎉 DONE! Parallel, auto-scoring, fail-proof system ready.")
