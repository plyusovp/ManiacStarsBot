import asyncio
import datetime
import logging
import secrets  # Используем secrets для более криптографически стойких случайных чисел
import sqlite3
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import aiosqlite
from aiogram import Bot

from config import settings
from economy import EARN_RULES

DB_NAME = "maniac_stars.db"


@asynccontextmanager
async def connect() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Asynchronous context manager for connecting to the DB with PRAGMA settings."""
    db_conn = await aiosqlite.connect(DB_NAME)
    db_conn.row_factory = aiosqlite.Row
    await db_conn.execute("PRAGMA journal_mode=WAL;")
    await db_conn.execute("PRAGMA foreign_keys = ON;")
    await db_conn.execute("PRAGMA busy_timeout = 5000;")
    try:
        yield db_conn
    finally:
        await db_conn.close()


async def _begin_transaction(db: aiosqlite.Connection) -> None:
    """Starts a transaction, retrying if another one is in progress."""
    retries = 5
    for attempt in range(retries):
        try:
            await db.execute("BEGIN EXCLUSIVE;")
            return
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempt < retries - 1:
                await asyncio.sleep(0.01 * (attempt + 1))
                continue
            raise


async def init_db() -> None:
    """Initializes and migrates the database schema."""
    async with connect() as db:
        # --- Idempotency Table ---
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
        # --- Users Table ---
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
        # --- Limit Tables ---
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
        # --- Gift System Tables ---
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
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
        # --- Other Tables ---
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
            stop_second REAL NOT NULL,
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

        # --- Migrations and Indexes ---
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

        cursor = await db.execute("PRAGMA table_info(timer_matches)")
        columns_info = {row[1]: row[2] for row in await cursor.fetchall()}
        if columns_info.get("stop_second") == "INTEGER":
            logging.info("Migrating timer_matches.stop_second to REAL...")
            # Turn off foreign keys for safe migration
            await db.execute("PRAGMA foreign_keys=OFF;")
            await db.execute("BEGIN TRANSACTION;")
            try:
                await db.execute(
                    "ALTER TABLE timer_matches RENAME TO _timer_matches_old;"
                )
                await db.execute(
                    """
                    CREATE TABLE timer_matches (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stake INTEGER NOT NULL CHECK(stake > 0),
                        bank INTEGER NOT NULL CHECK(bank >= 0),
                        winner_id INTEGER,
                        stop_second REAL NOT NULL,
                        state TEXT NOT NULL CHECK(state IN ('active','finished','draw','interrupted')),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(winner_id) REFERENCES users(user_id)
                    )"""
                )
                await db.execute(
                    "INSERT INTO timer_matches(id, stake, bank, winner_id, stop_second, state, created_at) SELECT id, stake, bank, winner_id, CAST(stop_second AS REAL), state, created_at FROM _timer_matches_old;"
                )
                await db.execute("DROP TABLE _timer_matches_old;")
                await db.commit()
            except Exception:
                logging.error("Migration failed, rolling back", exc_info=True)
                await db.rollback()
            finally:
                # Always turn foreign keys back on
                await db.execute("PRAGMA foreign_keys=ON;")
            logging.info("Migration complete.")

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
    Checks the idempotency key.
    Returns: True if the key is new, False if it's a duplicate.
    """
    try:
        await db.execute(
            "INSERT INTO idempotency (key, user_id) VALUES (?, ?)", (key, user_id)
        )
        return True
    except aiosqlite.IntegrityError:
        logging.warning(
            "Idempotency key violation",
            extra={"idempotency_key": key, "user_id": user_id},
        )
        return False


async def cleanup_old_idempotency_keys(days: int = 7) -> None:
    """Deletes old idempotency keys."""
    async with connect() as db:
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        cursor = await db.execute(
            "DELETE FROM idempotency WHERE created_at < ?", (cutoff_date,)
        )
        await db.commit()
        logging.info(f"Deleted {cursor.rowcount} old idempotency keys.")


