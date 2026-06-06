from locales.ru import texts as ru_texts
from locales.en import texts as en_texts
from locales.hy import texts as hy_texts

LOCALES = {
    "ru": ru_texts,
    "en": en_texts,
    "hy": hy_texts,
}


def t(lang: str, key: str) -> str:
    return LOCALES.get(lang, ru_texts).get(key, key)