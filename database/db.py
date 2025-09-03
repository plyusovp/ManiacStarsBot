# database/db.py
import datetime
import logging
import random
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Union

import aiosqlite
from aiogram import Bot

from config import settings
from economy import EARN_RULES

DB_NAME = "maniac_stars.db"
logger = logging.getLogger(__name__)


@asynccontextmanager
async def connect():
    """Контекстный менеджер для асинхронного подключения к БД с нужными PRAGMA."""
    db = await aiosqlite.connect(DB_NAME)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL;")
    await db.execute("PRAGMA foreign_keys = ON;")
    await db.execute("PRAGMA busy_timeout = 5000;")
    try:
        yield db
    finally:
        await db.close()


async def init_db():
    """Инициализирует и мигрирует схему базы данных."""
    async with connect() as db:
        # --- Таблица идемпотентности ---
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS idempotency (
                key TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_idempotency_created_at ON idempotency (created_at);"
        )
        # --- Таблица пользователей ---
        await db.execute(
            """
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
            last_seen INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            risk_level INTEGER NOT NULL DEFAULT 0,
            last_big_earn DATETIME
        )"""
        )
        # --- Таблицы для лимитов ---
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS earn_counters_daily (
            user_id INTEGER NOT NULL,
            source TEXT NOT NULL,
            day DATE NOT NULL,
            amount INTEGER NOT NULL DEFAULT 0,
            ops INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, source, day),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )"""
        )
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS earn_counters_window (
            user_id INTEGER NOT NULL,
            source TEXT NOT NULL,
            window_start DATETIME NOT NULL,
            window_size TEXT NOT NULL, -- '1m'/'1h'
            ops INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, source, window_start, window_size),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )"""
        )
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS ledger_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            amount INTEGER NOT NULL,
            currency TEXT NOT NULL DEFAULT 'STAR',
            reason TEXT NOT NULL,
            ref_id TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )"""
        )
        # --- Таблицы для системы подарков ---
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            item_id TEXT NOT NULL,
            stars_cost INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            risk_flags TEXT, -- JSON array of strings
            notes TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )"""
        )
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS reward_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reward_id INTEGER NOT NULL REFERENCES rewards(id) ON DELETE CASCADE,
            admin_id INTEGER NOT NULL,
            action TEXT NOT NULL, -- 'approve', 'reject', 'fulfill'
            notes TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )"""
        )
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS reward_counters_daily (
            user_id INTEGER NOT NULL,
            day DATE NOT NULL,
            amount INTEGER NOT NULL DEFAULT 0,
            ops INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, day),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )"""
        )
        # --- Остальные таблицы ---
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER NOT NULL,
            referred_id INTEGER NOT NULL UNIQUE,
            FOREIGN KEY(referrer_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY(referred_id) REFERENCES users(user_id) ON DELETE CASCADE
        )"""
        )
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS promocodes (
            code TEXT PRIMARY KEY,
            reward INTEGER NOT NULL CHECK(reward > 0),
            total_uses INTEGER NOT NULL CHECK(total_uses >= 0),
            uses_left INTEGER NOT NULL CHECK(uses_left >= 0 AND uses_left <= total_uses)
        )"""
        )
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS promo_activations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            UNIQUE(user_id, code),
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY(code) REFERENCES promocodes(code) ON DELETE RESTRICT
        )"""
        )
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS achievements (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            reward INTEGER NOT NULL CHECK(reward > 0),
            rarity TEXT DEFAULT 'Обычная'
        )"""
        )
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_id TEXT NOT NULL,
            completion_date INTEGER NOT NULL,
            UNIQUE(user_id, achievement_id),
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY(achievement_id) REFERENCES achievements(id) ON DELETE CASCADE
        )"""
        )
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS duel_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stake INTEGER NOT NULL CHECK(stake > 0),
            bank INTEGER NOT NULL CHECK(bank >= 0),
            rake_percent INTEGER DEFAULT 7,
            bonus_pool INTEGER DEFAULT 0,
            state TEXT NOT NULL CHECK(state IN ('active','finished','draw','interrupted')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""
        )
        await db.execute(
            """
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
        )"""
        )
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS duel_rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            round_no INTEGER NOT NULL,
            p1_card INTEGER,
            p2_card INTEGER,
            result TEXT,
            special TEXT,
            FOREIGN KEY (match_id) REFERENCES duel_matches(id) ON DELETE CASCADE
        )"""
        )
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS timer_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stake INTEGER NOT NULL CHECK(stake > 0),
            bank INTEGER NOT NULL CHECK(bank >= 0),
            winner_id INTEGER,
            stop_second INTEGER NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('active','finished','draw','interrupted')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(winner_id) REFERENCES users(user_id)
        )"""
        )
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS timer_players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT CHECK(role IN ('p1', 'p2')),
            clicked_at REAL CHECK(clicked_at IS NULL OR clicked_at >= 0),
            is_winner INTEGER CHECK(is_winner IN (0,1)),
            FOREIGN KEY(match_id) REFERENCES timer_matches(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )"""
        )

        # --- Миграции и Индексы ---
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in await cursor.fetchall()]
        if "risk_level" not in columns:
            await db.execute(
                "ALTER TABLE users ADD COLUMN risk_level INTEGER NOT NULL DEFAULT 0"
            )
        if "last_big_earn" not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN last_big_earn DATETIME")
        if "created_at" not in columns:
            await db.execute(
                "ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
            )

        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_rewards_user ON rewards (user_id, created_at DESC);"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_rewards_status ON rewards (status, created_at DESC);"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users (created_at);"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_ledger_user ON ledger_entries (user_id, created_at DESC);"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_idem_user ON idempotency (user_id, created_at DESC);"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);"
        )
        await db.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_duel_players_match_user ON duel_players(match_id, user_id);"
        )
        await db.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_duel_players_match_role ON duel_players(match_id, role);"
        )
        await db.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_timer_players_match_user ON timer_players(match_id, user_id);"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_promo_activations_user ON promo_activations(user_id);"
        )
        await db.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_duel_rounds_match_round ON duel_rounds(match_id, round_no);"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_duel_players_user ON duel_players(user_id);"
        )

        await db.commit()
    await populate_achievements()


