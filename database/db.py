import aiosqlite
import os
from datetime import datetime, timedelta

DB_PATH = "foodlens.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'ru',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                referred_by INTEGER DEFAULT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS food_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                dish_name TEXT,
                calories REAL,
                protein REAL,
                fat REAL,
                carbs REAL,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER PRIMARY KEY,
                is_active INTEGER DEFAULT 0,
                expires_at TIMESTAMP,
                scans_used INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS promo_codes (
                code TEXT PRIMARY KEY,
                days INTEGER NOT NULL,
                max_uses INTEGER DEFAULT 1,
                uses_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS promo_uses (
                user_id INTEGER,
                code TEXT,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, code)
            )
        """)
        await db.commit()


# ─── Язык ─────────────────────────────────────────────────────────────────────

async def get_user_language(user_id: int) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT language FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else "ru"


async def set_user_language(user_id: int, language: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, language)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET language = ?
        """, (user_id, language, language))
        await db.commit()


# ─── Дневник питания ──────────────────────────────────────────────────────────

async def save_food_log(user_id: int, dish_name: str, calories: float,
                        protein: float, fat: float, carbs: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO food_log (user_id, dish_name, calories, protein, fat, carbs)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, dish_name, calories, protein, fat, carbs))
        await db.commit()


async def get_today_log(user_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT dish_name, calories, protein, fat, carbs
            FROM food_log
            WHERE user_id = ? AND DATE(logged_at) = DATE('now')
            ORDER BY logged_at DESC
        """, (user_id,)) as cursor:
            return await cursor.fetchall()


# ─── Лимит сканирований за день ───────────────────────────────────────────────

async def get_today_scans(user_id: int) -> int:
    """Возвращает количество сканирований пользователя за сегодня."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT COUNT(*) FROM food_log
            WHERE user_id = ? AND DATE(logged_at) = DATE('now')
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


# ─── Подписка ─────────────────────────────────────────────────────────────────

async def get_subscription(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT is_active, expires_at, scans_used FROM subscriptions WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "is_active": bool(row[0]),
                    "expires_at": row[1],
                    "scans_used": row[2],
                }
            return {"is_active": False, "expires_at": None, "scans_used": 0}


async def check_subscription(user_id: int) -> bool:
    sub = await get_subscription(user_id)
    if not sub["is_active"]:
        return False
    if sub["expires_at"] is None:
        return False
    expires = datetime.fromisoformat(sub["expires_at"])
    return datetime.now() < expires


async def activate_subscription(user_id: int, days: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        async with db.execute(
            "SELECT expires_at FROM subscriptions WHERE user_id = ? AND is_active = 1",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
        if row and row[0]:
            existing = datetime.fromisoformat(row[0])
            base = existing if existing > datetime.now() else datetime.now()
        else:
            base = datetime.now()
        expires_at = base + timedelta(days=days)
        await db.execute("""
            INSERT INTO subscriptions (user_id, is_active, expires_at, scans_used)
            VALUES (?, 1, ?, 0)
            ON CONFLICT(user_id) DO UPDATE SET
                is_active = 1,
                expires_at = ?,
                scans_used = 0
        """, (user_id, expires_at.isoformat(), expires_at.isoformat()))
        await db.commit()


async def cancel_subscription(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE subscriptions SET is_active = 0 WHERE user_id = ?", (user_id,)
        )
        await db.commit()


async def increment_scans(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await db.execute("""
            INSERT INTO subscriptions (user_id, scans_used)
            VALUES (?, 1)
            ON CONFLICT(user_id) DO UPDATE SET scans_used = scans_used + 1
        """, (user_id,))
        await db.commit()


# ─── Реферальная система ──────────────────────────────────────────────────────

async def register_user_with_ref(user_id: int, referred_by: int = None) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            exists = await cursor.fetchone()
        if exists:
            return False
        await db.execute("""
            INSERT INTO users (user_id, referred_by) VALUES (?, ?)
        """, (user_id, referred_by))
        await db.commit()
    if referred_by and referred_by != user_id:
        await activate_subscription(referred_by, 30)
    return True


async def get_referral_count(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM users WHERE referred_by = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


# ─── Промокоды ────────────────────────────────────────────────────────────────

async def create_promo(code: str, days: int, max_uses: int = 1):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO promo_codes (code, days, max_uses, uses_count)
            VALUES (?, ?, ?, 0)
        """, (code.upper(), days, max_uses))
        await db.commit()


async def use_promo(user_id: int, code: str) -> dict:
    code = code.upper().strip()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT days, max_uses, uses_count FROM promo_codes WHERE code = ?", (code,)
        ) as cursor:
            promo = await cursor.fetchone()
        if not promo:
            return {"ok": False, "reason": "not_found"}
        days, max_uses, uses_count = promo
        if uses_count >= max_uses:
            return {"ok": False, "reason": "limit_reached"}
        async with db.execute(
            "SELECT 1 FROM promo_uses WHERE user_id = ? AND code = ?", (user_id, code)
        ) as cursor:
            already = await cursor.fetchone()
        if already:
            return {"ok": False, "reason": "already_used"}
        await db.execute(
            "UPDATE promo_codes SET uses_count = uses_count + 1 WHERE code = ?", (code,)
        )
        await db.execute(
            "INSERT INTO promo_uses (user_id, code) VALUES (?, ?)", (user_id, code)
        )
        await db.commit()
    await activate_subscription(user_id, days)
    return {"ok": True, "days": days}


# ─── Уведомления об истечении ─────────────────────────────────────────────────

async def get_expiring_soon(days_before: int = 3) -> list:
    threshold = datetime.now() + timedelta(days=days_before)
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT user_id, expires_at FROM subscriptions
            WHERE is_active = 1
            AND expires_at BETWEEN DATETIME('now') AND ?
        """, (threshold.isoformat(),)) as cursor:
            return await cursor.fetchall()


# ─── Статистика ───────────────────────────────────────────────────────────────

async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            total_users = (await cursor.fetchone())[0]
        async with db.execute("""
            SELECT COUNT(*) FROM users WHERE DATE(created_at) = DATE('now')
        """) as cursor:
            new_today = (await cursor.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM food_log") as cursor:
            total_scans = (await cursor.fetchone())[0]
        async with db.execute("""
            SELECT COUNT(*) FROM food_log WHERE DATE(logged_at) = DATE('now')
        """) as cursor:
            scans_today = (await cursor.fetchone())[0]
        async with db.execute("""
            SELECT COUNT(*) FROM subscriptions
            WHERE is_active = 1 AND expires_at > DATETIME('now')
        """) as cursor:
            active_subs = (await cursor.fetchone())[0]
    return {
        "total_users": total_users,
        "new_today": new_today,
        "total_scans": total_scans,
        "scans_today": scans_today,
        "active_subs": active_subs,
    }