async def _change_balance(
    db: aiosqlite.Connection,
    user_id: int,
    amount: int,
    reason: str,
    ref_id: Optional[str] = None,
) -> bool:
    """Internal function to change balance and write to ledger. Must be called within a transaction."""
    if amount == 0 and reason != "initial_balance":
        return True

    # Use a different query for debit to prevent negative balance
    if amount < 0:
        cursor = await db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ? AND balance >= ?",
            (amount, user_id, -amount),
        )
    else:
        cursor = await db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id),
        )

    if cursor.rowcount == 0:
        # This handles both insufficient funds and non-existent user
        return False

    await db.execute(
        "INSERT INTO ledger_entries (user_id, amount, reason, ref_id) VALUES (?, ?, ?, ?)",
        (user_id, amount, reason, ref_id),
    )
    return True


async def add_balance_unrestricted(
    user_id: int, amount: int, reason: str, ref_id: Optional[str] = None
) -> bool:
    """Adds funds without limit checks (for refunds, admin commands)."""
    if amount <= 0:  # Allow 0 for initial ledger entry
        return False
    async with connect() as db:
        await _begin_transaction(db)
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
    """Spends a user's funds within a transaction."""
    if amount <= 0:
        return False
    async with connect() as db:
        await _begin_transaction(db)
        try:
            if idem_key and not await check_idempotency_key(db, idem_key, user_id):
                # If key exists, it means the operation was already successful.
                # We rollback this empty transaction and return True.
                await db.rollback()
                return True

            success = await _change_balance(db, user_id, -amount, reason, ref_id)
            if success:
                await db.commit()
            else:
                await db.rollback()
            return success
        except Exception:
            await db.rollback()
            logging.error(
                "Spend balance transaction failed",
                exc_info=True,
                extra={"user_id": user_id},
            )
            return False


async def add_balance_with_checks(
    user_id: int, amount: int, source: str, ref_id: Optional[str] = None
) -> Dict[str, Union[bool, str]]:
    """Adds funds to a user, checking all economic limits and rules."""
    if amount <= 0:
        return {"success": False, "reason": "invalid_amount"}

    if user_id in settings.ADMIN_IDS:
        success = await add_balance_unrestricted(user_id, amount, source, ref_id)
        return {"success": success}

    rules = EARN_RULES.get(source)
    if not rules:
        logging.warning(f"Unknown earn source '{source}'", extra={"user_id": user_id})
        return {"success": False, "reason": "unknown_source"}
    if rules.get("unlimited"):
        success = await add_balance_unrestricted(user_id, amount, source, ref_id)
        return {"success": success}

    async with connect() as db:
        try:
            await _begin_transaction(db)

            # Check for user existence before proceeding with limit checks
            cursor = await db.execute(
                "SELECT 1 FROM users WHERE user_id = ?", (user_id,)
            )
            if await cursor.fetchone() is None:
                logging.error(
                    f"Attempted to change balance for non-existent user {user_id}"
                )
                await db.rollback()
                return {"success": False, "reason": "user_not_found"}

            # Here you would add logic for daily caps and rate limits based on `rules`

            if not await _change_balance(db, user_id, amount, source, ref_id):
                await db.rollback()
                return {"success": False, "reason": "update_failed"}

            # Update daily counters if needed
            if "daily_cap" in rules:
                today = datetime.date.today()
                cursor = await db.execute(
                    "SELECT amount FROM earn_counters_daily WHERE user_id = ? AND source = ? AND day = ?",
                    (user_id, source, today),
                )
                row = await cursor.fetchone()
                current_amount = row["amount"] if row else 0
                if current_amount + amount > rules["daily_cap"]:
                    await db.rollback()
                    return {"success": False, "reason": "daily_cap_exceeded"}
                if row:
                    await db.execute(
                        "UPDATE earn_counters_daily SET amount = amount + ?, ops = ops + 1 WHERE user_id = ? AND source = ? AND day = ?",
                        (amount, user_id, source, today),
                    )
                else:
                    await db.execute(
                        "INSERT INTO earn_counters_daily (user_id, source, day, amount, ops) VALUES (?, ?, ?, ?, 1)",
                        (user_id, source, today, amount),
                    )

            await db.commit()
            return {"success": True}
        except Exception:
            await db.rollback()
            logging.error(
                "Transaction failed in add_balance_with_checks",
                exc_info=True,
                extra={"user_id": user_id},
            )
            return {"success": False, "reason": "transaction_failed"}