async def check_idempotency_key(
    db: aiosqlite.Connection, key: str, user_id: int
) -> bool:
    """
    Проверяет ключ идемпотентности.
    Возвращает True, если ключ новый, False - если дубликат.
    """
    try:
        await db.execute(
            "INSERT INTO idempotency (key, user_id) VALUES (?, ?)", (key, user_id)
        )
        return True
    except aiosqlite.IntegrityError:
        # Конфликт первичного ключа означает, что такой запрос уже был
        return False


async def cleanup_old_idempotency_keys(days: int = 7):
    """Удаляет старые ключи идемпотентности."""
    async with connect() as db:
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        cursor = await db.execute(
            "DELETE FROM idempotency WHERE created_at < ?", (cutoff_date,)
        )
        await db.commit()
        logger.info(f"Удалено {cursor.rowcount} старых ключей идемпотентности.")


async def _change_balance(
    db: aiosqlite.Connection,
    user_id: int,
    amount: int,
    reason: str,
    ref_id: Optional[str] = None,
) -> bool:
    """Внутренняя функция для изменения баланса и записи в ledger. Вызывается только внутри транзакции."""
    if amount < 0:
        cursor = await db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ? AND balance >= ?",
            (amount, user_id, -amount),
        )
        if cursor.rowcount == 0:
            return False
    else:
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id),
        )
    await db.execute(
        "INSERT INTO ledger_entries (user_id, amount, reason, ref_id) VALUES (?, ?, ?, ?)",
        (user_id, amount, reason, ref_id),
    )
    return True


async def add_balance_unrestricted(
    user_id: int, amount: int, reason: str, ref_id: Optional[str] = None
) -> bool:
    """Начисляет средства без проверки лимитов (для возвратов, админ. команд)."""
    if amount <= 0:
        return False
    async with connect() as db:
        await db.execute("BEGIN IMMEDIATE;")
        success = await _change_balance(db, user_id, amount, reason, ref_id)
        if success:
            await db.commit()
        else:
            await db.rollback()
        return success


async def spend_balance(
    user_id: int,
    amount: int,
    reason: str,
    ref_id: Optional[str] = None,
    idem_key: Optional[str] = None,
) -> bool:
    """Списывает средства у пользователя в рамках транзакции."""
    if amount <= 0:
        return False
    async with connect() as db:
        await db.execute("BEGIN IMMEDIATE;")
        try:
            if idem_key and not await check_idempotency_key(db, idem_key, user_id):
                await db.commit()
                return True

            success = await _change_balance(db, user_id, -amount, reason, ref_id)
            if success:
                await db.commit()
            else:
                await db.rollback()
            return success
        except Exception:
            await db.rollback()
            raise


async def add_balance_with_checks(
    user_id: int, amount: int, source: str, ref_id: Optional[str] = None
) -> Dict[str, Union[bool, str]]:
    """Начисляет средства пользователю, проверяя все экономические лимиты и правила."""
    if amount <= 0:
        return {"success": False, "reason": "invalid_amount"}

    # --- ИСПРАВЛЕНО: Админы обходят лимиты ---
    if user_id in settings.ADMIN_IDS:
        success = await add_balance_unrestricted(user_id, amount, source, ref_id)
        return {"success": success}

    rules = EARN_RULES.get(source)
    if not rules:
        return {"success": False, "reason": "unknown_source"}
    if rules.get("unlimited"):
        success = await add_balance_unrestricted(user_id, amount, source, ref_id)
        return {"success": success}

    async with connect() as db:
        try:
            await db.execute("BEGIN IMMEDIATE;")

            daily_cap = rules.get("daily_cap")
            if daily_cap is not None:
                today = datetime.date.today()
                cursor = await db.execute(
                    "SELECT amount FROM earn_counters_daily WHERE user_id = ? AND source = ? AND day = ?",
                    (user_id, source, today),
                )
                daily_row = await cursor.fetchone()
                current_daily_amount = daily_row["amount"] if daily_row else 0
                if current_daily_amount + amount > daily_cap:
                    await db.rollback()
                    return {"success": False, "reason": "daily_cap_exceeded"}

            rpm_cap = rules.get("rpm")
            if rpm_cap is not None:
                now = datetime.datetime.now()
                minute_start = now.replace(second=0, microsecond=0)
                cursor = await db.execute(
                    "SELECT ops FROM earn_counters_window WHERE user_id=? AND source=? AND window_start=? AND window_size='1m'",
                    (user_id, source, minute_start),
                )
                rpm_row = await cursor.fetchone()
                current_rpm_ops = rpm_row["ops"] if rpm_row else 0
                if current_rpm_ops + 1 > rpm_cap:
                    await db.rollback()
                    return {"success": False, "reason": "rate_limit_minute"}

            rph_cap = rules.get("rph")
            if rph_cap is not None:
                now = datetime.datetime.now()
                hour_start = now.replace(minute=0, second=0, microsecond=0)
                cursor = await db.execute(
                    "SELECT ops FROM earn_counters_window WHERE user_id=? AND source=? AND window_start=? AND window_size='1h'",
                    (user_id, source, hour_start),
                )
                rph_row = await cursor.fetchone()
                current_rph_ops = rph_row["ops"] if rph_row else 0
                if current_rph_ops + 1 > rph_cap:
                    await db.rollback()
                    return {"success": False, "reason": "rate_limit_hour"}

            if not await _change_balance(db, user_id, amount, source, ref_id):
                await db.rollback()
                return {"success": False, "reason": "db_error"}

            if daily_cap is not None:
                await db.execute(
                    "INSERT INTO earn_counters_daily (user_id, source, day, amount, ops) VALUES (?, ?, ?, ?, 1) "
                    "ON CONFLICT(user_id, source, day) DO UPDATE SET amount = amount + ?, ops = ops + 1",
                    (user_id, source, today, amount, amount),
                )
            if rpm_cap is not None:
                await db.execute(
                    "INSERT INTO earn_counters_window (user_id, source, window_start, window_size, ops) VALUES (?, ?, ?, '1m', 1) "
                    "ON CONFLICT(user_id, source, window_start, window_size) DO UPDATE SET ops = ops + 1",
                    (user_id, source, minute_start),
                )
            if rph_cap is not None:
                await db.execute(
                    "INSERT INTO earn_counters_window (user_id, source, window_start, window_size, ops) VALUES (?, ?, ?, '1h', 1) "
                    "ON CONFLICT(user_id, source, window_start, window_size) DO UPDATE SET ops = ops + 1",
                    (user_id, source, hour_start),
                )

            await db.commit()
            return {"success": True}

        except Exception as e:
            await db.rollback()
            print(f"Transaction failed in add_balance_with_checks: {e}")
            return {"success": False, "reason": "transaction_failed"}


