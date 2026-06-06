from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from locales import t


def main_menu(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "btn_analyze"))],
            [
                KeyboardButton(text=t(lang, "btn_diary")),
                KeyboardButton(text=t(lang, "btn_settings")),
            ],
            [
                KeyboardButton(text=t(lang, "btn_subscription")),
            ],
            [
                KeyboardButton(text=t(lang, "btn_end")),
                KeyboardButton(text=t(lang, "btn_restart")),
            ],
        ],
        resize_keyboard=True,
    )


def result_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=t(lang, "btn_recipe")),
                KeyboardButton(text=t(lang, "btn_save")),
            ],
            [
                KeyboardButton(text=t(lang, "btn_end")),
                KeyboardButton(text=t(lang, "btn_restart")),
            ],
        ],
        resize_keyboard=True,
    )


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
            ],
            [
                InlineKeyboardButton(text="🇦🇲 Հայերեն", callback_data="lang_hy"),
            ],
        ]
    )


def subscription_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐ 1 месяц — 250 Stars",
                    callback_data="sub_30"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⭐ 3 месяца — 600 Stars",
                    callback_data="sub_90"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⭐ 1 год — 2000 Stars",
                    callback_data="sub_365"
                ),
            ],
        ]
    )