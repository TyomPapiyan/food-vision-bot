from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove
import os

from database.db import (
    get_user_language, save_food_log, get_today_log,
    check_subscription, get_subscription, use_promo,
    get_referral_count, cancel_subscription
)
from keyboards.main_kb import main_menu, language_keyboard, subscription_keyboard
from locales import t
from locales.ru import texts as ru_texts
from locales.en import texts as en_texts
from locales.hy import texts as hy_texts
from handlers.photo import user_last_result

router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Собираем все возможные тексты кнопок из всех языков
def all_btn(key):
    return {ru_texts[key], en_texts[key], hy_texts[key]}


@router.message(F.text.in_(all_btn("btn_end")))
async def btn_end(message: Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    await message.answer(t(lang, "end"), reply_markup=ReplyKeyboardRemove())


@router.message(F.text.in_(all_btn("btn_restart")))
async def btn_restart(message: Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    await message.answer(t(lang, "restart"), reply_markup=main_menu(lang))
    await message.answer(t(lang, "send_photo"))


@router.message(F.text.in_(all_btn("btn_analyze")))
async def btn_analyze(message: Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    await message.answer(t(lang, "send_photo"))


@router.message(F.text.in_(all_btn("btn_recipe")))
async def btn_recipe(message: Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    result = user_last_result.get(user_id)
    if not result:
        await message.answer(t(lang, "send_photo"))
        return
    await message.answer(result["recipe"], parse_mode="Markdown")


@router.message(F.text.in_(all_btn("btn_save")))
async def btn_save(message: Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    result = user_last_result.get(user_id)
    if not result:
        await message.answer(t(lang, "send_photo"))
        return
    n = result["nutrition"]
    await save_food_log(
        user_id, result["dish_name"],
        n.get("calories", 0), n.get("protein", 0),
        n.get("fat", 0), n.get("carbs", 0),
    )
    await message.answer(t(lang, "saved"))


@router.message(F.text.in_(all_btn("btn_diary")))
async def btn_diary(message: Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    rows = await get_today_log(user_id)
    if not rows:
        await message.answer(t(lang, "diary_empty"))
        return
    total_cal = sum(r[1] for r in rows)
    total_p = sum(r[2] for r in rows)
    total_f = sum(r[3] for r in rows)
    total_c = sum(r[4] for r in rows)
    lines = [f"*{t(lang, 'diary_title')}*\n"]
    for row in rows:
        lines.append(f"• {row[0]} — {row[1]:.0f} ккал")
    lines.append(f"\n*{t(lang, 'diary_total')}*")
    lines.append(f"🔥 {total_cal:.0f} ккал | 🥩 {total_p:.1f}г | 🧈 {total_f:.1f}г | 🌾 {total_c:.1f}г")
    await message.answer("\n".join(lines), parse_mode="Markdown")


@router.message(F.text.in_(all_btn("btn_settings")))
async def btn_settings(message: Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    await message.answer(t(lang, "choose_language"), reply_markup=language_keyboard())


@router.message(F.text.in_(all_btn("btn_subscription")))
async def btn_subscription(message: Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    has_sub = await check_subscription(user_id)
    if has_sub:
        await message.answer(t(lang, "subscription_active"))
        return
    await message.answer(
        t(lang, "subscription_info"),
        reply_markup=subscription_keyboard(lang),
        parse_mode="Markdown"
    )


@router.message(Command("me"))
async def cmd_me(message: Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    sub = await get_subscription(user_id)
    has_sub = await check_subscription(user_id)
    ref_count = await get_referral_count(user_id)
    bot_username = (await message.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"

    if has_sub:
        expires = datetime.fromisoformat(sub["expires_at"])
        sub_text = t(lang, "me_sub_active").format(date=expires.strftime("%d.%m.%Y"))
    else:
        free_left = max(0, 3 - sub.get("scans_used", 0))
        sub_text = t(lang, "me_sub_none").format(left=free_left)

    text = (
        f"{t(lang, 'me_title')}\n\n"
        f"{t(lang, 'me_id')}: `{user_id}`\n"
        f"💳 {sub_text}\n"
        f"{t(lang, 'me_refs')}: *{ref_count}*\n\n"
        f"{t(lang, 'me_ref_link')}:\n`{ref_link}`"
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("ref"))
async def cmd_ref(message: Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    bot_username = (await message.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    ref_count = await get_referral_count(user_id)
    text = (
        f"{t(lang, 'ref_title')}\n\n"
        f"{t(lang, 'ref_text')}\n\n"
        f"{t(lang, 'ref_link_label')}:\n`{ref_link}`\n\n"
        f"{t(lang, 'ref_invited')}: *{ref_count}*"
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("promo"))
async def cmd_promo(message: Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    args = message.text.split()
    if len(args) < 2:
        await message.answer(t(lang, "promo_enter"), parse_mode="Markdown")
        return
    result = await use_promo(user_id, args[1])
    if result["ok"]:
        await message.answer(
            t(lang, "promo_success").format(days=result["days"]),
            parse_mode="Markdown"
        )
    elif result["reason"] == "not_found":
        await message.answer(t(lang, "promo_not_found"))
    elif result["reason"] == "already_used":
        await message.answer(t(lang, "promo_already_used"))
    elif result["reason"] == "limit_reached":
        await message.answer(t(lang, "promo_limit"))


@router.message(Command("cancel"))
async def cmd_cancel(message: Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    has_sub = await check_subscription(user_id)
    if not has_sub:
        await message.answer(t(lang, "sub_cancel_none"))
        return
    await cancel_subscription(user_id)
    await message.answer(t(lang, "sub_cancel_confirm"))