async def create_reward_request(
    user_id: int, item_id: str, stars_cost: int, idem_key: str
) -> Dict[str, Union[bool, str, int]]:
    """Создает заявку на подарок, удерживая звезды."""
    async with connect() as db:
        try:
            await db.execute("BEGIN IMMEDIATE;")

            if not await check_idempotency_key(db, idem_key, user_id):
                await db.commit()
                cursor = await db.execute(
                    "SELECT id FROM rewards WHERE user_id = ? ORDER BY id DESC LIMIT 1",
                    (user_id,),
                )
                last_reward = await cursor.fetchone()
                return {
                    "success": True,
                    "already_exists": True,
                    "reward_id": last_reward["id"] if last_reward else None,
                }

            # --- ИСПРАВЛЕНО: Админы обходят лимиты на вывод ---
            if user_id not in settings.ADMIN_IDS:
                today = datetime.date.today()
                cursor = await db.execute(
                    "SELECT ops, amount FROM reward_counters_daily WHERE user_id = ? AND day = ?",
                    (user_id, today),
                )
                counter = await cursor.fetchone()
                current_ops = counter["ops"] if counter else 0
                current_amount = counter["amount"] if counter else 0

                if current_ops >= settings.MAX_REWARDS_PER_DAY:
                    await db.rollback()
                    return {"success": False, "reason": "daily_ops_limit"}
                if current_amount + stars_cost > settings.MAX_REWARDS_STARS_PER_DAY:
                    await db.rollback()
                    return {"success": False, "reason": "daily_amount_limit"}

            hold_success = await _change_balance(
                db, user_id, -stars_cost, "reward_hold"
            )
            if not hold_success:
                await db.rollback()
                return {"success": False, "reason": "insufficient_funds"}

            cursor = await db.execute(
                "INSERT INTO rewards (user_id, item_id, stars_cost, status) VALUES (?, ?, ?, 'pending')",
                (user_id, item_id, stars_cost),
            )
            reward_id = cursor.lastrowid

            await db.execute(
                "UPDATE ledger_entries SET ref_id = ? WHERE id = (SELECT id FROM ledger_entries WHERE user_id = ? AND reason = 'reward_hold' ORDER BY id DESC LIMIT 1)",
                (f"reward:{reward_id}", user_id),
            )

            if user_id not in settings.ADMIN_IDS:
                await db.execute(
                    "INSERT INTO reward_counters_daily (user_id, day, ops, amount) VALUES (?, ?, 1, ?) "
                    "ON CONFLICT(user_id, day) DO UPDATE SET ops = ops + 1, amount = amount + ?",
                    (user_id, today, stars_cost, stars_cost),
                )

            await db.commit()
            return {"success": True, "reward_id": reward_id}
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create reward request: {e}")
            return {"success": False, "reason": "db_error"}


async def _update_reward_status(
    db: aiosqlite.Connection,
    reward_id: int,
    new_status: str,
    admin_id: int,
    notes: Optional[str] = None,
):
    """Внутренняя функция для смены статуса заявки и логирования действия."""
    await db.execute(
        "UPDATE rewards SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (new_status, notes, reward_id),
    )
    await db.execute(
        "INSERT INTO reward_actions (reward_id, admin_id, action, notes) VALUES (?, ?, ?, ?)",
        (reward_id, admin_id, new_status, notes),
    )


async def reject_reward(reward_id: int, admin_id: int, notes: str) -> bool:
    """Отклоняет заявку и возвращает звезды пользователю."""
    async with connect() as db:
        try:
            await db.execute("BEGIN IMMEDIATE;")
            cursor = await db.execute(
                "SELECT user_id, stars_cost, status FROM rewards WHERE id = ?",
                (reward_id,),
            )
            reward = await cursor.fetchone()
            if not reward or reward["status"] not in ["pending", "approved"]:
                await db.rollback()
                return False

            await _change_balance(
                db,
                reward["user_id"],
                reward["stars_cost"],
                "reward_revert",
                f"reward:{reward_id}",
            )

            await _update_reward_status(db, reward_id, "rejected", admin_id, notes)

            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to reject reward: {e}")
            return False


async def approve_reward(
    reward_id: int, admin_id: int, notes: Optional[str] = None
) -> bool:
    """Одобряет заявку."""
    async with connect() as db:
        try:
            await db.execute("BEGIN IMMEDIATE;")
            await _update_reward_status(db, reward_id, "approved", admin_id, notes)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to approve reward: {e}")
            return False


async def fulfill_reward(
    reward_id: int, admin_id: int, notes: Optional[str] = None
) -> bool:
    """Помечает заявку как выполненную."""
    async with connect() as db:
        try:
            await db.execute("BEGIN IMMEDIATE;")
            await _update_reward_status(db, reward_id, "fulfilled", admin_id, notes)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to fulfill reward: {e}")
            return False


