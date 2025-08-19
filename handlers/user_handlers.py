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
    main_menu, back_to_main_menu_keyboard, withdraw_menu, main_reply_keyboard,
    earn_menu_keyboard
)
from config import *
import database.db as db
from handlers.menu_handler import show_main_menu
from .utils import clean_junk_message
from texts.texts import LEXICON

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
async def start_handler(message: Message, command: CommandObject, bot: Bot, state: FSMContext):
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
        ach_result = await db.grant_achievement(user_id, 'first_steps')
        if ach_result['granted']:
            # Всплывающее уведомление здесь невозможно, поэтому отправляем обычное сообщение
            reply = await message.answer(ach_result['text'])
            await state.update_data(junk_message_id=reply.message_id)

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
                if ref_count in [1, 5, 15, 50]: # Проверяем сразу несколько порогов
                    ach_map = {1: 'first_referral', 5: 'friendly', 15: 'social', 50: 'legend'}
                    ach_result_ref = await db.grant_achievement(referrer_id, ach_map[ref_count])
                    if ach_result_ref['granted']:
                         await bot.send_message(referrer_id, ach_result_ref['text'])
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
    await show_main_menu(bot, chat_id=callback.message.chat.id, user_id=callback.from_user.id, message_id=callback.message.message_id)


@router.callback_query(F.data == "profile")
async def profile_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await clean_junk_message(callback, state)
    user_id = callback.from_user.id
    
    ach_result = await db.grant_achievement(user_id, 'curious')
    if ach_result['granted']:
        await callback.answer(ach_result['text'], show_alert=True)
    
    balance = await db.get_user_balance(user_id)
    referrals_count = await db.get_referrals_count(user_id)
    stats = await db.get_user_duel_stats(user_id)

    text = LEXICON['profile'].format(
        full_name=callback.from_user.full_name,
        user_id=user_id,
        referrals_count=referrals_count,
        duel_wins=stats['wins'],
        duel_losses=stats['losses'],
        balance=balance
    )
    await callback.message.edit_media(media=InputMediaPhoto(media=PHOTO_PROFILE, caption=text), reply_markup=back_to_main_menu_keyboard())


@router.callback_query(F.data == "earn")
async def earn_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await clean_junk_message(callback, state)
    bot_info = await bot.get_me()
    user_id = callback.from_user.id
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    invited_count = await db.get_referrals_count(user_id)

    text = LEXICON['earn_menu'].format(
        ref_link=ref_link,
        invited_count=invited_count
    )
    await callback.message.edit_media(media=InputMediaPhoto(media=PHOTO_EARN_STARS, caption=text), reply_markup=earn_menu_keyboard())


@router.callback_query(F.data == "top")
async def top_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await clean_junk_message(callback, state)
    top_users = await db.get_top_referrers(5)
    
    text = LEXICON['top_menu']
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

    text = LEXICON['withdraw_menu'].format(
        balance=balance,
        referrals_count=referrals_count
    )
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
        media=InputMediaPhoto(media=PHOTO_PROMO, caption=LEXICON['promo_prompt']),
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
    notifications = []

    if isinstance(result, int):
        response_text = f"✅ Промокод успешно активирован! Вам начислено {result} ⭐"
        
        ach_result = await db.grant_achievement(user_id, 'code_breaker')
        if ach_result['granted']:
            notifications.append(ach_result['text'])

        full_info = await db.get_full_user_info(user_id)
        if full_info and len(full_info['activated_codes']) == 3:
            ach_result_master = await db.grant_achievement(user_id, 'promo_master')
            if ach_result_master['granted']:
                notifications.append(ach_result_master['text'])
            
    elif result == "not_found":
        response_text = "❌ Такого промокода не существует или его срок действия истёк."
    elif result == "already_activated":
        response_text = "❌ Вы уже активировали этот промокод."

    # Соединяем все уведомления в одно сообщение
    final_response = response_text
    if notifications:
        final_response += "\n\n" + "\n".join(notifications)

    reply = await message.answer(final_response)
    await state.update_data(junk_message_id=reply.message_id)
    
    await message.delete()