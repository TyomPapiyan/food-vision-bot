from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from database.db import set_user_language, get_user_language, register_user_with_ref
from keyboards.main_kb import language_keyboard, main_menu
from locales import t

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    args = message.text.split()

    referred_by = None
    if len(args) > 1:
        try:
            referred_by = int(args[1])
        except ValueError:
            pass

    is_new = await register_user_with_ref(user_id, referred_by)

    # Уведомляем реферера если пришёл новый пользователь
    if is_new and referred_by and referred_by != user_id:
        try:
            await message.bot.send_message(
                referred_by,
                "🎉 По вашей реферальной ссылке зарегистрировался новый пользователь!\n"
                "✅ Вам начислен *1 месяц* подписки!",
                parse_mode="Markdown"
            )
        except Exception:
            pass

    await message.answer(
        t("ru", "welcome"),
        reply_markup=language_keyboard()
    )


@router.callback_query(F.data.startswith("lang_"))
async def set_language(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    user_id = callback.from_user.id
    await set_user_language(user_id, lang)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        t(lang, "language_set"),
        reply_markup=main_menu(lang)
    )
    await callback.answer()