async def get_pending_rewards(page: int = 1, limit: int = 5) -> List[dict]:
    """Получает список заявок в статусе 'pending'."""
    async with connect() as db:
        offset = (page - 1) * limit
        cursor = await db.execute(
            "SELECT r.id, r.user_id, u.username, r.item_id, r.stars_cost, r.created_at "
            "FROM rewards r JOIN users u ON r.user_id = u.user_id "
            "WHERE r.status = 'pending' ORDER BY r.created_at ASC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_pending_rewards_count() -> int:
    """Считает количество заявок в статусе 'pending'."""
    async with connect() as db:
        cursor = await db.execute(
            "SELECT COUNT(id) as count FROM rewards WHERE status = 'pending'"
        )
        row = await cursor.fetchone()
        return row["count"] if row else 0


async def get_reward_full_details(reward_id: int) -> Optional[dict]:
    """Получает всю информацию по заявке для админ-панели."""
    async with connect() as db:
        cursor = await db.execute(
            "SELECT r.*, u.username, u.full_name, u.balance, u.registration_date, u.risk_level "
            "FROM rewards r JOIN users u ON r.user_id = u.user_id WHERE r.id = ?",
            (reward_id,),
        )
        reward_data = await cursor.fetchone()
        if not reward_data:
            return None

        cursor = await db.execute(
            "SELECT amount, reason, ref_id, created_at FROM ledger_entries WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
            (reward_data["user_id"],),
        )
        ledger_history = await cursor.fetchall()

        return {
            "reward": dict(reward_data),
            "ledger": [dict(row) for row in ledger_history],
        }


async def populate_achievements():
    """Заполняет таблицу достижений."""
    async with connect() as db:
        achievements_list = [
            ("first_steps", "Первые шаги", "Просто запустить бота.", 1, "Обычная"),
            ("first_referral", "Первопроходец", "Пригласить 1 друга.", 5, "Обычная"),
            (
                "bonus_hunter",
                "Охотник за бонусами",
                "Собрать первый ежедневный бонус.",
                3,
                "Обычная",
            ),
            ("curious", "Любопытный", 'Зайти в раздел "Профиль".', 1, "Обычная"),
            ("friendly", "Дружелюбный", "Пригласить 5 друзей.", 10, "Обычная"),
            (
                "code_breaker",
                "Взломщик кодов",
                "Активировать 1 промокод.",
                5,
                "Обычная",
            ),
            ("social", "Душа компании", "Пригласить 15 друзей.", 20, "Редкая"),
            ("regular", "Завсегдатай", "Заходить в бота 3 дня подряд.", 10, "Редкая"),
            ("magnate", "Магнат", "Накопить на балансе 100 звёзд.", 15, "Редкая"),
            (
                "promo_master",
                "Магистр промокодов",
                "Активировать 3 разных промокода.",
                20,
                "Редкая",
            ),
            ("legend", "Легенда", "Пригласить 50 друзей.", 50, "Эпическая"),
            (
                "king",
                "Король рефералов",
                "Удержать 1 место в топе 3 дня.",
                100,
                "Эпическая",
            ),
            (
                "meta",
                "Что ты такое?",
                "Попытаться использовать команду /info на самого себя.",
                5,
                "Мифическая",
            ),
        ]
        await db.executemany(
            "INSERT OR IGNORE INTO achievements (id, name, description, reward, rarity) VALUES (?, ?, ?, ?, ?)",
            achievements_list,
        )
        await db.commit()


async def add_user(user_id, username, full_name, referrer_id=None):
    async with connect() as db:
        cursor = await db.execute(
            "SELECT user_id FROM users WHERE user_id = ?", (user_id,)
        )
        if await cursor.fetchone() is None:
            reg_time = int(time.time())
            await db.execute("BEGIN IMMEDIATE;")
            await db.execute(
                "INSERT INTO users (user_id, username, full_name, invited_by, registration_date, last_seen, created_at) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                (user_id, username, full_name, referrer_id, reg_time, reg_time),
            )
            await _change_balance(db, user_id, 0, "initial_balance")

            if referrer_id:
                await db.execute(
                    "INSERT OR IGNORE INTO referrals (referrer_id, referred_id) VALUES (?, ?)",
                    (referrer_id, user_id),
                )
                # referral bonus is handled in user_handler to send a notification
            await db.commit()
            return True
        else:
            # --- ИСПРАВЛЕНО: Обновляем username и full_name при каждом /start ---
            await db.execute(
                "UPDATE users SET username = ?, full_name = ? WHERE user_id = ?",
                (username, full_name, user_id),
            )
            await db.commit()
        return False


async def update_user_last_seen(user_id: int):
    async with connect() as db:
        await db.execute(
            "UPDATE users SET last_seen = ? WHERE user_id = ?",
            (int(time.time()), user_id),
        )
        await db.commit()


async def get_user_balance(user_id):
    async with connect() as db:
        cursor = await db.execute(
            "SELECT balance FROM users WHERE user_id = ?", (user_id,)
        )
        result = await cursor.fetchone()
        return result[0] if result else 0


async def get_referrals_count(user_id):
    async with connect() as db:
        cursor = await db.execute(
            "SELECT COUNT(id) FROM referrals WHERE referrer_id = ?", (user_id,)
        )
        result = await cursor.fetchone()
        return result[0] if result else 0


async def get_full_user_info(user_id):
    async with connect() as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user_data = await cursor.fetchone()
        if not user_data:
            return None
        cursor = await db.execute(
            "SELECT referred_id FROM referrals WHERE referrer_id = ?", (user_id,)
        )
        invited_users = await cursor.fetchall()
        cursor = await db.execute(
            "SELECT code FROM promo_activations WHERE user_id = ?", (user_id,)
        )
        activated_codes = await cursor.fetchall()
        return {
            "user_data": dict(user_data),
            "invited_users": [i[0] for i in invited_users],
            "activated_codes": [c[0] for c in activated_codes],
        }


async def get_top_referrers(limit=5):
    async with connect() as db:
        cursor = await db.execute(
            """
            SELECT referrer_id, COUNT(referred_id) as ref_count
            FROM referrals GROUP BY referrer_id ORDER BY ref_count DESC LIMIT ?
        """,
            (limit,),
        )
        return await cursor.fetchall()


async def activate_promo(user_id, code, idem_key: str):
    async with connect() as db:
        try:
            await db.execute("BEGIN IMMEDIATE;")

            # --- ИСПРАВЛЕНО: Проверка идемпотентности для избежания двойной активации ---
            if not await check_idempotency_key(db, idem_key, user_id):
                cursor = await db.execute(
                    "SELECT 1 FROM promo_activations WHERE user_id = ? AND code = ?",
                    (user_id, code),
                )
                if await cursor.fetchone():
                    await db.commit()
                    return "already_activated"
                # Если ключ есть, а активации нет - это повторный клик на сбойную операцию. Просто продолжаем.

            cursor = await db.execute(
                "SELECT reward FROM promocodes WHERE code=? AND uses_left > 0", (code,)
            )
            row = await cursor.fetchone()
            if not row:
                await db.rollback()
                return "not_found"
            reward = row[0]

            # Проверяем, не активировал ли юзер этот код ранее
            cursor = await db.execute(
                "SELECT 1 FROM promo_activations WHERE user_id = ? AND code = ?",
                (user_id, code),
            )
            if await cursor.fetchone():
                await db.commit()  # Завершаем транзакцию, так как ничего не меняли
                return "already_activated"

            await db.execute(
                "INSERT INTO promo_activations(user_id, code) VALUES(?, ?)",
                (user_id, code),
            )

            cursor = await db.execute(
                "UPDATE promocodes SET uses_left = uses_left - 1 WHERE code=? AND uses_left > 0",
                (code,),
            )
            if cursor.rowcount == 0:
                await db.rollback()
                return "not_found"

            result = await add_balance_with_checks(
                user_id, reward, "promo_activation", ref_id=code
            )
            if not result["success"]:
                await db.rollback()
                return result["reason"]

            await db.commit()
            return reward
        except aiosqlite.IntegrityError:
            await db.rollback()
            return "already_activated"
        except Exception as e:
            await db.rollback()
            logger.error(f"Error in activate_promo transaction: {e}")
            return "error"


# --- ИСПРАВЛЕНО: Логика получения бонуса для предотвращения race condition ---
async def get_daily_bonus(user_id):
    async with connect() as db:
        current_time = int(time.time())
        # 86400 секунд = 24 часа
        time_limit = current_time - 86400

        # --- ИСПРАВЛЕНО: Админы могут получать бонус без ограничений ---
        is_admin = user_id in settings.ADMIN_IDS

        try:
            await db.execute("BEGIN IMMEDIATE;")

            # Атомарно обновляем время, только если прошло 24 часа (для обычных юзеров)
            update_query = "UPDATE users SET last_bonus_time = ? WHERE user_id = ?"
            params = [current_time, user_id]
            if not is_admin:
                update_query += " AND last_bonus_time < ?"
                params.append(time_limit)

            cursor = await db.execute(update_query, tuple(params))

            # Если ни одна строка не была обновлена, значит бонус уже взят
            if cursor.rowcount == 0:
                await db.rollback()
                cursor = await db.execute(
                    "SELECT last_bonus_time FROM users WHERE user_id = ?", (user_id,)
                )
                res = await cursor.fetchone()
                last_bonus_time = res[0] if res else 0
                return {
                    "status": "wait",
                    "seconds_left": 86400 - (current_time - last_bonus_time),
                }

            # Если обновление прошло, начисляем награду
            reward = random.randint(1, 5)
            result = await add_balance_with_checks(user_id, reward, "daily_bonus")

            if not result["success"]:
                await db.rollback()
                return {"status": "error", "reason": result.get("reason")}

            await db.commit()
            return {"status": "success", "reward": reward}
        except Exception as e:
            await db.rollback()
            logger.error(f"Error in get_daily_bonus transaction: {e}")
            return {"status": "error"}


async def grant_achievement(user_id, ach_id, bot: Bot) -> bool:
    """Награждает пользователя за достижение."""
    async with connect() as db:
        try:
            await db.execute("BEGIN IMMEDIATE;")
            cursor = await db.execute(
                "SELECT id FROM user_achievements WHERE user_id = ? AND achievement_id = ?",
                (user_id, ach_id),
            )
            if await cursor.fetchone():
                await db.rollback()
                return False

            cursor = await db.execute(
                "SELECT name, reward FROM achievements WHERE id = ?", (ach_id,)
            )
            details = await cursor.fetchone()
            if not details:
                await db.rollback()
                return False

            ach_name, reward = details
            await db.execute(
                "INSERT INTO user_achievements (user_id, achievement_id, completion_date) VALUES (?, ?, ?)",
                (user_id, ach_id, int(time.time())),
            )
            await add_balance_with_checks(user_id, reward, "achievement_reward", ach_id)
            await db.commit()

            try:
                await bot.send_message(
                    user_id,
                    f"🏆 <b>Новое достижение!</b>\nВы открыли: «{ach_name}» (+{reward} ⭐)",
                )
            except Exception as e:
                logger.warning(
                    f"Не удалось уведомить пользователя {user_id} о достижении: {e}"
                )
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Error in grant_achievement transaction: {e}")
            return False


async def create_duel_atomic(p1_id: int, p2_id: int, stake: int, idem_key: str):
    """Создает дуэль, списывая ставки с обоих игроков."""
    async with connect() as db:
        try:
            await db.execute("BEGIN IMMEDIATE;")

            if not await check_idempotency_key(db, idem_key, p2_id):
                await db.commit()
                return None

            p1_success = await _change_balance(db, p1_id, -stake, "duel_stake_hold")
            if not p1_success:
                await db.rollback()
                return "p1_insufficient_funds"

            p2_success = await _change_balance(db, p2_id, -stake, "duel_stake_hold")
            if not p2_success:
                await _change_balance(db, p1_id, stake, "duel_creation_refund")
                await db.rollback()
                return "p2_insufficient_funds"

            bank = stake * 2
            cur = await db.execute(
                "INSERT INTO duel_matches (stake, bank, state) VALUES (?, ?, 'active')",
                (stake, bank),
            )
            match_id = cur.lastrowid
            await db.execute(
                "INSERT INTO duel_players (match_id, user_id, role) VALUES (?, ?, 'p1'), (?, ?, 'p2')",
                (match_id, p1_id, match_id, p2_id),
            )
            await db.commit()
            return match_id
        except Exception as e:
            await db.rollback()
            logger.error(f"create_duel TX error: {e}")
            return None


async def finish_duel_atomic(
    match_id: int,
    winner_id: int,
    loser_id: int,
    prize: int,
    is_draw: bool = False,
    stake: int = 0,
):
    """Завершает дуэль и распределяет банк."""
    async with connect() as db:
        try:
            await db.execute("BEGIN IMMEDIATE;")

            one_hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)
            cursor = await db.execute(
                """
                SELECT COUNT(DISTINCT m.id)
                FROM duel_matches m
                JOIN duel_players p1 ON m.id = p1.match_id
                JOIN duel_players p2 ON m.id = p2.match_id
                WHERE ((p1.user_id = ? AND p2.user_id = ?) OR (p1.user_id = ? AND p2.user_id = ?))
                AND m.created_at > ? AND m.state IN ('finished', 'interrupted')
            """,
                (winner_id, loser_id, loser_id, winner_id, one_hour_ago),
            )
            recent_games = await cursor.fetchone()
            if recent_games and recent_games[0] > 5:
                logger.warning(
                    f"ANTI-ABUSE: Users {winner_id} and {loser_id} played {recent_games[0]} games recently. Match ID: {match_id}"
                )

            if is_draw:
                await _change_balance(
                    db, winner_id, stake, "duel_draw_refund", str(match_id)
                )
                await _change_balance(
                    db, loser_id, stake, "duel_draw_refund", str(match_id)
                )
                await db.execute(
                    "UPDATE duel_matches SET state = 'draw' WHERE id = ?", (match_id,)
                )
            else:
                await add_balance_with_checks(
                    winner_id, prize, "duel_win", str(match_id)
                )
                await db.execute(
                    "UPDATE users SET duel_wins = duel_wins + 1 WHERE user_id = ?",
                    (winner_id,),
                )
                await db.execute(
                    "UPDATE users SET duel_losses = duel_losses + 1 WHERE user_id = ?",
                    (loser_id,),
                )
                await db.execute(
                    "UPDATE duel_players SET is_winner = 1 WHERE match_id = ? AND user_id = ?",
                    (match_id, winner_id),
                )
                await db.execute(
                    "UPDATE duel_matches SET state = 'finished' WHERE id = ?",
                    (match_id,),
                )
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Ошибка в транзакции finish_duel: {e}")


