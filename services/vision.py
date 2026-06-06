from google import genai
from google.genai import types
import os, json, base64
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


async def analyze_food_photo(photo_bytes: bytes, lang: str) -> dict:
    prompt = """
Analyze this food photo. Respond ONLY in raw JSON, no markdown, no extra text.
{
  "is_food": true or false,
  "dish_name": "name of dish in the user's language",
  "dish_name_en": "name of dish in English",
  "portion_grams": estimated portion weight as a number
}
If no food: {"is_food": false, "dish_name": "", "dish_name_en": "", "portion_grams": 0}
"""
    response = client.models.generate_content(
    model="gemini-2.0-flash-lite",
        contents=[
            types.Part.from_bytes(data=photo_bytes, mime_type="image/jpeg"),
            prompt
        ]
    )
    text = response.text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(text)