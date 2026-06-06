import aiosqlite

DB_PATH = "foodlens.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'ru',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        await db.commit()


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


# ── Подписка ──────────────────────────────────────────

async def get_subscription(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT is_active, expires_at, scans_used
            FROM subscriptions WHERE user_id = ?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return {"is_active": False, "expires_at": None, "scans_used": 0}
            return {"is_active": bool(row[0]), "expires_at": row[1], "scans_used": row[2]}


async def activate_subscription(user_id: int, days: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO subscriptions (user_id, is_active, expires_at, scans_used)
            VALUES (?, 1, datetime('now', ?), 0)
            ON CONFLICT(user_id) DO UPDATE SET
                is_active = 1,
                expires_at = datetime('now', ?),
                scans_used = 0
        """, (user_id, f"+{days} days", f"+{days} days"))
        await db.commit()


async def increment_scans(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO subscriptions (user_id, scans_used)
            VALUES (?, 1)
            ON CONFLICT(user_id) DO UPDATE SET scans_used = scans_used + 1
        """, (user_id,))
        await db.commit()


async def check_subscription(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT is_active, expires_at, scans_used
            FROM subscriptions WHERE user_id = ?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return False
            is_active, expires_at, scans_used = row
            if not is_active:
                return False
            async with db.execute("""
                SELECT datetime('now') > ?
            """, (expires_at,)) as cur2:
                expired = await cur2.fetchone()
                if expired and expired[0]:
                    await db.execute("""
                        UPDATE subscriptions SET is_active = 0 WHERE user_id = ?
                    """, (user_id,))
                    await db.commit()
                    return False
            return True


# ── Статистика для админа ─────────────────────────────

async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            total_users = (await cursor.fetchone())[0]

        async with db.execute("""
            SELECT COUNT(*) FROM users
            WHERE DATE(created_at) = DATE('now')
        """) as cursor:
            new_today = (await cursor.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM food_log") as cursor:
            total_scans = (await cursor.fetchone())[0]

        async with db.execute("""
            SELECT COUNT(*) FROM food_log
            WHERE DATE(logged_at) = DATE('now')
        """) as cursor:
            scans_today = (await cursor.fetchone())[0]

        async with db.execute("""
            SELECT COUNT(*) FROM subscriptions WHERE is_active = 1
        """) as cursor:
            active_subs = (await cursor.fetchone())[0]

        return {
            "total_users": total_users,
            "new_today": new_today,
            "total_scans": total_scans,
            "scans_today": scans_today,
            "active_subs": active_subs,
        }