async def create_reward_request(
    user_id: int, item_id: str, stars_cost: int, idem_key: str
) -> Dict[str, Union[bool, str, int, None]]:
    """Creates a gift request, holding the stars, in a single transaction."""
    if stars_cost <= 0:
        return {"success": False, "reason": "invalid_amount"}

    async with connect() as db:
        await _begin_transaction(db)
        try:
            # Idempotency check first
            cursor = await db.execute(
                "SELECT key FROM idempotency WHERE key = ?", (idem_key,)
            )
            if await cursor.fetchone():
                await db.commit()
                return {"success": True, "reward_id": None}

            # Now, check the balance and hold funds
            success = await _change_balance(
                db, user_id, -stars_cost, "reward_hold", ref_id=idem_key
            )
            if not success:
                await db.rollback()
                return {"success": False, "reason": "insufficient_funds"}

            # Log idempotency key
            await db.execute(
                "INSERT INTO idempotency (key, user_id) VALUES (?, ?)",
                (idem_key, user_id),
            )

            # Create reward record
            cursor = await db.execute(
                "INSERT INTO rewards (user_id, item_id, stars_cost) VALUES (?, ?, ?)",
                (user_id, item_id, stars_cost),
            )
            reward_id = cursor.lastrowid
            await db.commit()
            return {"success": True, "reward_id": reward_id}
        except aiosqlite.IntegrityError as e:
            await db.rollback()
            if "idempotency.key" in str(e):
                return {"success": True, "reward_id": None}
            logging.error("Integrity error in create_reward_request", exc_info=True)
            return {"success": False, "reason": "transaction_failed"}
        except Exception:
            await db.rollback()
            logging.error(
                "Transaction failed in create_reward_request",
                exc_info=True,
                extra={"user_id": user_id, "idem_key": idem_key},
            )
            return {"success": False, "reason": "transaction_failed"}


