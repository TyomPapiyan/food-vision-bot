import os
import aiosqlite
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database.db import get_stats, activate_subscription, create_promo

router = Router()

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    stats = await get_stats()
    text = (
        f"📊 *Статистика FoodLens Bot*\n\n"
        f"👥 Всего пользователей: *{stats['total_users']}*\n"
        f"🆕 Новых сегодня: *{stats['new_today']}*\n\n"
        f"📸 Всего сканирований: *{stats['total_scans']}*\n"
        f"📸 Сканирований сегодня: *{stats['scans_today']}*\n\n"
        f"💳 Активных подписок: *{stats['active_subs']}*"
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("give"))
async def cmd_give(message: Message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) != 3:
        await message.answer("Использование: /give <user_id> <дней>\nПример: /give 123456789 30")
        return
    try:
        user_id = int(args[1])
        days = int(args[2])
    except ValueError:
        await message.answer("Неверный формат. Пример: /give 123456789 30")
        return
    await activate_subscription(user_id, days)
    await message.answer(f"✅ Подписка на {days} дней выдана пользователю {user_id}")


@router.message(Command("createpromo"))
async def cmd_createpromo(message: Message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 3:
        await message.answer(
            "Использование: /createpromo <код> <дней> [макс_использований]\n"
            "Пример: /createpromo SUMMER30 30 100"
        )
        return
    try:
        code = args[1]
        days = int(args[2])
        max_uses = int(args[3]) if len(args) > 3 else 1
    except ValueError:
        await message.answer("Неверный формат.")
        return
    await create_promo(code, days, max_uses)
    await message.answer(
        f"✅ Промокод создан:\n"
        f"Код: `{code.upper()}`\n"
        f"Дней: {days}\n"
        f"Макс. использований: {max_uses}",
        parse_mode="Markdown"
    )


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /broadcast <текст>")
        return
    text = args[1]
    async with aiosqlite.connect("foodlens.db") as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            users = await cursor.fetchall()
    sent = 0
    failed = 0
    for (user_id,) in users:
        try:
            await message.bot.send_message(user_id, text)
            sent += 1
        except Exception:
            failed += 1
    await message.answer(
        f"📢 Рассылка завершена!\n"
        f"✅ Отправлено: {sent}\n"
        f"❌ Не доставлено: {failed}"
    )