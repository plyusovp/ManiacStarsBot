# database/db.py
import aiosqlite
import time
import random
from aiogram import Bot

DB_NAME = 'maniac_stars.db'

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA busy_timeout = 5000;")
        
        # --- Миграции (обновление структуры старых таблиц) ---
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in await cursor.fetchall()]
        if 'last_bonus_time' not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN last_bonus_time INTEGER DEFAULT 0")
        if 'duel_wins' not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN duel_wins INTEGER DEFAULT 0")
        if 'duel_losses' not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN duel_losses INTEGER DEFAULT 0")

        cursor = await db.execute("PRAGMA table_info(duel_rounds)")
        columns = [column[1] for column in await cursor.fetchall()]
        if 'special' not in columns:
            await db.execute("ALTER TABLE duel_rounds ADD COLUMN special TEXT")

        # --- Создание всех таблиц (если их нет) ---
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT,
            balance INTEGER NOT NULL DEFAULT 0, invited_by INTEGER,
            registration_date INTEGER NOT NULL, last_bonus_time INTEGER DEFAULT 0,
            duel_wins INTEGER DEFAULT 0, duel_losses INTEGER DEFAULT 0
        )""")
        
        await db.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT, referrer_id INTEGER NOT NULL,
            referred_id INTEGER NOT NULL UNIQUE
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS promocodes (
            code TEXT PRIMARY KEY, reward INTEGER NOT NULL,
            total_uses INTEGER NOT NULL, uses_left INTEGER NOT NULL
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS promo_activations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            code TEXT NOT NULL, UNIQUE(user_id, code)
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL,
            reward INTEGER NOT NULL, rarity TEXT DEFAULT 'Обычная'
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            achievement_id TEXT NOT NULL, completion_date INTEGER NOT NULL,
            UNIQUE(user_id, achievement_id)
        )""")
        
        await db.execute("""
        CREATE TABLE IF NOT EXISTS duel_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stake INTEGER NOT NULL, bank INTEGER NOT NULL, rake_percent INTEGER DEFAULT 7,
            bonus_pool INTEGER DEFAULT 0, state TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
        
        await db.execute("""
        CREATE TABLE IF NOT EXISTS duel_players (
            id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
            role TEXT NOT NULL, hand_json TEXT, wins INTEGER DEFAULT 0, is_winner BOOLEAN,
            FOREIGN KEY (match_id) REFERENCES duel_matches(id)
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS duel_rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER NOT NULL, round_no INTEGER NOT NULL,
            p1_card INTEGER, p2_card INTEGER, result TEXT, special TEXT,
            FOREIGN KEY (match_id) REFERENCES duel_matches(id)
        )""")

        # 🔥 ИСПРАВЛЕНИЕ ЗДЕСЬ: Добавлена колонка state
        await db.execute("""
        CREATE TABLE IF NOT EXISTS timer_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT, stake INTEGER NOT NULL, bank INTEGER NOT NULL,
            winner_id INTEGER, stop_second INTEGER NOT NULL, jackpot_rematch INTEGER DEFAULT 0,
            state TEXT DEFAULT 'active', created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS timer_players (
            id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL, clicked_at REAL, is_winner BOOLEAN,
            FOREIGN KEY (match_id) REFERENCES timer_matches(id)
        )""")
        
        # 🔥 ИСПРАВЛЕНИЕ ЗДЕСЬ: Добавляем миграцию для новой колонки
        cursor = await db.execute("PRAGMA table_info(timer_matches)")
        columns = [column[1] for column in await cursor.fetchall()]
        if 'state' not in columns:
            await db.execute("ALTER TABLE timer_matches ADD COLUMN state TEXT DEFAULT 'active'")

        await db.commit()
    await populate_achievements()

async def populate_achievements():
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
    async with aiosqlite.connect(DB_NAME) as db:
        await db.executemany("INSERT OR IGNORE INTO achievements (id, name, description, reward, rarity) VALUES (?, ?, ?, ?, ?)", achievements_list)
        await db.commit()

async def add_user(user_id, username, full_name, referrer_id=None):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if await cursor.fetchone() is None:
            await db.execute("INSERT INTO users (user_id, username, full_name, invited_by, registration_date) VALUES (?, ?, ?, ?, ?)",
                        (user_id, username, full_name, referrer_id, int(time.time())))
            if referrer_id:
                await db.execute("INSERT OR IGNORE INTO referrals (referrer_id, referred_id) VALUES (?, ?)", (referrer_id, user_id))
                await db.execute("UPDATE users SET balance = balance + 5 WHERE user_id = ?", (referrer_id,))
            await db.commit()
            return True
        return False

async def get_user_balance(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else 0

async def get_referrals_count(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(id) FROM referrals WHERE referrer_id = ?", (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else 0

async def get_full_user_info(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user_data = await cursor.fetchone()
        if not user_data:
            return None
        
        cursor = await db.execute("SELECT referred_id FROM referrals WHERE referrer_id = ?", (user_id,))
        invited_users = await cursor.fetchall()
        
        cursor = await db.execute("SELECT code FROM promo_activations WHERE user_id = ?", (user_id,))
        activated_codes = await cursor.fetchall()

        return {
            "user_data": user_data,
            "invited_users": [i[0] for i in invited_users],
            "activated_codes": [c[0] for c in activated_codes]
        }

async def get_top_referrers(limit=5):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT referrer_id, COUNT(referred_id) as ref_count
            FROM referrals GROUP BY referrer_id ORDER BY ref_count DESC LIMIT ?
        """, (limit,))
        return await cursor.fetchall()

