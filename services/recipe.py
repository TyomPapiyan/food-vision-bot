from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

LANG_NAMES = {
    "ru": "Russian",
    "en": "English",
    "hy": "Armenian",
}


async def get_recipe(dish_name_en: str, lang: str) -> str:
    language = LANG_NAMES.get(lang, "Russian")
    prompt = f"""
Write a recipe for "{dish_name_en}" in {language}.
Format exactly like this:
**{dish_name_en}**

Ingredients:
- ingredient 1
- ingredient 2

Steps:
1. Step one
2. Step two

Max 6 ingredients and 5 steps. Respond only in {language}.
"""
    response = client.models.generate_content(
    model="gemini-2.0-flash-lite",
        contents=prompt
    )
    return response.text.strip()