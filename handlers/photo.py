import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message

from database.db import get_user_language, check_subscription, increment_scans, get_today_scans
from keyboards.main_kb import result_keyboard, subscription_keyboard
from services.vision import analyze_food_photo
from services.recipe import get_recipe
from services.nutrition import get_nutrition
from locales import t

router = Router()

user_last_result = {}

FREE_SCANS_LIMIT = 3


@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)

    has_sub = await check_subscription(user_id)

    if not has_sub:
        # Проверяем сколько сканов сделано СЕГОДНЯ (лимит обновляется каждый день)
        today_scans = await get_today_scans(user_id)

        if today_scans >= FREE_SCANS_LIMIT:
            await message.answer(
                t(lang, "no_subscription"),
                reply_markup=subscription_keyboard(lang),
                parse_mode="Markdown"
            )
            return

    status_msg = await message.answer(t(lang, "analyzing"))

    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    photo_bytes = await bot.download_file(file.file_path)
    photo_bytes = photo_bytes.read()

    try:
        vision_result = await analyze_food_photo(photo_bytes, lang)
    except Exception:
        await status_msg.delete()
        await message.answer(t(lang, "error"))
        return

    if not vision_result.get("is_food", True):
        await status_msg.delete()
        await message.answer(t(lang, "not_food"), reply_markup=result_keyboard(lang))
        return

    dish_name = vision_result.get("dish_name", "Unknown")
    dish_name_en = vision_result.get("dish_name_en", dish_name)
    portion = vision_result.get("portion_grams", 200)

    try:
        nutrition, recipe = await asyncio.gather(
            get_nutrition(dish_name_en, portion),
            get_recipe(dish_name_en, lang),
        )
    except Exception:
        await status_msg.delete()
        await message.answer(t(lang, "error"))
        return

    await increment_scans(user_id)

    user_last_result[user_id] = {
        "dish_name": dish_name,
        "dish_name_en": dish_name_en,
        "nutrition": nutrition,
        "recipe": recipe,
    }

    await status_msg.delete()

    n = nutrition
    text = (
        f"🍽 *{dish_name}*\n\n"
        f"*{t(lang, 'nutrition_title')}*\n"
        f"🔥 {t(lang, 'calories')}: {n.get('calories', 0):.0f} ккал\n"
        f"🥩 {t(lang, 'protein')}: {n.get('protein', 0):.1f}г\n"
        f"🧈 {t(lang, 'fat')}: {n.get('fat', 0):.1f}г\n"
        f"🌾 {t(lang, 'carbs')}: {n.get('carbs', 0):.1f}г\n"
        f"⚖️ {t(lang, 'portion')}: {n.get('portion_grams', portion)}г"
    )

    if not has_sub:
        left = FREE_SCANS_LIMIT - (await get_today_scans(user_id))
        text += f"\n\n📊 _Осталось бесплатных сканов сегодня: {left}_"

    await message.answer(text, reply_markup=result_keyboard(lang), parse_mode="Markdown")