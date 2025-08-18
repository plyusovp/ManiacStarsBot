# handlers/user_handlers.py
import asyncio
import os
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from keyboards.inline import (
    main_menu, back_to_main_menu_keyboard, withdraw_menu, main_reply_keyboard
)
from config import *
import database.db as db
from handlers.menu_handler import show_main_menu
from .utils import clean_junk_message # 🔥 Импортируем из нового файла

router = Router()

class PromoCode(StatesGroup):
    waiting_for_code = State()

async def check_subscription(user_id: int, bot: Bot):
    """Проверяет подписку пользователя на канал."""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Ошибка проверки подписки: {e}")
        return False

@router.message(CommandStart())
async def start_handler(message: Message, command: CommandObject, bot: Bot):
    await message.answer(
        "Добро пожаловать!",
        reply_markup=main_reply_keyboard()
    )

    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name
    
    referrer_id = command.args
    if referrer_id and referrer_id.isdigit() and int(referrer_id) != user_id:
        referrer_id = int(referrer_id)
    else:
        referrer_id = None

    is_new = await db.add_user(user_id, username, full_name, referrer_id)

    if is_new:
        await db.grant_achievement(user_id, 'first_steps', bot)
        
        flag_file = 'compensation_sent.flag'
        if not os.path.exists(flag_file):
            await db.add_stars(user_id, 2)
            await message.answer(
                "Извините за технические неполадки 😔\n\n"
                "Ошибки исправлены, и всем выдана компенсация <b>+2 ⭐</b>.\n\n"
                "(Для получения звёзд, которые вам не начислили ранее, напишите в техподдержку с точным количеством и подтверждением). Спасибо за понимание!"
            )

        if referrer_id:
            try:
                await bot.send_message(referrer_id, f"По вашей ссылке зарегистрировался новый пользователь! +5 ⭐")
                
                ref_count = await db.get_referrals_count(referrer_id)
                if ref_count == 1:
                    await db.grant_achievement(referrer_id, 'first_referral', bot)
                elif ref_count == 5:
                    await db.grant_achievement(referrer_id, 'friendly', bot)
                elif ref_count == 15:
                    await db.grant_achievement(referrer_id, 'social', bot)
                elif ref_count == 50:
                    await db.grant_achievement(referrer_id, 'legend', bot)
            except Exception as e:
                print(f"Не удалось уведомить реферера {referrer_id}: {e}")

    await show_main_menu(bot, chat_id=message.chat.id, user_id=user_id)

@router.message(F.text == "🏠 Меню")
async def main_menu_handler(message: Message, bot: Bot):
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
    await show_main_menu(bot, chat_id=message.chat.id, user_id=message.from_user.id)


@router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await clean_junk_message(callback, state)
    
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    await show_main_menu(bot, chat_id=callback.message.chat.id, user_id=callback.from_user.id)


@router.callback_query(F.data == "profile")
async def profile_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await clean_junk_message(callback, state)
    await db.grant_achievement(callback.from_user.id, 'curious', bot)
    
    balance = await db.get_user_balance(callback.from_user.id)
    referrals_count = await db.get_referrals_count(callback.from_user.id)
    stats = await db.get_user_duel_stats(callback.from_user.id)

    text = f"""
🔥 <b>Профиль</b> 🔥

👤 <b>Имя:</b> {callback.from_user.full_name}
🔑 <b>ID:</b> <code>{callback.from_user.id}</code>

📄 <b>Статистика</b> 📄
- <b>Приглашено друзей:</b> {referrals_count}
- <b>Дуэли (Побед/Поражений):</b> {stats['wins']}/{stats['losses']}
- <b>Баланс:</b> {balance} ⭐
"""
    await callback.message.edit_media(media=InputMediaPhoto(media=PHOTO_PROFILE, caption=text), reply_markup=back_to_main_menu_keyboard())


@router.callback_query(F.data == "earn")
async def earn_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await clean_junk_message(callback, state)
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={callback.from_user.id}"
    invited_count = await db.get_referrals_count(callback.from_user.id)

    text = f"""
⭐ <b>Приглашай пользователей в бота и получай по 5 ЗВЁЗД за каждого!</b>

🔗 <b>Ваша ссылка:</b> <code>{ref_link}</code>

🤝 <b>Как использовать ссылку?</b>
<a href="https://t.me/+_DDj9YbIEOljNzU0">Мануал вы найдете здесь</a>

🔑 <b>Вы пригласили:</b> {invited_count}
"""
    await callback.message.edit_media(media=InputMediaPhoto(media=PHOTO_EARN_STARS, caption=text), reply_markup=back_to_main_menu_keyboard())