async def activate_promo(user_id, code):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT reward, uses_left FROM promocodes WHERE code = ? AND uses_left > 0", (code,))
        promo = await cursor.fetchone()
        if not promo:
            return "not_found"
        
        cursor = await db.execute("SELECT id FROM promo_activations WHERE user_id = ? AND code = ?", (user_id, code))
        if await cursor.fetchone():
            return "already_activated"
            
        reward = promo[0]
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
        await db.execute("UPDATE promocodes SET uses_left = uses_left - 1 WHERE code = ?", (code,))
        await db.execute("INSERT INTO promo_activations (user_id, code) VALUES (?, ?)", (user_id, code))
        await db.commit()
        return reward

async def get_daily_bonus(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT last_bonus_time FROM users WHERE user_id = ?", (user_id,))
        res = await cursor.fetchone()
        if res is None:
            return {"status": "error"}
            
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

async def get_all_achievements():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id, name FROM achievements ORDER BY rarity, name")
        return await cursor.fetchall()

async def get_user_achievements(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT achievement_id FROM user_achievements WHERE user_id = ?", (user_id,))
        return [row[0] for row in await cursor.fetchall()]

async def get_achievement_details(ach_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT name, description, reward, rarity FROM achievements WHERE id = ?", (ach_id,))
        return await cursor.fetchone()

async def add_promo_code(name, reward, uses):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR REPLACE INTO promocodes (code, reward, total_uses, uses_left) VALUES (?, ?, ?, ?)",
                    (name, reward, uses, uses))
        await db.commit()

async def update_user_balance(user_id, amount):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

async def grant_achievement(user_id, ach_id):
    """
    Присваивает достижение пользователю, если у него его ещё нет.
    Возвращает словарь с результатом и текстом для уведомления.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id FROM user_achievements WHERE user_id = ? AND achievement_id = ?", (user_id, ach_id))
        if await cursor.fetchone():
            return {'granted': False} # Достижение уже было

        cursor = await db.execute("SELECT name, reward FROM achievements WHERE id = ?", (ach_id,))
        details = await cursor.fetchone()
        if not details:
            return {'granted': False}

        ach_name, reward = details
        
        await db.execute("INSERT INTO user_achievements (user_id, achievement_id, completion_date) VALUES (?, ?, ?)",
                    (user_id, ach_id, int(time.time())))
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
        await db.commit()

        notification_text = f"🏆 Новое достижение!\n«{ach_name}» (+{reward} ⭐)"
        return {'granted': True, 'text': notification_text}

async def get_user_by_username(username: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        result = await cursor.fetchone()
        return result[0] if result else None

async def get_all_users():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT user_id FROM users")
        return [row[0] for row in await cursor.fetchall()]

async def add_stars(user_id: int, amount: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

async def add_refs(user_id: int, amount: int):
    async with aiosqlite.connect(DB_NAME) as db:
        for _ in range(amount):
            fake_referred_id = int(time.time() * 1000) + random.randint(1000, 9999)
            await db.execute("INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)", (user_id, fake_referred_id))
        await db.commit()

async def get_active_promos():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT code, reward, uses_left, total_uses FROM promocodes WHERE uses_left > 0")
        return await cursor.fetchall()

async def create_duel(p1_id: int, p2_id: int, stake: int):
    async with aiosqlite.connect(DB_NAME) as db:
        bank = stake * 2
        cursor = await db.execute(
            "INSERT INTO duel_matches (stake, bank, state) VALUES (?, ?, ?)",
            (stake, bank, 'active')
        )
        match_id = cursor.lastrowid
        await db.execute(
            "INSERT INTO duel_players (match_id, user_id, role) VALUES (?, ?, ?), (?, ?, ?)",
            (match_id, p1_id, 'p1', match_id, p2_id, 'p2')
        )
        await db.commit()
        return match_id

async def get_user_duel_stats(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT duel_wins, duel_losses FROM users WHERE user_id = ?", (user_id,))
        stats = await cursor.fetchone()
        if stats:
            return {"wins": stats[0], "losses": stats[1]}
        return {"wins": 0, "losses": 0}

async def update_duel_stats(db, winner_id: int, loser_id: int):
    await db.execute("UPDATE users SET duel_wins = duel_wins + 1 WHERE user_id = ?", (winner_id,))
    await db.execute("UPDATE users SET duel_losses = duel_losses + 1 WHERE user_id = ?", (loser_id,))

async def is_user_in_active_duel(user_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT 1 FROM duel_players dp
            JOIN duel_matches dm ON dp.match_id = dm.id
            WHERE dp.user_id = ? AND dm.state = 'active'
        """, (user_id,))
        return await cursor.fetchone() is not None
        
async def get_duel_details(match_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT p1.user_id, p2.user_id, m.stake 
            FROM duel_matches m
            JOIN duel_players p1 ON m.id = p1.match_id AND p1.role = 'p1'
            JOIN duel_players p2 ON m.id = p2.match_id AND p2.role = 'p2'
            WHERE m.id = ?
        """, (match_id,))
        return await cursor.fetchone()

async def create_duel_round(match_id: int, round_no: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO duel_rounds (match_id, round_no) VALUES (?, ?)", (match_id, round_no))
        await db.commit()

async def save_duel_round(match_id: int, round_no: int, p1_card: int, p2_card: int, result: str, special: str = None):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE duel_rounds SET p1_card = ?, p2_card = ?, result = ?, special = ? WHERE match_id = ? AND round_no = ?",
            (p1_card, p2_card, result, special, match_id, round_no)
        )
        await db.commit()

async def finish_duel(match_id: int, winner_id: int = None, loser_id: int = None):
    async with aiosqlite.connect(DB_NAME) as db:
        if winner_id and loser_id:
            await update_duel_stats(db, winner_id, loser_id)
            await db.execute("UPDATE duel_players SET is_winner = TRUE WHERE match_id = ? AND user_id = ?", (match_id, winner_id))
        
        await db.execute("UPDATE duel_matches SET state = 'finished' WHERE id = ?", (match_id,))
        await db.commit()

async def get_active_duel_id(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT m.id FROM duel_matches m
            JOIN duel_players p ON m.id = p.match_id
            WHERE p.user_id = ? AND m.state = 'active'
        """, (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else None

async def interrupt_duel(match_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE duel_matches SET state = 'interrupted' WHERE id = ?", (match_id,))
        await db.commit()

async def get_all_active_duels():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id FROM duel_matches WHERE state = 'active'")
        return [row[0] for row in await cursor.fetchall()]

async def create_timer_match(p1_id: int, p2_id: int, stake: int, bank: int):
    async with aiosqlite.connect(DB_NAME) as db:
        stop_second = random.randint(0, 9)
        cursor = await db.execute(
            "INSERT INTO timer_matches (stake, bank, stop_second, state) VALUES (?, ?, ?, 'active')",
            (stake, bank, stop_second)
        )
        match_id = cursor.lastrowid
        await db.execute(
            "INSERT INTO timer_players (match_id, user_id) VALUES (?, ?), (?, ?)",
            (match_id, p1_id, match_id, p2_id)
        )
        await db.commit()
        return match_id, stop_second

async def update_timer_player_click(match_id: int, user_id: int, clicked_at: float):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE timer_players SET clicked_at = ? WHERE match_id = ? AND user_id = ?",
            (clicked_at, match_id, user_id)
        )
        await db.commit()

async def finish_timer_match(match_id: int, winner_id: int = None, is_draw: bool = False, new_bank: int = 0):
    async with aiosqlite.connect(DB_NAME) as db:
        if is_draw:
            await db.execute("UPDATE timer_matches SET state = 'draw', bank = ? WHERE id = ?", (new_bank, match_id))
        else:
            await db.execute("UPDATE timer_matches SET state = 'finished', winner_id = ? WHERE id = ?", (winner_id, match_id))
        
        if winner_id:
            await db.execute(
                "UPDATE timer_players SET is_winner = TRUE WHERE match_id = ? AND user_id = ?",
                (match_id, winner_id)
            )
        await db.commit()
        
async def get_timer_match_details(match_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT stake, bank, p1.user_id, p2.user_id FROM timer_matches m JOIN timer_players p1 ON m.id = p1.match_id JOIN timer_players p2 ON m.id = p2.match_id WHERE m.id = ? AND p1.user_id != p2.user_id", (match_id,))
        return await cursor.fetchone()

async def get_timer_players(match_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT user_id FROM timer_players WHERE match_id = ?", (match_id,))
        return [row[0] for row in await cursor.fetchall()]

async def get_active_timer_id(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT m.id FROM timer_matches m
            JOIN timer_players p ON m.id = p.match_id
            WHERE p.user_id = ? AND m.state = 'active'
        """, (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else None

async def interrupt_timer_match(match_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE timer_matches SET state = 'interrupted' WHERE id = ?", (match_id,))
        await db.commit()

async def get_all_active_timers():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id FROM timer_matches WHERE state = 'active'")
        return [row[0] for row in await cursor.fetchall()]
    
    async def get_users_for_notification():
     """Выбирает пользователей, которым можно отправить уведомление о бонусе."""
    async with aiosqlite.connect(DB_NAME) as db:
        # Мы выбираем тех, кто получил бонус больше 23 часов назад,
        # чтобы уведомление пришло с небольшим запасом.
        # time() - 82800 секунд = 23 часа назад
        twenty_three_hours_ago = int(time.time()) - 82800
        cursor = await db.execute(
            "SELECT user_id FROM users WHERE last_bonus_time > 0 AND last_bonus_time < ?",
            (twenty_three_hours_ago,)
        )
        return [row[0] for row in await cursor.fetchall()]
