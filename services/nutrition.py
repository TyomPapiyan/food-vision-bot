from google import genai
import os, json
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


async def get_nutrition(dish_name_en: str, portion_grams: int) -> dict:
    prompt = f"""
Give approximate nutrition facts for "{dish_name_en}" for a {portion_grams}g portion.
Respond ONLY in raw JSON, no markdown, no extra text.
{{
  "calories": number,
  "protein": number,
  "fat": number,
  "carbs": number,
  "portion_grams": {portion_grams}
}}
"""
    response = client.models.generate_content(
    model="gemini-2.0-flash-lite",
        contents=prompt
    )
    text = response.text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(text)