@router.callback_query(F.data == "top")
async def top_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await clean_junk_message(callback, state)
    top_users = await db.get_top_referrers(5)
    
    text = "🏆 <b>Топ-5 пользователей по приглашениям:</b>\n\n"
    if not top_users:
        text += "Пока никто никого не пригласил."
    else:
        for i, (user_id, ref_count) in enumerate(top_users, start=1):
            try:
                user = await bot.get_chat(user_id)
                username = f"@{user.username}" if user.username else user.full_name
                text += f"{i}. {username} — {ref_count} приглашений\n"
            except Exception:
                text += f"{i}. Пользователь <code>{user_id}</code> — {ref_count} приглашений\n"
    
    await callback.message.edit_media(media=InputMediaPhoto(media=PHOTO_TOP, caption=text), reply_markup=back_to_main_menu_keyboard())


@router.callback_query(F.data == "withdraw")
async def withdraw_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await clean_junk_message(callback, state)
    balance = await db.get_user_balance(callback.from_user.id)
    referrals_count = await db.get_referrals_count(callback.from_user.id)

    text = f"""
💵 <b>Баланс:</b> {balance} ⭐

‼️ <b>Для вывода требуется:</b>
— Минимум 5 приглашённых друзей (у вас {referrals_count})
— Быть подписанным на <a href="https://t.me/+Hu5bVLrGpRpiMTBk">наш канал</a>

<b>Выберите подарок:</b>
"""
    await callback.message.edit_media(media=InputMediaPhoto(media=PHOTO_WITHDRAW, caption=text), reply_markup=withdraw_menu())


@router.callback_query(F.data.startswith("gift_"))
async def withdraw_gift_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await clean_junk_message(callback, state)
    user_id = callback.from_user.id
    
    if not await check_subscription(user_id, bot):
        await callback.answer("Для вывода необходимо быть подписанным на наш канал!", show_alert=True)
        return
        
    try:
        cost = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer("Ошибка в данных о подарке.", show_alert=True)
        return

    balance = await db.get_user_balance(user_id)
    referrals_count = await db.get_referrals_count(user_id)

    if referrals_count < 5:
        await callback.answer(f"Для вывода нужно пригласить минимум 5 друзей (у вас {referrals_count}).", show_alert=True)
        return
    if balance < cost:
        await callback.answer(f"У вас недостаточно звёзд. Нужно {cost} ⭐, а у вас {balance} ⭐.", show_alert=True)
        return

    await db.update_user_balance(user_id, -cost)
    
    gift_text = "Неизвестный подарок"
    for row in callback.message.reply_markup.inline_keyboard:
        for button in row:
            if button.callback_data == callback.data:
                gift_text = button.text
                break

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, f"❗️ Новая заявка на вывод!\nПользователь: @{callback.from_user.username or 'скрыт'} (ID: `{user_id}`)\nХочет получить: {gift_text}\nБаланс после списания: {balance - cost} ⭐")
        except Exception as e:
            print(f"Не удалось отправить уведомление админу {admin_id}: {e}")
    
    reply = await bot.send_message(user_id, "Вывод принят, с вами свяжутся! 😍")
    await state.update_data(junk_message_id=reply.message_id)
    await callback.answer()


@router.callback_query(F.data == "promo_code")
async def promo_code_start(callback: CallbackQuery, state: FSMContext):
    await clean_junk_message(callback, state)
    await callback.message.edit_media(
        media=InputMediaPhoto(media=PHOTO_PROMO, caption="<b>Введите ваш промокод:</b>"),
        reply_markup=back_to_main_menu_keyboard()
    )
    await state.set_state(PromoCode.waiting_for_code)


@router.message(PromoCode.waiting_for_code)
async def process_promo_code(message: Message, state: FSMContext, bot: Bot):
    try:
        await bot.delete_message(message.chat.id, message.message_id - 1)
    except TelegramBadRequest:
        pass
        
    await state.clear()
    code = message.text.strip().upper()
    user_id = message.from_user.id
    
    result = await db.activate_promo(user_id, code)
    response_text = ""
    if isinstance(result, int):
        response_text = f"✅ Промокод успешно активирован! Вам начислено {result} ⭐"
        await db.grant_achievement(user_id, 'code_breaker', bot)
        
        full_info = await db.get_full_user_info(user_id)
        if full_info and len(full_info['activated_codes']) == 3:
            await db.grant_achievement(user_id, 'promo_master', bot)
            
    elif result == "not_found":
        response_text = "❌ Такого промокода не существует или его срок действия истёк."
    elif result == "already_activated":
        response_text = "❌ Вы уже активировали этот промокод."

    reply = await message.answer(response_text)
    await state.update_data(junk_message_id=reply.message_id)
    
    await message.delete()