async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Gets basic information about a user."""
    async with connect() as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def populate_achievements():
    """Заполняет таблицу достижений, обновляя старые и убирая неактуальные."""
    async with connect() as db:
        # !!! ВАЖНО: Мы удаляем старые достижения, которые невозможно выполнить.
        # Это гарантирует, что список будет чистым.
        await db.execute("DELETE FROM achievements WHERE id IN ('king', 'meta')")

        # Награда за каждое достижение установлена в 1 ⭐, как ты просил.
        achievements_list = [
            ("first_steps", "Первые шаги", "Просто запустить бота.", 1, "Обычная"),
            ("first_referral", "Первопроходец", "Пригласить 1 друга.", 1, "Обычная"),
            (
                "bonus_hunter",
                "Охотник за бонусами",
                "Собрать первый ежедневный бонус.",
                1,
                "Обычная",
            ),
            ("curious", "Любопытный", 'Зайти в раздел "Профиль".', 1, "Обычная"),
            ("friendly", "Дружелюбный", "Пригласить 5 друзей.", 1, "Обычная"),
            (
                "code_breaker",
                "Взломщик кодов",
                "Активировать 1 промокод.",
                1,
                "Обычная",
            ),
            ("social", "Душа компании", "Пригласить 15 друзей.", 1, "Редкая"),
            ("regular", "Завсегдатай", "Заходить в бота 3 дня подряд.", 1, "Редкая"),
            ("magnate", "Магнат", "Накопить на балансе 100 звёзд.", 1, "Редкая"),
            (
                "promo_master",
                "Магистр промокодов",
                "Активировать 3 разных промокода.",
                1,
                "Редкая",
            ),
            ("legend", "Легенда", "Пригласить 50 друзей.", 1, "Эпическая"),
            # Неактуальные достижения 'king' и 'meta' были удалены выше.
        ]

        # Обновляем существующие и вставляем новые.
        # Мы используем INSERT OR REPLACE, но в данном случае лучше
        # INSERT OR IGNORE, чтобы не потерять уже полученные, но
        # в исходном коде используется executemany с INSERT OR IGNORE,
        # что не позволяет обновить существующие.

        # Для гарантированного обновления награды, мы должны использовать REPLACE.
        # Чтобы не потерять данные, мы используем три запроса:

        # 1. Обновляем награду для уже существующих достижений
        for ach_id, name, desc, reward, rarity in achievements_list:
            await db.execute(
                "UPDATE achievements SET reward = ?, name = ?, description = ?, rarity = ? WHERE id = ?",
                (reward, name, desc, rarity, ach_id),
            )

        # 2. Вставляем новые достижения (если их нет)
        await db.executemany(
            """
            INSERT OR IGNORE INTO achievements (id, name, description, reward, rarity)
            VALUES (?, ?, ?, ?, ?)
            """,
            achievements_list,
        )
        await db.commit()


async def add_user(
    user_id, username, full_name, referrer_id=None, initial_balance=None
):
    """
    Добавляет нового пользователя в базу данных.
    Возвращает True, если пользователь новый, иначе False.
    """
    if initial_balance is None:
        initial_balance = settings.INITIAL_BALANCE

    async with connect() as db:
        await db.execute("BEGIN IMMEDIATE;")
        try:
            cursor = await db.execute(
                "SELECT user_id FROM users WHERE user_id = ?", (user_id,)
            )
            if await cursor.fetchone() is None:
                reg_time = int(time.time())
                await db.execute(
                    "INSERT INTO users (user_id, username, full_name, invited_by, registration_date, last_seen, created_at, balance) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)",
                    (
                        user_id,
                        username,
                        full_name,
                        referrer_id,
                        reg_time,
                        reg_time,
                        initial_balance,
                    ),
                )
                if initial_balance > 0:
                    await db.execute(
                        "INSERT INTO ledger_entries (user_id, amount, reason) VALUES (?, ?, ?)",
                        (user_id, initial_balance, "initial_balance"),
                    )

                if referrer_id:
                    await db.execute(
                        "INSERT OR IGNORE INTO referrals (referrer_id, referred_id) VALUES (?, ?)",
                        (referrer_id, user_id),
                    )
                await db.commit()
                return True
            else:
                await db.execute(
                    "UPDATE users SET username = ?, full_name = ? WHERE user_id = ?",
                    (username, full_name, user_id),
                )
                await db.commit()
                return False
        except Exception:
            await db.rollback()
            logging.error("Transaction failed in add_user", exc_info=True)
            return False


async def user_exists(user_id: int) -> bool:
    """Проверяет существование пользователя."""
    async with connect() as db:
        cursor = await db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        return await cursor.fetchone() is not None


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


# ... (The rest of the file remains the same)
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
            SELECT u.full_name, COUNT(r.referred_id) as ref_count
            FROM referrals r
            JOIN users u ON r.referrer_id = u.user_id
            GROUP BY r.referrer_id, u.full_name
            ORDER BY ref_count DESC
            LIMIT ?
        """,
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_promocode(code: str) -> Optional[dict]:
    """Получает информацию о промокоде."""
    async with connect() as db:
        cursor = await db.execute("SELECT * FROM promocodes WHERE code = ?", (code,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def has_user_activated_promo(user_id: int, code: str) -> bool:
    """Проверяет, активировал ли пользователь данный промокод."""
    async with connect() as db:
        cursor = await db.execute(
            "SELECT 1 FROM promo_activations WHERE user_id = ? AND code = ?",
            (user_id, code),
        )
        return await cursor.fetchone() is not None


async def activate_promo(user_id, code, idem_key: str):
    async with connect() as db:
        try:
            await db.execute("BEGIN IMMEDIATE;")

            if not await check_idempotency_key(db, idem_key, user_id):
                cursor = await db.execute(
                    "SELECT 1 FROM promo_activations WHERE user_id = ? AND code = ?",
                    (user_id, code),
                )
                if await cursor.fetchone():
                    await db.commit()
                    return "already_activated"
                # If key exists but promo not activated, it's a weird state, treat as error
                await db.rollback()
                return "error"

            cursor = await db.execute(
                "SELECT reward FROM promocodes WHERE code=? AND uses_left > 0", (code,)
            )
            row = await cursor.fetchone()
            if not row:
                await db.rollback()
                return "not_found"
            reward = row[0]

            cursor = await db.execute(
                "SELECT 1 FROM promo_activations WHERE user_id = ? AND code = ?",
                (user_id, code),
            )
            if await cursor.fetchone():
                await db.commit()
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

            if not await _change_balance(db, user_id, reward, "promo_activation", code):
                await db.rollback()
                return "unknown_error"

            await db.commit()
            return reward
        except aiosqlite.IntegrityError:
            await db.rollback()
            return "already_activated"
        except Exception:
            await db.rollback()
            logging.error(
                "Error in activate_promo transaction",
                exc_info=True,
                extra={"user_id": user_id},
            )
            return "error"


# ... (весь код до функции get_daily_bonus) ...


async def get_daily_bonus(user_id: int) -> Dict[str, Any]:
    """
    Атомарно выдает ежедневный бонус с повторными попытками при блокировке БД.
    """
    retries = 5  # Попытки на случай, если базу залочило
    for attempt in range(retries):
        try:
            async with connect() as db:
                await _begin_transaction(db)
                try:
                    # Внутренняя логика, которая может упасть
                    current_time = int(time.time())
                    # ИСПОЛЬЗУЕМ НОВУЮ НАСТРОЙКУ ИЗ CONFIG.PY
                    time_limit = current_time - (settings.DAILY_BONUS_HOURS * 3600)
                    is_admin = user_id in settings.ADMIN_IDS

                    update_query = (
                        "UPDATE users SET last_bonus_time = ? WHERE user_id = ?"
                    )
                    params = [current_time, user_id]

                    if not is_admin:
                        update_query += " AND last_bonus_time < ?"
                        params.append(time_limit)

                    cursor = await db.execute(update_query, tuple(params))

                    if cursor.rowcount == 0:
                        await db.rollback()
                        cursor = await db.execute(
                            "SELECT last_bonus_time FROM users WHERE user_id = ?",
                            (user_id,),
                        )
                        res = await cursor.fetchone()
                        last_bonus_time = res["last_bonus_time"] if res else 0
                        elapsed = current_time - last_bonus_time
                        seconds_left = max(
                            0, (settings.DAILY_BONUS_HOURS * 3600) - elapsed
                        )
                        return {"status": "wait", "seconds_left": seconds_left}

                    # ИСПОЛЬЗУЕМ СУММУ БОНУСА ИЗ CONFIG.PY
                    reward = settings.DAILY_BONUS_AMOUNT
                    if not await _change_balance(db, user_id, reward, "daily_bonus"):
                        await db.rollback()
                        return {"status": "error", "reason": "update_failed"}

                    await db.commit()
                    return {"status": "success", "reward": reward}

                except Exception as e:
                    await db.rollback()
                    # Если ошибка - это блокировка, то мы её прокидываем выше, чтобы сработал retry
                    if isinstance(e, sqlite3.OperationalError) and "locked" in str(e):
                        raise
                    # Все другие ошибки логируем как обычно
                    logging.error(
                        "Error in get_daily_bonus inner transaction on attempt %d",
                        attempt + 1,
                        exc_info=True,
                        extra={"user_id": user_id},
                    )
                    return {"status": "error", "reason": "transaction_failed"}

        # Ловим ошибку блокировки и ждём перед новой попыткой
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempt < retries - 1:
                logging.warning(
                    "Database locked for get_daily_bonus on attempt %d for user %d. Retrying...",
                    attempt + 1,
                    user_id,
                )
                await asyncio.sleep(0.01 * (attempt + 1))
                continue
            else:
                logging.error(
                    "Failed to get daily bonus for user %d after %d retries",
                    user_id,
                    retries,
                    exc_info=True,
                )
                return {"status": "error", "reason": "db_locked"}
        # Ловим все остальные непредвиденные ошибки
        except Exception:
            logging.error(
                "Unhandled exception in get_daily_bonus for user %d",
                user_id,
                exc_info=True,
            )
            return {"status": "error", "reason": "unknown_error"}

    # Если все попытки провалились
    return {"status": "error", "reason": "max_retries_exceeded"}


# ... (остальной код файла db.py) ...


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
            await _change_balance(db, user_id, reward, "achievement_reward", ach_id)
            await db.commit()

            try:
                await bot.send_message(
                    user_id,
                    f"🏆 <b>Новое достижение!</b>\nВы открыли: «{ach_name}» (+{reward} ⭐)",
                )
            except Exception:
                logging.warning(
                    "Не удалось уведомить пользователя о достижении",
                    exc_info=True,
                    extra={"user_id": user_id},
                )
            return True
        except Exception:
            await db.rollback()
            logging.error(
                "Error in grant_achievement transaction",
                exc_info=True,
                extra={"user_id": user_id},
            )
            return False


async def create_duel(p1_id: int, p2_id: int, stake: int) -> Optional[int]:
    """
    Атомарно создает дуэль: списывает ставки и создает матч в одной транзакции.
    Возвращает ID матча в случае успеха, иначе None.
    """
    async with connect() as db:
        try:
            await _begin_transaction(db)

            # Пытаемся списать средства с обоих игроков
            p1_success = await _change_balance(
                db, p1_id, -stake, "duel_stake_hold", f"vs_{p2_id}"
            )
            p2_success = await _change_balance(
                db, p2_id, -stake, "duel_stake_hold", f"vs_{p1_id}"
            )

            # Если у кого-то не хватает средств, откатываем транзакцию
            if not p1_success or not p2_success:
                await db.rollback()
                logging.warning(
                    f"Failed to create duel between {p1_id} and {p2_id} due to insufficient funds."
                )
                # Не нужно возвращать деньги вручную, rollback сделает это за нас
                return None

            # Создаем запись о матче
            bank = stake * 2
            rake_percent = settings.DUEL_RAKE_PERCENT
            cursor = await db.execute(
                "INSERT INTO duel_matches (stake, bank, rake_percent, state) VALUES (?, ?, ?, 'active')",
                (stake, bank, rake_percent),
            )
            match_id = cursor.lastrowid
            if not match_id:
                raise aiosqlite.Error("Failed to create duel match entry.")

            # Добавляем игроков в матч
            await db.execute(
                "INSERT INTO duel_players (match_id, user_id, role) VALUES (?, ?, 'p1'), (?, ?, 'p2')",
                (match_id, p1_id, match_id, p2_id),
            )

            await db.commit()
            return match_id
        except Exception:
            await db.rollback()
            logging.error(
                f"Atomic duel creation failed for users {p1_id} and {p2_id}",
                exc_info=True,
            )
            return None


async def update_duel_stats(winner_id: int, loser_id: int):
    """Обновляет статистику дуэлей для победителя и проигравшего."""
    async with connect() as db:
        await db.execute(
            "UPDATE users SET duel_wins = duel_wins + 1 WHERE user_id = ?", (winner_id,)
        )
        await db.execute(
            "UPDATE users SET duel_losses = duel_losses + 1 WHERE user_id = ?",
            (loser_id,),
        )
        await db.commit()


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
                await _change_balance(db, winner_id, prize, "duel_win", str(match_id))
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
        except Exception:
            await db.rollback()
            logging.error("Ошибка в транзакции finish_duel", exc_info=True)


async def create_timer_match(
    p1_id: int, p2_id: int, stake: int
) -> tuple[Optional[int], Optional[float]]:
    """Создает таймер-матч, списывая ставки с обоих игроков в одной транзакции."""
    async with connect() as db:
        try:
            await _begin_transaction(db)

            p1_success = await _change_balance(db, p1_id, -stake, "timer_stake_hold")
            p2_success = await _change_balance(db, p2_id, -stake, "timer_stake_hold")

            if not p1_success or not p2_success:
                await (
                    db.rollback()
                )  # Откатываем транзакцию, средства вернутся автоматически
                return None, None

            bank = stake * 2
            stop_second = secrets.SystemRandom().uniform(2.5, 7.0)
            cur = await db.execute(
                "INSERT INTO timer_matches (stake, bank, stop_second, state) VALUES (?, ?, ?, 'active')",
                (stake, bank, stop_second),
            )
            match_id = cur.lastrowid
            if match_id:
                await db.execute(
                    "INSERT INTO timer_players (match_id, user_id, role) VALUES (?, ?, 'p1'), (?, ?, 'p2')",
                    (match_id, p1_id, match_id, p2_id),
                )
            await db.commit()
            return match_id, stop_second
        except Exception:
            await db.rollback()
            logging.error("create_timer_match TX error", exc_info=True)
            return None, None


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
                await db.rollback()
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
                prize = (stake * 2) - int(
                    (stake * 2) * (settings.DUEL_RAKE_PERCENT / 100)
                )
                await _change_balance(db, winner_id, prize, "timer_win", str(match_id))
                await db.execute(
                    "UPDATE timer_matches SET state = 'finished', winner_id = ? WHERE id = ?",
                    (winner_id, match_id),
                )
                await db.execute(
                    "UPDATE timer_players SET is_winner = 1 WHERE match_id = ? AND user_id = ?",
                    (match_id, winner_id),
                )
            await db.commit()
        except Exception:
            await db.rollback()
            logging.error("Ошибка в транзакции finish_timer_match", exc_info=True)


async def get_user_duel_stats(user_id: int):
    async with connect() as db:
        cursor = await db.execute(
            "SELECT duel_wins, duel_losses FROM users WHERE user_id = ?", (user_id,)
        )
        stats = await cursor.fetchone()
        return (
            {"wins": stats["duel_wins"], "losses": stats["duel_losses"]}
            if stats
            else {"wins": 0, "losses": 0}
        )


async def get_all_active_duels():
    async with connect() as db:
        cursor = await db.execute("SELECT id FROM duel_matches WHERE state = 'active'")
        return [row[0] for row in await cursor.fetchall()]


async def interrupt_duel(match_id: int):
    async with connect() as db:
        await db.execute(
            "UPDATE duel_matches SET state = 'interrupted' WHERE id = ?", (match_id,)
        )
        await db.commit()


async def get_all_active_timers():
    async with connect() as db:
        cursor = await db.execute("SELECT id FROM timer_matches WHERE state = 'active'")
        return [row[0] for row in await cursor.fetchall()]


async def interrupt_timer_match(match_id: int):
    async with connect() as db:
        await db.execute(
            "UPDATE timer_matches SET state = 'interrupted' WHERE id = ?", (match_id,)
        )
        await db.commit()


async def get_all_users() -> List[int]:
    """Возвращает список всех ID пользователей."""
    async with connect() as db:
        cursor = await db.execute("SELECT user_id FROM users")
        return [row[0] for row in await cursor.fetchall()]


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


async def get_users_for_notification() -> List[int]:
    """
    Возвращает ID пользователей, которые не забирали
    ежедневный бонус более 24 часов.
    """
    async with connect() as db:
        day_ago = int(time.time()) - 86400  # 24 часа в секундах
        cursor = await db.execute(
            "SELECT user_id FROM users WHERE last_bonus_time < ?",
            (day_ago,),
        )
        return [row[0] for row in await cursor.fetchall()]


async def get_all_achievements():
    async with connect() as db:
        cursor = await db.execute(
            "SELECT id, name FROM achievements ORDER BY rarity, name"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


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
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_bot_statistics() -> Dict[str, int]:
    """Собирает общую статистику по боту."""
    async with connect() as db:
        cursor = await db.execute("SELECT COUNT(user_id) FROM users")
        total_users = (await cursor.fetchone())[0]

        today_start = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_start_ts = int(today_start.timestamp())

        cursor = await db.execute(
            "SELECT COUNT(user_id) FROM users WHERE registration_date >= ?",
            (today_start_ts,),
        )
        new_today = (await cursor.fetchone())[0]

        week_ago_ts = int((today_start - datetime.timedelta(days=7)).timestamp())
        cursor = await db.execute(
            "SELECT COUNT(user_id) FROM users WHERE registration_date >= ?",
            (week_ago_ts,),
        )
        new_week = (await cursor.fetchone())[0]

        day_ago_ts = int((today_start - datetime.timedelta(days=1)).timestamp())
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
        except Exception:
            await db.rollback()
            logging.error("Failed to approve reward", exc_info=True)
            return False


async def reject_reward(reward_id: int, admin_id: int, notes: str) -> bool:
    """Rejects a request and returns the stars to the user."""
    async with connect() as db:
        try:
            await db.execute("BEGIN IMMEDIATE;")
            cursor = await db.execute(
                "SELECT user_id, stars_cost, status FROM rewards WHERE id = ?",
                (reward_id,),
            )
            reward_data = await cursor.fetchone()
            if not reward_data or reward_data["status"] != "pending":
                await db.rollback()
                return False

            user_id = reward_data["user_id"]
            stars_cost = reward_data["stars_cost"]

            await _change_balance(
                db, user_id, stars_cost, "reward_revert", str(reward_id)
            )
            await _update_reward_status(db, reward_id, "rejected", admin_id, notes)

            await db.commit()
            return True
        except Exception:
            await db.rollback()
            logging.error("Failed to reject reward", exc_info=True)
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
        except Exception:
            await db.rollback()
            logging.error("Failed to fulfill reward", exc_info=True)
            return False


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