async def force_surrender_duel(match_id: int, user_id: int):
    """Принудительно завершает дуэль, когда игрок выходит из зависшей игры."""
    async with connect() as db:
        cursor = await db.execute(
            "SELECT state, stake FROM duel_matches WHERE id = ?", (match_id,)
        )
        match_info = await cursor.fetchone()
        if not match_info or match_info["state"] != "active":
            return

        cursor = await db.execute(
            "SELECT user_id FROM duel_players WHERE match_id = ? AND user_id != ?",
            (match_id, user_id),
        )
        opponent = await cursor.fetchone()
        if not opponent:
            await add_balance_unrestricted(
                user_id, match_info["stake"], "duel_stuck_refund", f"stuck:{match_id}"
            )
            await db.execute(
                "UPDATE duel_matches SET state = 'interrupted' WHERE id = ?",
                (match_id,),
            )
            await db.commit()
            return

        winner_id = opponent["user_id"]
        loser_id = user_id

        await add_balance_unrestricted(
            winner_id, match_info["stake"], "duel_stuck_refund", f"stuck:{match_id}"
        )

        await db.execute(
            "UPDATE users SET duel_losses = duel_losses + 1 WHERE user_id = ?",
            (loser_id,),
        )
        await db.execute(
            "UPDATE duel_matches SET state = 'interrupted' WHERE id = ?", (match_id,)
        )
        await db.commit()


