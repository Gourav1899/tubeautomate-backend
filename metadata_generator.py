"""Metadata Generator — OpenRouter + AI Style"""
import json, logging, requests

log = logging.getLogger(__name__)
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
FREE_MODEL = "meta-llama/llama-3.1-8b-instruct:free"

AI_STYLE_PROMPTS = {
    "energetic": "Create VIRAL, high-energy titles with emojis. Use power words like SHOCKING, INSANE, MUST WATCH.",
    "professional": "Create professional, informative titles. Clear and value-focused. No clickbait.",
    "funny": "Create funny, witty titles with humor. Use jokes and casual language.",
    "educational": "Create educational titles. Use 'How to', 'Why', 'What is' format.",
    "custom": ""
}


class MetadataGenerator:
    def __init__(self, api_key: str = None, ai_style: str = "energetic", custom_prompt: str = None):
        import os
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.ai_style = ai_style
        self.custom_prompt = custom_prompt

    def generate(self, filename: str) -> dict:
        clean_name = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
        style = self.custom_prompt if self.ai_style == "custom" and self.custom_prompt else AI_STYLE_PROMPTS.get(self.ai_style, AI_STYLE_PROMPTS["energetic"])

        prompt = f"""YouTube SEO expert. Style: {style}
Video: "{clean_name}"
Return ONLY valid JSON:
{{"title":"title with emoji max 60 chars","description":"400 word SEO description","hashtags":"#tag1 #tag2 ... #tag15","thumbnail_text":"MAX 4 WORDS CAPS"}}"""

        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {"model": FREE_MODEL, "messages": [{"role": "user", "content": prompt}], "max_tokens": 1000}
            resp = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=40)
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"].strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(raw)
        except Exception as e:
            log.error(f"Metadata error: {e}")
            return {
                "title": f"🔥 {clean_name[:55]}",
                "description": f"Watch: {clean_name}\n\nLike & Subscribe! 🔔",
                "hashtags": "#viral #trending #youtube #india",
                "thumbnail_text": "WATCH NOW"
            }
