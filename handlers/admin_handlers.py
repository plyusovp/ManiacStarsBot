# handlers/admin_handlers.py
import datetime
import html
import logging
from typing import Any, Optional

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from config import ADMIN_IDS
from database import db

# --- Router & filters ---
router = Router()
# Фильтр: только админы из конфига
router.message.filter(F.from_user.id.in_(ADMIN_IDS))
logger = logging.getLogger(__name__)

# --- Constants ---
REG_DT_FORMAT = "%Y-%m-%d %H:%M:%S"


# --- Helpers ---
async def get_user_id(arg: str) -> Optional[int]:
    """Преобразует аргумент команды в user_id."""
    if not arg:
        return None
    token = arg.strip().split(maxsplit=1)[0]
    if token.isdigit():
        return int(token)

    username = token.replace("@", "").strip()
    if not username:
        return None

    try:
        return await db.get_user_by_username(username)
    except Exception:
        logger.exception("Failed to fetch user_id for username: %s", username)
        return None


def safe_format_ts(ts: Any) -> str:
    """Безопасно форматирует timestamp в строку."""
    try:
        ts_int = int(ts)
        if ts_int <= 0:
            return "неизвестно"
        dt = datetime.datetime.fromtimestamp(ts_int)
        return dt.strftime(REG_DT_FORMAT)
    except (ValueError, TypeError, OSError, OverflowError):
        return "неизвестно"


def _escape_or_na(value: Any, na_text: str = "не указан") -> str:
    """Экранирует значение для HTML. Пустые/None -> 'не указан'."""
    if value is None:
        return na_text
    s = str(value).strip()
    return html.escape(s) if s else na_text


def _format_username(value: Any) -> str:
    """Красиво отображает username."""
    raw = str(value or "").strip().lstrip("@")
    if not raw:
        return "не указан"
    return f"@{html.escape(raw)}"


# --- Handlers ---
@router.message(Command("info"))
async def get_user_info_handler(
    message: Message, command: CommandObject, bot: Bot
) -> None:
    """/info <id|@username> — показать полную информацию о пользователе."""
    if not command.args:
        await message.answer(
            "Пожалуйста, укажите ID или @username пользователя.\n"
            "Пример: `/info 12345678` или `/info @username`"
        )
        return

    user_to_find = await get_user_id(command.args)
    if not user_to_find:
        await message.answer("Пользователь не найден в базе данных.")
        return

    if user_to_find == message.from_user.id:
        await db.grant_achievement(message.from_user.id, "meta", bot)

    try:
        info = await db.get_full_user_info(user_to_find)
    except Exception:
        logger.exception("get_full_user_info failed for user_id: %s", user_to_find)
        await message.answer(
            f"Не удалось получить информацию о пользователе `{user_to_find}`."
        )
        return

    if not info or not info.get("user_data"):
        await message.answer(
            f"Не удалось получить полную информацию о пользователе `{user_to_find}`."
        )
        return

    user_data = info["user_data"]
    invited_users = info.get("invited_users", [])
    activated_codes = info.get("activated_codes", [])

    reg_date = safe_format_ts(user_data[5])
    duel_wins = user_data[7]
    duel_losses = user_data[8]

    text = "\n".join(
        [
            "ℹ️ <b>Полная информация о пользователе:</b>",
            "",
            f"<b>ID:</b> <code>{user_data[0]}</code>",
            f"<b>Username:</b> {_format_username(user_data[1])}",
            f"<b>Full Name:</b> {_escape_or_na(user_data[2])}",
            f"<b>Баланс:</b> {user_data[3]} ⭐",
            "",
            f"<b>Дата регистрации:</b> {reg_date}",
            f"<b>Приглашен от:</b> {_escape_or_na(user_data[4], 'Никто')}",
            "",
            "📊 <b>Статистика:</b>",
            f"- Всего приглашено: {len(invited_users)}",
            f"- Активировано промокодов: {len(activated_codes)}",
            f"- Дуэли (Побед/Поражений): {duel_wins}/{duel_losses}",
        ]
    )
    await message.answer(text)


@router.message(Command("addpromo"))
async def add_promo_handler(message: Message, command: CommandObject) -> None:
    """/addpromo <NAME> <REWARD:int> <USES:int>"""
    if not command.args or len(command.args.split()) != 3:
        await message.answer(
            "Ошибка. Используй формат:\n`/addpromo НАЗВАНИЕ НАГРАДА КОЛИЧЕСТВО`\n"
            "Пример: `/addpromo HELLO5 5 100`"
        )
        return

    name, reward_str, uses_str = command.args.split()
    try:
        reward = int(reward_str)
        uses = int(uses_str)
        if reward <= 0 or uses < 0:
            raise ValueError("Reward and uses must be positive.")
    except ValueError:
        await message.answer(
            "Ошибка. Награда и количество должны быть положительными числами."
        )
        return

    try:
        await db.add_promo_code(name.upper(), reward, uses)
    except Exception:
        logger.exception("add_promo_code failed")
        await message.answer("Не удалось создать промокод из-за ошибки БД.")
        return

    await message.answer(
        f"✅ Промокод <code>{html.escape(name.upper())}</code> "
        f"на {reward} ⭐ ({uses} активаций) успешно создан."
    )


@router.message(Command("addstar"))
async def add_star_handler(message: Message, command: CommandObject) -> None:
    """/addstar <id|@username> <AMOUNT:int>"""
    if not command.args or len(command.args.split()) != 2:
        await message.answer(
            "Ошибка. Используй: `/addstar <ID или @username> <количество>`"
        )
        return

    user_arg, amount_str = command.args.split()
    try:
        user_id = await get_user_id(user_arg)
        if not user_id:
            await message.answer("Пользователь не найден в базе данных.")
            return
        amount = int(amount_str)
    except ValueError:
        await message.answer("Количество звёзд должно быть числом.")
        return
    except Exception:
        logger.exception("Failed to parse args in add_star")
        await message.answer("Ошибка в аргументах.")
        return

    try:
        await db.add_stars(user_id, amount)
    except Exception:
        logger.exception("add_stars failed")
        await message.answer("Не удалось начислить звёзды из-за ошибки БД.")
        return

    await message.answer(f"✅ Пользователю `{user_id}` успешно начислено {amount} ⭐.")


@router.message(Command("addref"))
async def add_ref_handler(message: Message, command: CommandObject) -> None:
    """/addref <id|@username> <AMOUNT:int> - ВРЕМЕННО ОТКЛЮЧЕНО"""
    await message.answer(
        "Эта команда временно отключена, так как `add_refs` небезопасна."
    )


@router.message(Command("activepromo"))
async def active_promo_handler(message: Message) -> None:
    """/activepromo — список активных промокодов."""
    try:
        promos = await db.get_active_promos()
    except Exception:
        logger.exception("get_active_promos failed")
        await message.answer("Не удалось получить список промокодов.")
        return

    if not promos:
        await message.answer("Активных промокодов нет.")
        return

    lines = ["🎟️ <b>Активные промокоды:</b>", ""]
    for code, reward, uses_left, total_uses in promos:
        lines.append(
            f"<code>{html.escape(str(code))}</code> — <b>{reward} ⭐</b> "
            f"(осталось {uses_left}/{total_uses})"
        )
    await message.answer("\n".join(lines))
