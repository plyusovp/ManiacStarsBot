# database/db.py
import aiosqlite
import time
import random
from typing import Union
from aiogram import Bot
from contextlib import asynccontextmanager

DB_NAME = 'maniac_stars.db'

@asynccontextmanager
async def connect():
    """Контекстный менеджер для асинхронного подключения к БД с нужными PRAGMA."""
    db = await aiosqlite.connect(DB_NAME)
    await db.execute("PRAGMA foreign_keys = ON;")
    await db.execute("PRAGMA journal_mode=WAL;")
    await db.execute("PRAGMA busy_timeout = 5000;")
    try:
        yield db
    finally:
        await db.close()

async def init_db():
    async with connect() as db:
        # Создание таблиц
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            balance INTEGER NOT NULL DEFAULT 0 CHECK(balance >= 0),
            invited_by INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
            registration_date INTEGER NOT NULL,
            last_bonus_time INTEGER DEFAULT 0,
            duel_wins INTEGER DEFAULT 0,
            duel_losses INTEGER DEFAULT 0,
            last_seen INTEGER DEFAULT 0
        )""")
        
        await db.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER NOT NULL,
            referred_id INTEGER NOT NULL UNIQUE,
            FOREIGN KEY(referrer_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY(referred_id) REFERENCES users(user_id) ON DELETE CASCADE
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS promocodes (
            code TEXT PRIMARY KEY,
            reward INTEGER NOT NULL CHECK(reward > 0),
            total_uses INTEGER NOT NULL CHECK(total_uses >= 0),
            uses_left INTEGER NOT NULL CHECK(uses_left >= 0 AND uses_left <= total_uses)
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS promo_activations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            UNIQUE(user_id, code),
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY(code) REFERENCES promocodes(code) ON DELETE RESTRICT
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            reward INTEGER NOT NULL CHECK(reward > 0),
            rarity TEXT DEFAULT 'Обычная'
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_id TEXT NOT NULL,
            completion_date INTEGER NOT NULL,
            UNIQUE(user_id, achievement_id),
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY(achievement_id) REFERENCES achievements(id) ON DELETE CASCADE
        )""")
        
        await db.execute("""
        CREATE TABLE IF NOT EXISTS duel_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stake INTEGER NOT NULL CHECK(stake > 0),
            bank INTEGER NOT NULL CHECK(bank >= 0),
            rake_percent INTEGER DEFAULT 7,
            bonus_pool INTEGER DEFAULT 0,
            state TEXT NOT NULL CHECK(state IN ('active','finished','draw','interrupted')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
        
        await db.execute("""
        CREATE TABLE IF NOT EXISTS duel_players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('p1', 'p2')),
            hand_json TEXT,
            wins INTEGER DEFAULT 0,
            is_winner INTEGER CHECK(is_winner IN (0,1)),
            FOREIGN KEY(match_id) REFERENCES duel_matches(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS duel_rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            round_no INTEGER NOT NULL,
            p1_card INTEGER,
            p2_card INTEGER,
            result TEXT,
            special TEXT,
            FOREIGN KEY (match_id) REFERENCES duel_matches(id) ON DELETE CASCADE
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS timer_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stake INTEGER NOT NULL CHECK(stake > 0),
            bank INTEGER NOT NULL CHECK(bank >= 0),
            winner_id INTEGER,
            stop_second INTEGER NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('active','finished','draw','interrupted')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(winner_id) REFERENCES users(user_id)
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS timer_players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT CHECK(role IN ('p1', 'p2')),
            clicked_at REAL CHECK(clicked_at IS NULL OR clicked_at >= 0),
            is_winner INTEGER CHECK(is_winner IN (0,1)),
            FOREIGN KEY(match_id) REFERENCES timer_matches(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )""")

        # Миграции
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in await cursor.fetchall()]
        if 'last_seen' not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN last_seen INTEGER DEFAULT 0")

        cursor = await db.execute("PRAGMA table_info(timer_players)")
        columns = [column[1] for column in await cursor.fetchall()]
        if 'role' not in columns:
            await db.execute("ALTER TABLE timer_players ADD COLUMN role TEXT;")
        
        # Очистка дубликатов в раундах перед созданием уникального индекса
        await db.execute("""
        DELETE FROM duel_rounds
        WHERE rowid NOT IN (
          SELECT MIN(rowid)
          FROM duel_rounds
          GROUP BY match_id, round_no
        )
        """)
        
        # Индексы
        await db.execute("CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);")
        await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_duel_players_match_user ON duel_players(match_id, user_id);")
        await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_duel_players_match_role ON duel_players(match_id, role);")
        await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_timer_players_match_user ON timer_players(match_id, user_id);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_promo_activations_user ON promo_activations(user_id);")
        await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_duel_rounds_match_round ON duel_rounds(match_id, round_no);")

        await db.commit()
    await populate_achievements()

async def populate_achievements():
    async with connect() as db:
        achievements_list = [
            ('first_steps', 'Первые шаги', 'Просто запустить бота.', 1, 'Обычная'),
            ('first_referral', 'Первопроходец', 'Пригласить 1 друга.', 5, 'Обычная'),
            ('bonus_hunter', 'Охотник за бонусами', 'Собрать первый ежедневный бонус.', 3, 'Обычная'),
            ('curious', 'Любопытный', 'Зайти в раздел "Профиль".', 1, 'Обычная'),
            ('friendly', 'Дружелюбный', 'Пригласить 5 друзей.', 10, 'Обычная'),
            ('code_breaker', 'Взломщик кодов', 'Активировать 1 промокод.', 5, 'Обычная'),
            ('social', 'Душа компании', 'Пригласить 15 друзей.', 20, 'Редкая'),
            ('regular', 'Завсегдатай', 'Заходить в бота 3 дня подряд.', 10, 'Редкая'),
            ('magnate', 'Магнат', 'Накопить на балансе 100 звёзд.', 15, 'Редкая'),
            ('promo_master', 'Магистр промокодов', 'Активировать 3 разных промокода.', 20, 'Редкая'),
            ('legend', 'Легенда', 'Пригласить 50 друзей.', 50, 'Эпическая'),
            ('king', 'Король рефералов', 'Удержать 1 место в топе 3 дня.', 100, 'Эпическая'),
            ('meta', 'Что ты такое?', 'Попытаться использовать команду /info на самого себя.', 5, 'Мифическая')
        ]
        await db.executemany("INSERT OR IGNORE INTO achievements (id, name, description, reward, rarity) VALUES (?, ?, ?, ?, ?)", achievements_list)
        await db.commit()

async def add_user(user_id, username, full_name, referrer_id=None):
    async with connect() as db:
        cursor = await db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if await cursor.fetchone() is None:
            await db.execute("INSERT INTO users (user_id, username, full_name, invited_by, registration_date, last_seen) VALUES (?, ?, ?, ?, ?, ?)",
                        (user_id, username, full_name, referrer_id, int(time.time()), int(time.time())))
            if referrer_id:
                await db.execute("INSERT OR IGNORE INTO referrals (referrer_id, referred_id) VALUES (?, ?)", (referrer_id, user_id))
                await db.execute("UPDATE users SET balance = balance + 5 WHERE user_id = ?", (referrer_id,))
            await db.commit()
            return True
        return False

async def update_user_last_seen(user_id: int):
    async with connect() as db:
        await db.execute("UPDATE users SET last_seen = ? WHERE user_id = ?", (int(time.time()), user_id))
        await db.commit()

async def get_user_balance(user_id):
    async with connect() as db:
        cursor = await db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else 0

async def get_referrals_count(user_id):
    async with connect() as db:
        cursor = await db.execute("SELECT COUNT(id) FROM referrals WHERE referrer_id = ?", (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else 0

async def get_full_user_info(user_id):
    async with connect() as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user_data = await cursor.fetchone()
        if not user_data: return None
        cursor = await db.execute("SELECT referred_id FROM referrals WHERE referrer_id = ?", (user_id,))
        invited_users = await cursor.fetchall()
        cursor = await db.execute("SELECT code FROM promo_activations WHERE user_id = ?", (user_id,))
        activated_codes = await cursor.fetchall()
        return {
            "user_data": user_data, "invited_users": [i[0] for i in invited_users],
            "activated_codes": [c[0] for c in activated_codes]
        }

async def get_top_referrers(limit=5):
    async with connect() as db:
        cursor = await db.execute("""
            SELECT referrer_id, COUNT(referred_id) as ref_count
            FROM referrals GROUP BY referrer_id ORDER BY ref_count DESC LIMIT ?
        """, (limit,))
        return await cursor.fetchall()

async def activate_promo(user_id, code):
    async with connect() as db:
        try:
            await db.execute("BEGIN IMMEDIATE;")
            cursor = await db.execute("SELECT reward FROM promocodes WHERE code=? AND uses_left > 0", (code,))
            row = await cursor.fetchone()
            if not row:
                await db.execute("ROLLBACK;")
                return "not_found"
            reward = row[0]
            
            await db.execute("INSERT INTO promo_activations(user_id, code) VALUES(?, ?)", (user_id, code))
            
            cursor = await db.execute("UPDATE promocodes SET uses_left = uses_left - 1 WHERE code=? AND uses_left > 0", (code,))
            if cursor.rowcount == 0:
                await db.execute("ROLLBACK;")
                return "not_found"
            
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (reward, user_id))
            await db.execute("COMMIT;")
            return reward
        except aiosqlite.IntegrityError:
            await db.execute("ROLLBACK;")
            return "already_activated"
        except Exception as e:
            await db.execute("ROLLBACK;")
            print(f"Error in activate_promo transaction: {e}")
            return "error"

async def get_daily_bonus(user_id):
    async with connect() as db:
        cursor = await db.execute("SELECT last_bonus_time FROM users WHERE user_id = ?", (user_id,))
        res = await cursor.fetchone()
        if res is None: return {"status": "error"}
        last_bonus_time = res[0]
        current_time = int(time.time())
        time_passed = current_time - (last_bonus_time or 0)
        if time_passed > 86400:
            reward = random.randint(1, 5)
            await db.execute("UPDATE users SET balance = balance + ?, last_bonus_time = ? WHERE user_id = ?", (reward, current_time, user_id))
            await db.commit()
            return {"status": "success", "reward": reward}
        else:
            return {"status": "wait", "seconds_left": 86400 - time_passed}

async def get_users_for_notification():
    async with connect() as db:
        twenty_three_hours_ago = int(time.time()) - 82800
        cursor = await db.execute(
            "SELECT user_id FROM users WHERE last_bonus_time > 0 AND last_bonus_time < ?",
            (twenty_three_hours_ago,)
        )
        return [row[0] for row in await cursor.fetchall()]

async def get_all_achievements():
    async with connect() as db:
        cursor = await db.execute("SELECT id, name FROM achievements ORDER BY rarity, name")
        return await cursor.fetchall()

async def get_user_achievements(user_id):
    async with connect() as db:
        cursor = await db.execute("SELECT achievement_id FROM user_achievements WHERE user_id = ?", (user_id,))
        return [row[0] for row in await cursor.fetchall()]

async def get_achievement_details(ach_id):
    async with connect() as db:
        cursor = await db.execute("SELECT name, description, reward, rarity FROM achievements WHERE id = ?", (ach_id,))
        return await cursor.fetchone()

async def add_promo_code(name, reward, uses):
    async with connect() as db:
        await db.execute("INSERT OR REPLACE INTO promocodes (code, reward, total_uses, uses_left) VALUES (?, ?, ?, ?)",
                    (name, reward, uses, uses))
        await db.commit()

async def update_user_balance(user_id, amount) -> bool:
    async with connect() as db:
        if amount < 0:
            cursor = await db.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id = ? AND balance >= ?",
                (amount, user_id, -amount)
            )
            if cursor.rowcount == 0: return False
        else:
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()
        return True

async def grant_achievement(user_id, ach_id, bot: Bot) -> bool:
    async with connect() as db:
        cursor = await db.execute("SELECT id FROM user_achievements WHERE user_id = ? AND achievement_id = ?", (user_id, ach_id))
        if await cursor.fetchone(): return False
        cursor = await db.execute("SELECT name, reward FROM achievements WHERE id = ?", (ach_id,))
        details = await cursor.fetchone()
        if not details: return False
        ach_name, reward = details
        await db.execute("INSERT INTO user_achievements (user_id, achievement_id, completion_date) VALUES (?, ?, ?)",
                    (user_id, ach_id, int(time.time())))
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
        await db.commit()
    try:
        await bot.send_message(user_id, f"🏆 <b>Новое достижение!</b>\nВы открыли: «{ach_name}» (+{reward} ⭐)")
    except Exception as e:
        print(f"Не удалось уведомить пользователя {user_id} о достижении: {e}")
    return True

async def get_user_by_username(username: str) -> Union[int, None]:
    async with connect() as db:
        cursor = await db.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        result = await cursor.fetchone()
        return result[0] if result else None

async def get_all_users():
    async with connect() as db:
        cursor = await db.execute("SELECT user_id FROM users")
        return [row[0] for row in await cursor.fetchall()]

async def add_stars(user_id: int, amount: int):
    return await update_user_balance(user_id, amount)

# async def add_refs(user_id: int, amount: int):
#     """Эта функция небезопасна из-за FK, лучше не использовать."""
#     pass

async def get_active_promos():
    async with connect() as db:
        cursor = await db.execute("SELECT code, reward, uses_left, total_uses FROM promocodes WHERE uses_left > 0")
        return await cursor.fetchall()

# --- Функции для Дуэлей ---
async def create_duel_atomic(p1_id: int, p2_id: int, stake: int):
    async with connect() as db:
        try:
            await db.execute("BEGIN IMMEDIATE;")
            for uid in (p1_id, p2_id):
                cur = await db.execute(
                    "UPDATE users SET balance = balance - ? WHERE user_id = ? AND balance >= ?",
                    (stake, uid, stake)
                )
                if cur.rowcount == 0:
                    await db.execute("ROLLBACK;")
                    return None
            bank = stake * 2
            cur = await db.execute(
                "INSERT INTO duel_matches (stake, bank, state) VALUES (?, ?, 'active')",
                (stake, bank)
            )
            match_id = cur.lastrowid
            await db.execute(
                "INSERT INTO duel_players (match_id, user_id, role) VALUES (?, ?, 'p1'), (?, ?, 'p2')",
                (match_id, p1_id, match_id, p2_id)
            )
            await db.execute("COMMIT;")
            return match_id
        except Exception as e:
            await db.execute("ROLLBACK;")
            print(f'create_duel TX error: {e}')
            return None

async def get_user_duel_stats(user_id: int):
    async with connect() as db:
        cursor = await db.execute("SELECT duel_wins, duel_losses FROM users WHERE user_id = ?", (user_id,))
        stats = await cursor.fetchone()
        return {"wins": stats[0], "losses": stats[1]} if stats else {"wins": 0, "losses": 0}

async def update_duel_stats(db, winner_id: int, loser_id: int):
    await db.execute("UPDATE users SET duel_wins = duel_wins + 1 WHERE user_id = ?", (winner_id,))
    await db.execute("UPDATE users SET duel_losses = duel_losses + 1 WHERE user_id = ?", (loser_id,))

async def is_user_in_active_duel(user_id: int) -> bool:
    async with connect() as db:
        cursor = await db.execute("""
            SELECT 1 FROM duel_players dp
            JOIN duel_matches dm ON dp.match_id = dm.id
            WHERE dp.user_id = ? AND dm.state = 'active'
        """, (user_id,))
        return await cursor.fetchone() is not None
        
async def get_duel_players(match_id: int):
    async with connect() as db:
        cursor = await db.execute("SELECT user_id, role FROM duel_players WHERE match_id = ?", (match_id,))
        return await cursor.fetchall()

async def create_duel_round(match_id: int, round_no: int):
    async with connect() as db:
        await db.execute("INSERT OR IGNORE INTO duel_rounds (match_id, round_no) VALUES (?, ?)", (match_id, round_no))
        await db.commit()

async def save_duel_round(match_id: int, round_no: int, p1_card: int, p2_card: int, result: str, special: str = None):
    async with connect() as db:
        await db.execute(
            "UPDATE duel_rounds SET p1_card = ?, p2_card = ?, result = ?, special = ? WHERE match_id = ? AND round_no = ?",
            (p1_card, p2_card, result, special, match_id, round_no)
        )
        await db.commit()

async def finish_duel_atomic(match_id: int, winner_id: int, loser_id: int, prize: int):
    async with connect() as db:
        try:
            await db.execute("BEGIN IMMEDIATE;")
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (prize, winner_id))
            await update_duel_stats(db, winner_id, loser_id)
            await db.execute("UPDATE duel_players SET is_winner = 1 WHERE match_id = ? AND user_id = ?", (match_id, winner_id))
            await db.execute("UPDATE duel_matches SET state = 'finished' WHERE id = ?", (match_id,))
            await db.execute("COMMIT;")
        except Exception as e:
            await db.execute("ROLLBACK;")
            print(f"Ошибка в транзакции finish_duel: {e}")

async def get_active_duel_id(user_id: int):
    async with connect() as db:
        cursor = await db.execute("""
            SELECT m.id FROM duel_matches m
            JOIN duel_players p ON m.id = p.match_id
            WHERE p.user_id = ? AND m.state = 'active'
        """, (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else None

async def interrupt_duel(match_id: int):
    async with connect() as db:
        await db.execute("UPDATE duel_matches SET state = 'interrupted' WHERE id = ?", (match_id,))
        await db.commit()

async def get_all_active_duels():
    async with connect() as db:
        cursor = await db.execute("SELECT id FROM duel_matches WHERE state = 'active'")
        return [row[0] for row in await cursor.fetchall()]

# --- Функции для Таймера ---
async def create_timer_match(p1_id: int, p2_id: int, stake: int):
    async with connect() as db:
        try:
            await db.execute("BEGIN IMMEDIATE;")
            for uid in (p1_id, p2_id):
                cur = await db.execute(
                    "UPDATE users SET balance = balance - ? WHERE user_id = ? AND balance >= ?",
                    (stake, uid, stake)
                )
                if cur.rowcount == 0:
                    await db.execute("ROLLBACK;")
                    return None
            bank = stake * 2
            stop_second = random.randint(0, 9)
            cur = await db.execute(
                "INSERT INTO timer_matches (stake, bank, stop_second, state) VALUES (?, ?, ?, 'active')",
                (stake, bank, stop_second)
            )
            match_id = cur.lastrowid
            await db.execute(
                "INSERT INTO timer_players (match_id, user_id, role) VALUES (?, ?, 'p1'), (?, ?, 'p2')",
                (match_id, p1_id, match_id, p2_id)
            )
            await db.execute("COMMIT;")
            return match_id, stop_second
        except Exception as e:
            await db.execute("ROLLBACK;")
            print(f'create_timer_match TX error: {e}')
            return None

async def update_timer_player_click(match_id: int, user_id: int, clicked_at: float):
    async with connect() as db:
        await db.execute(
            "UPDATE timer_players SET clicked_at = ? WHERE user_id = ? AND match_id = ?",
            (clicked_at, user_id, match_id)
        )
        await db.commit()

async def finish_timer_match_atomic(match_id: int, winner_id: int = None, prize: int = 0, is_draw: bool = False, new_bank: int = 0):
    async with connect() as db:
        try:
            await db.execute("BEGIN IMMEDIATE;")
            if is_draw:
                await db.execute("UPDATE timer_matches SET state = 'draw', bank = ? WHERE id = ?", (new_bank, match_id))
            else:
                await db.execute("UPDATE timer_matches SET state = 'finished', winner_id = ? WHERE id = ?", (winner_id, match_id))
                if winner_id and prize > 0:
                    await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (prize, winner_id))
                if winner_id:
                    await db.execute("UPDATE timer_players SET is_winner = 1 WHERE match_id = ? AND user_id = ?", (match_id, winner_id))
            await db.execute("COMMIT;")
        except Exception as e:
            await db.execute("ROLLBACK;")
            print(f"Ошибка в транзакции finish_timer_match: {e}")
        
async def get_timer_match_details(match_id: int):
    async with connect() as db:
        cursor = await db.execute("""
            SELECT m.stake, m.bank, p1.user_id, p2.user_id
            FROM timer_matches m
            JOIN timer_players p1 ON m.id = p1.match_id AND p1.role = 'p1'
            JOIN timer_players p2 ON m.id = p2.match_id AND p2.role = 'p2'
            WHERE m.id = ?
        """, (match_id,))
        return await cursor.fetchone()

async def get_timer_players(match_id: int):
    async with connect() as db:
        cursor = await db.execute("SELECT user_id FROM timer_players WHERE match_id = ?", (match_id,))
        return [row[0] for row in await cursor.fetchall()]

async def get_active_timer_id(user_id: int):
    async with connect() as db:
        cursor = await db.execute("""
            SELECT m.id FROM timer_matches m
            JOIN timer_players p ON m.id = p.match_id
            WHERE p.user_id = ? AND m.state = 'active'
        """, (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else None

async def interrupt_timer_match(match_id: int):
    async with connect() as db:
        await db.execute("UPDATE timer_matches SET state = 'interrupted' WHERE id = ?", (match_id,))
        await db.commit()

async def get_all_active_timers():
    async with connect() as db:
        cursor = await db.execute("SELECT id FROM timer_matches WHERE state = 'active'")
        return [row[0] for row in await cursor.fetchall()]