async def get_duel_details_for_rematch(match_id: int) -> Optional[dict]:
    """Получает данные, необходимые для реванша."""
    async with connect() as db:
        cursor = await db.execute(
            """
            SELECT m.stake, p1.user_id as p1_id, p2.user_id as p2_id
            FROM duel_matches m
            JOIN duel_players p1 ON m.id = p1.match_id AND p1.role = 'p1'
            JOIN duel_players p2 ON m.id = p2.match_id AND p2.role = 'p2'
            WHERE m.id = ?
        """,
            (match_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def create_timer_match(p1_id: int, p2_id: int, stake: int):
    """Создает таймер-матч, списывая ставки с обоих игроков."""
    async with connect() as db:
        try:
            await db.execute("BEGIN IMMEDIATE;")

            p1_success = await _change_balance(db, p1_id, -stake, "timer_stake_hold")
            if not p1_success:
                await db.rollback()
                return None, "p1_insufficient_funds"

            p2_success = await _change_balance(db, p2_id, -stake, "timer_stake_hold")
            if not p2_success:
                await _change_balance(db, p1_id, stake, "timer_creation_refund")
                await db.rollback()
                return None, "p2_insufficient_funds"

            bank = stake * 2
            stop_second = random.randint(0, 9)
            cur = await db.execute(
                "INSERT INTO timer_matches (stake, bank, stop_second, state) VALUES (?, ?, ?, 'active')",
                (stake, bank, stop_second),
            )
            match_id = cur.lastrowid
            await db.execute(
                "INSERT INTO timer_players (match_id, user_id, role) VALUES (?, ?, 'p1'), (?, ?, 'p2')",
                (match_id, p1_id, match_id, p2_id),
            )
            await db.commit()
            return match_id, stop_second
        except Exception as e:
            await db.rollback()
            logger.error(f"create_timer_match TX error: {e}")
            return None, "db_error"


async def finish_timer_match(
    match_id: int,
    winner_id: Optional[int] = None,
    is_draw: bool = False,
    new_bank: int = 0,
):
    """Завершает таймер-матч, распределяя банк."""
    async with connect() as db:
        try:
            await db.execute("BEGIN IMMEDIATE;")
            cursor = await db.execute(
                "SELECT stake, bank, state FROM timer_matches WHERE id = ?", (match_id,)
            )
            details = await cursor.fetchone()
            if not details or details["state"] != "active":
                await db.rollback()  # Игра уже завершена
                return

            stake = details["stake"]

            cursor = await db.execute(
                "SELECT user_id FROM timer_players WHERE match_id = ?", (match_id,)
            )
            players = [row["user_id"] for row in await cursor.fetchall()]
            p1_id, p2_id = players[0], players[1]

            if is_draw:
                await _change_balance(
                    db, p1_id, stake, "timer_draw_refund", str(match_id)
                )
                await _change_balance(
                    db, p2_id, stake, "timer_draw_refund", str(match_id)
                )
                await db.execute(
                    "UPDATE timer_matches SET state = 'draw' WHERE id = ?",
                    (match_id,),
                )
            elif winner_id:
                prize = (stake * 2) - int((stake * 2) * 0.07)
                await add_balance_with_checks(
                    winner_id, prize, "timer_win", str(match_id)
                )
                await db.execute(
                    "UPDATE timer_matches SET state = 'finished', winner_id = ? WHERE id = ?",
                    (winner_id, match_id),
                )
                await db.execute(
                    "UPDATE timer_players SET is_winner = 1 WHERE match_id = ? AND user_id = ?",
                    (match_id, winner_id),
                )
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Ошибка в транзакции finish_timer_match: {e}")


async def recalculate_and_get_balance(
    user_id: int,
) -> dict[str, Union[int, bool, str]]:
    """Пересчитывает баланс из ledger и сравнивает с кэшем в таблице users."""
    async with connect() as db:
        cursor = await db.execute(
            "SELECT balance FROM users WHERE user_id = ?", (user_id,)
        )
        cached_row = await cursor.fetchone()
        if not cached_row:
            return {"error": "User not found"}
        cached_balance = cached_row[0]

        cursor = await db.execute(
            "SELECT SUM(amount) FROM ledger_entries WHERE user_id = ?", (user_id,)
        )
        calculated_row = await cursor.fetchone()
        calculated_balance = calculated_row[0] if calculated_row[0] is not None else 0

        return {
            "user_id": user_id,
            "cached_balance": cached_balance,
            "calculated_balance": calculated_balance,
            "is_consistent": cached_balance == calculated_balance,
        }


async def get_user_duel_stats(user_id: int):
    async with connect() as db:
        cursor = await db.execute(
            "SELECT duel_wins, duel_losses FROM users WHERE user_id = ?", (user_id,)
        )
        stats = await cursor.fetchone()
        return (
            {"wins": stats[0], "losses": stats[1]}
            if stats
            else {"wins": 0, "losses": 0}
        )


async def is_user_in_active_duel(user_id: int) -> bool:
    async with connect() as db:
        cursor = await db.execute(
            """
            SELECT 1 FROM duel_players dp
            JOIN duel_matches dm ON dp.match_id = dm.id
            WHERE dp.user_id = ? AND dm.state = 'active'
        """,
            (user_id,),
        )
        return await cursor.fetchone() is not None


async def get_duel_players(match_id: int):
    async with connect() as db:
        cursor = await db.execute(
            "SELECT user_id, role FROM duel_players WHERE match_id = ?", (match_id,)
        )
        return await cursor.fetchall()


async def create_duel_round(match_id: int, round_no: int):
    async with connect() as db:
        await db.execute(
            "INSERT OR IGNORE INTO duel_rounds (match_id, round_no) VALUES (?, ?)",
            (match_id, round_no),
        )
        await db.commit()


async def save_duel_round(
    match_id: int,
    round_no: int,
    p1_card: int,
    p2_card: int,
    result: str,
    special: str = None,
):
    async with connect() as db:
        await db.execute(
            "UPDATE duel_rounds SET p1_card = ?, p2_card = ?, result = ?, special = ? WHERE match_id = ? AND round_no = ?",
            (p1_card, p2_card, result, special, match_id, round_no),
        )
        await db.commit()


async def get_active_duel_id(user_id: int):
    async with connect() as db:
        cursor = await db.execute(
            """
            SELECT m.id FROM duel_matches m
            JOIN duel_players p ON m.id = p.match_id
            WHERE p.user_id = ? AND m.state = 'active'
        """,
            (user_id,),
        )
        result = await cursor.fetchone()
        return result[0] if result else None


async def interrupt_duel(match_id: int):
    async with connect() as db:
        await db.execute(
            "UPDATE duel_matches SET state = 'interrupted' WHERE id = ?", (match_id,)
        )
        await db.commit()


async def get_all_active_duels():
    async with connect() as db:
        cursor = await db.execute("SELECT id FROM duel_matches WHERE state = 'active'")
        return [row[0] for row in await cursor.fetchall()]


async def update_timer_player_click(match_id: int, user_id: int, clicked_at: float):
    async with connect() as db:
        await db.execute(
            "UPDATE timer_players SET clicked_at = ? WHERE user_id = ? AND match_id = ?",
            (clicked_at, user_id, match_id),
        )
        await db.commit()


async def get_timer_match_details(match_id: int):
    async with connect() as db:
        cursor = await db.execute(
            """
            SELECT m.stake, m.bank, p1.user_id, p2.user_id
            FROM timer_matches m
            JOIN timer_players p1 ON m.id = p1.match_id AND p1.role = 'p1'
            JOIN timer_players p2 ON m.id = p2.match_id AND p2.role = 'p2'
            WHERE m.id = ?
        """,
            (match_id,),
        )
        return await cursor.fetchone()


async def get_timer_players(match_id: int):
    async with connect() as db:
        cursor = await db.execute(
            "SELECT user_id FROM timer_players WHERE match_id = ?", (match_id,)
        )
        return [row[0] for row in await cursor.fetchall()]


async def get_active_timer_id(user_id: int):
    async with connect() as db:
        cursor = await db.execute(
            """
            SELECT m.id FROM timer_matches m
            JOIN timer_players p ON m.id = p.match_id
            WHERE p.user_id = ? AND m.state = 'active'
        """,
            (user_id,),
        )
        result = await cursor.fetchone()
        return result[0] if result else None


async def interrupt_timer_match(match_id: int):
    async with connect() as db:
        await db.execute(
            "UPDATE timer_matches SET state = 'interrupted' WHERE id = ?", (match_id,)
        )
        await db.commit()


async def get_all_active_timers():
    async with connect() as db:
        cursor = await db.execute("SELECT id FROM timer_matches WHERE state = 'active'")
        return [row[0] for row in await cursor.fetchall()]


async def get_all_users():
    async with connect() as db:
        cursor = await db.execute("SELECT user_id FROM users")
        return [row[0] for row in await cursor.fetchall()]


# --- ИСПРАВЛЕНО: Поиск по username нечувствителен к регистру ---
async def get_user_by_username(username: str) -> Union[int, None]:
    async with connect() as db:
        cursor = await db.execute(
            "SELECT user_id FROM users WHERE LOWER(username) = LOWER(?)", (username,)
        )
        result = await cursor.fetchone()
        return result[0] if result else None


async def add_promo_code(name, reward, uses):
    async with connect() as db:
        await db.execute(
            "INSERT OR REPLACE INTO promocodes (code, reward, total_uses, uses_left) VALUES (?, ?, ?, ?)",
            (name, reward, uses, uses),
        )
        await db.commit()


async def get_active_promos():
    async with connect() as db:
        cursor = await db.execute(
            "SELECT code, reward, uses_left, total_uses FROM promocodes WHERE uses_left > 0"
        )
        return await cursor.fetchall()


async def get_users_for_notification():
    async with connect() as db:
        twenty_three_hours_ago = int(time.time()) - 82800
        cursor = await db.execute(
            "SELECT user_id FROM users WHERE last_bonus_time > 0 AND last_bonus_time < ?",
            (twenty_three_hours_ago,),
        )
        return [row[0] for row in await cursor.fetchall()]


async def get_all_achievements():
    async with connect() as db:
        cursor = await db.execute(
            "SELECT id, name FROM achievements ORDER BY rarity, name"
        )
        return await cursor.fetchall()


async def get_user_achievements(user_id):
    async with connect() as db:
        cursor = await db.execute(
            "SELECT achievement_id FROM user_achievements WHERE user_id = ?", (user_id,)
        )
        return [row[0] for row in await cursor.fetchall()]


async def get_achievement_details(ach_id):
    async with connect() as db:
        cursor = await db.execute(
            "SELECT name, description, reward, rarity FROM achievements WHERE id = ?",
            (ach_id,),
        )
        return await cursor.fetchone()


# --- НОВОЕ: Функции для расширенной админ-панели ---
async def get_bot_statistics():
    """Собирает общую статистику по боту."""
    async with connect() as db:
        cursor = await db.execute("SELECT COUNT(user_id) FROM users")
        total_users = (await cursor.fetchone())[0]

        today_start_ts = int(
            datetime.datetime.now()
            .replace(hour=0, minute=0, second=0, microsecond=0)
            .timestamp()
        )
        cursor = await db.execute(
            "SELECT COUNT(user_id) FROM users WHERE registration_date >= ?",
            (today_start_ts,),
        )
        new_today = (await cursor.fetchone())[0]

        week_ago_ts = int(
            (datetime.datetime.now() - datetime.timedelta(days=7)).timestamp()
        )
        cursor = await db.execute(
            "SELECT COUNT(user_id) FROM users WHERE registration_date >= ?",
            (week_ago_ts,),
        )
        new_week = (await cursor.fetchone())[0]

        day_ago_ts = int(
            (datetime.datetime.now() - datetime.timedelta(days=1)).timestamp()
        )
        cursor = await db.execute(
            "SELECT COUNT(user_id) FROM users WHERE last_seen >= ?", (day_ago_ts,)
        )
        active_day = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT SUM(balance) FROM users")
        total_balance = (await cursor.fetchone())[0] or 0

        return {
            "total_users": total_users,
            "new_today": new_today,
            "new_week": new_week,
            "active_day": active_day,
            "total_balance": total_balance,
        }


async def get_user_full_details_for_admin(user_id: int):
    """Собирает всю возможную информацию о пользователе для админа."""
    async with connect() as db:
        user_info = await get_full_user_info(user_id)
        if not user_info:
            return None

        cursor = await db.execute(
            "SELECT amount, reason, ref_id, created_at FROM ledger_entries WHERE user_id = ? ORDER BY created_at DESC LIMIT 15",
            (user_id,),
        )
        user_info["ledger"] = [dict(row) for row in await cursor.fetchall()]

        user_info["duel_stats"] = await get_user_duel_stats(user_id)
        user_info["referrals_count"] = await get_referrals_count(user_id)

        return user_info
