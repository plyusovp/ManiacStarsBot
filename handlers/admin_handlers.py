# handlers/admin_handlers.py
import datetime
import time
import random
from typing import Union
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command, CommandObject

from config import ADMIN_IDS
import database.db as db

router = Router()
# Этот фильтр будет проверять, является ли пользователь админом, для всех команд в этом файле
router.message.filter(F.from_user.id.in_(ADMIN_IDS))

async def get_user_id(arg: str) -> Union[int, None]:
    """Вспомогательная функция для получения ID по юзернейму или ID."""
    if arg.isdigit():
        return int(arg)
    else:
        username = arg.replace('@', '').strip()
        return await db.get_user_by_username(username)

@router.message(Command("info"))
async def get_user_info_handler(message: Message, command: CommandObject, bot: Bot):
    if not command.args:
        await message.answer("Пожалуйста, укажите ID или @username пользователя. \nПример: `/info 12345678` или `/info @username`")
        return

    user_to_find = await get_user_id(command.args)
    if not user_to_find:
        await message.answer("Пользователь не найден в базе данных.")
        return
        
    # Выдаём секретную ачивку, если админ проверяет сам себя
    if user_to_find == message.from_user.id:
        await db.grant_achievement(message.from_user.id, 'meta', bot)
        
    info = await db.get_full_user_info(user_to_find)
    if not info:
        await message.answer(f"Не удалось получить полную информацию о пользователе с ID `{user_to_find}`.")
        return

    user_data, invited_users, activated_codes = info.values()
    
    reg_date = datetime.datetime.fromtimestamp(user_data[5]).strftime('%Y-%m-%d %H:%M:%S')
    
    duel_wins = user_data[7]
    duel_losses = user_data[8]

    text = f"""
ℹ️ <b>Полная информация о пользователе:</b>

<b>ID:</b> <code>{user_data[0]}</code>
<b>Username:</b> @{user_data[1] or 'не указан'}
<b>Full Name:</b> {user_data[2]}
<b>Баланс:</b> {user_data[3]} ⭐

<b>Дата регистрации:</b> {reg_date}
<b>Приглашен от:</b> {user_data[4] if user_data[4] else 'Никто'}

📊 <b>Статистика:</b>
- Всего приглашено: {len(invited_users)}
- Активировано промокодов: {len(activated_codes)}
- Дуэли (Побед/Поражений): {duel_wins}/{duel_losses}

<b>Пригласил пользователей:</b>
<code>{', '.join(map(str, invited_users)) if invited_users else 'Никого'}</code>

<b>Активированные промокоды:</b>
<code>{', '.join(activated_codes) if activated_codes else 'Нет'}</code>
"""
    await message.answer(text)


@router.message(Command("addpromo"))
async def add_promo_handler(message: Message, command: CommandObject):
    if not command.args or len(command.args.split()) != 3:
        await message.answer(
            "Ошибка. Используй формат: \n`/addpromo НАЗВАНИЕ НАГРАДА КОЛИЧЕСТВО`\n\n"
            "Пример: `/addpromo HELLO5 5 100`"
        )
        return

    try:
        name, reward_str, uses_str = command.args.split()
        reward = int(reward_str)
        uses = int(uses_str)
    except ValueError:
        await message.answer(
            "Ошибка в аргументах. Награда и количество должны быть числами.\n"
            "Пример: `/addpromo HELLO5 5 100`"
        )
        return

    await db.add_promo_code(name.upper(), reward, uses)
    await message.answer(f"✅ Промокод <code>{name.upper()}</code> на {reward} ⭐ ({uses} активаций) успешно создан.")


@router.message(Command("addstar"))
async def add_star_handler(message: Message, command: CommandObject):
    if not command.args or len(command.args.split()) != 2:
        await message.answer("Ошибка. Используй: `/addstar <ID или @username> <количество>`")
        return
    
    user_arg, amount_str = command.args.split()
    user_id = await get_user_id(user_arg)
    
    if not user_id:
        await message.answer("Пользователь не найден в базе данных.")
        return
    
    try:
        amount = int(amount_str)
        await db.add_stars(user_id, amount)
        await message.answer(f"✅ Пользователю `{user_id}` успешно начислено {amount} ⭐.")
    except ValueError:
        await message.answer("Количество звёзд должно быть числом.")

@router.message(Command("addref"))
async def add_ref_handler(message: Message, command: CommandObject):
    if not command.args or len(command.args.split()) != 2:
        await message.answer("Ошибка. Используй: `/addref <ID или @username> <количество>`")
        return

    user_arg, amount_str = command.args.split()
    user_id = await get_user_id(user_arg)

    if not user_id:
        await message.answer("Пользователь не найден в базе данных.")
        return
    
    try:
        amount = int(amount_str)
        await db.add_refs(user_id, amount)
        await message.answer(f"✅ Пользователю `{user_id}` успешно добавлено {amount} рефералов.")
    except ValueError:
        await message.answer("Количество рефералов должно быть числом.")

@router.message(Command("activepromo"))
async def active_promo_handler(message: Message):
    promos = await db.get_active_promos()
    if not promos:
        await message.answer("Активных промокодов нет.")
        return
    
    text = "🎟️ <b>Активные промокоды:</b>\n\n"
    for code, reward, uses_left, total_uses in promos:
        text += f"<code>{code}</code> — <b>{reward} ⭐</b> (осталось {uses_left}/{total_uses})\n"
        
    await message.answer(text)