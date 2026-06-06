import os
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery,
    LabeledPrice, PreCheckoutQuery
)

from database.db import get_user_language, activate_subscription
from locales import t

router = Router()

# Цены в Stars (1$ ≈ 50 Stars примерно, Telegram сам конвертирует)
PLANS = {
    "sub_30": {"days": 30, "stars": 250, "label": "1 месяц — 250 ⭐"},
    "sub_90": {"days": 90, "stars": 600, "label": "3 месяца — 600 ⭐"},
    "sub_365": {"days": 365, "stars": 2000, "label": "1 год — 2000 ⭐"},
}


@router.callback_query(F.data.startswith("sub_"))
async def handle_subscription_choice(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    plan_key = callback.data
    plan = PLANS.get(plan_key)

    if not plan:
        await callback.answer()
        return

    await callback.message.answer_invoice(
        title="FoodLens Premium",
        description=f"Подписка на FoodLens — {plan['label']}",
        payload=f"{plan_key}:{user_id}",
        currency="XTR",  # XTR = Telegram Stars
        prices=[LabeledPrice(label=plan["label"], amount=plan["stars"])],
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    # Всегда подтверждаем
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    payload = message.successful_payment.invoice_payload
    # payload = "sub_30:123456789"
    plan_key = payload.split(":")[0]
    plan = PLANS.get(plan_key)

    if plan:
        await activate_subscription(user_id, plan["days"])
        await message.answer(
            f"✅ Оплата прошла успешно!\n"
            f"Подписка активирована на *{plan['days']} дней*. 🎉\n\n"
            f"Используй /me чтобы проверить срок.",
            parse_mode="Markdown"
        )