# handlers/user_handlers.py
import html
import os

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InputMediaPhoto, Message

from config import (ADMIN_IDS, CHANNEL_ID, PHOTO_EARN_STARS, PHOTO_PROFILE,
                    PHOTO_PROMO, PHOTO_TOP, PHOTO_WITHDRAW)
from database import db
from handlers.menu_handler import show_main_menu
from handlers.utils import clean_junk_message
from keyboards.inline import (back_to_main_menu_keyboard, earn_menu_keyboard,
                              main_reply_keyboard, withdraw_menu)
from lexicon.texts import LEXICON

router = Router()


class PromoCode(StatesGroup):
    waiting_for_code = State()


async def check_subscription(user_id: int, bot: Bot):
    """Проверяет подписку пользователя на канал."""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Ошибка проверки подписки: {e}")
        return False


@router.message(CommandStart())
async def start_handler(
    message: Message, command: CommandObject, bot: Bot, state: FSMContext
):
    await message.answer("Добро пожаловать!", reply_markup=main_reply_keyboard())

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
        await db.grant_achievement(user_id, "first_steps", bot)

        flag_file = "compensation_sent.flag"
        if not os.path.exists(flag_file):
            await db.add_stars(user_id, 2)
            await message.answer(
                "Извините за технические неполадки 😔\n\n"
                "Ошибки исправлены, и всем выдана компенсация <b>+2 ⭐</b>.\n\n"
                "(Для получения звёзд, которые вам не начислили ранее, напишите в техподдержку с точным количеством и подтверждением). Спасибо за понимание!"
            )

        if referrer_id:
            try:
                await bot.send_message(
                    referrer_id,
                    "По вашей ссылке зарегистрировался новый пользователь! +5 ⭐",
                )

                ref_count = await db.get_referrals_count(referrer_id)
                ach_map = {
                    1: "first_referral",
                    5: "friendly",
                    15: "social",
                    50: "legend",
                }
                if ref_count in ach_map:
                    await db.grant_achievement(referrer_id, ach_map[ref_count], bot)
            except Exception as e:
                print(f"Не удалось уведомить реферера {referrer_id}: {e}")

    await show_main_menu(bot, chat_id=message.chat.id, user_id=user_id)


@router.message(F.text == "🏠 Меню")
async def main_menu_handler(message: Message, bot: Bot, state: FSMContext):
    await message.delete()
    # Пассивная проверка на напоминание о бонусе
    bonus_check = await db.get_daily_bonus(message.from_user.id)
    if bonus_check["status"] == "success":
        # "Потратим" бонус, чтобы не спамить, и отправим напоминание
        await db.get_daily_bonus(message.from_user.id)
        await message.answer(
            "Кстати, твой ежедневный бонус уже доступен! 😉\nНапиши /bonus, чтобы забрать его."
        )

    await show_main_menu(bot, chat_id=message.chat.id, user_id=message.from_user.id)


@router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await clean_junk_message(callback, state)
    await show_main_menu(
        bot,
        chat_id=callback.message.chat.id,
        user_id=callback.from_user.id,
        message_id=callback.message.message_id,
    )


@router.callback_query(F.data == "profile")
async def profile_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await clean_junk_message(callback, state)
    user_id = callback.from_user.id

    ach_result = await db.grant_achievement(user_id, "curious", bot)
    if ach_result:
        await callback.answer(
            "🏆 Новое достижение!\n«Любопытный» (+1 ⭐)", show_alert=True
        )

    balance = await db.get_user_balance(user_id)
    referrals_count = await db.get_referrals_count(user_id)
    stats = await db.get_user_duel_stats(user_id)

    text = LEXICON["profile"].format(
        full_name=html.escape(callback.from_user.full_name),
        user_id=user_id,
        referrals_count=referrals_count,
        duel_wins=stats["wins"],
        duel_losses=stats["losses"],
        balance=balance,
    )
    await callback.message.edit_media(
        media=InputMediaPhoto(media=PHOTO_PROFILE, caption=text),
        reply_markup=back_to_main_menu_keyboard(),
    )


@router.callback_query(F.data == "earn")
async def earn_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await clean_junk_message(callback, state)
    bot_info = await bot.get_me()
    user_id = callback.from_user.id
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    invited_count = await db.get_referrals_count(user_id)

    text = LEXICON["earn_menu"].format(ref_link=ref_link, invited_count=invited_count)
    await callback.message.edit_media(
        media=InputMediaPhoto(media=PHOTO_EARN_STARS, caption=text),
        reply_markup=earn_menu_keyboard(),
    )


@router.callback_query(F.data == "top")
async def top_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await clean_junk_message(callback, state)
    top_users = await db.get_top_referrers(5)

    top_users_text = ""
    if not top_users:
        top_users_text = "Пока никто никого не пригласил."
    else:
        for i, (user_id, ref_count) in enumerate(top_users, start=1):
            try:
                user = await bot.get_chat(user_id)
                username = html.escape(
                    f"@{user.username}" if user.username else user.full_name
                )
                top_users_text += f"{i}. {username} — {ref_count} приглашений\n"
            except Exception:
                top_users_text += f"{i}. Пользователь <code>{user_id}</code> — {ref_count} приглашений\n"

    text = LEXICON["top_menu"].format(top_users_text=top_users_text)
    await callback.message.edit_media(
        media=InputMediaPhoto(media=PHOTO_TOP, caption=text),
        reply_markup=back_to_main_menu_keyboard(),
    )


@router.callback_query(F.data == "withdraw")
async def withdraw_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await clean_junk_message(callback, state)
    balance = await db.get_user_balance(callback.from_user.id)
    referrals_count = await db.get_referrals_count(callback.from_user.id)

    text = LEXICON["withdraw_menu"].format(
        balance=balance, referrals_count=referrals_count
    )
    await callback.message.edit_media(
        media=InputMediaPhoto(media=PHOTO_WITHDRAW, caption=text),
        reply_markup=withdraw_menu(),
    )


@router.callback_query(F.data.startswith("gift_"))
async def withdraw_gift_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await clean_junk_message(callback, state)
    user_id = callback.from_user.id

    if not await check_subscription(user_id, bot):
        await callback.answer(
            "Для вывода необходимо быть подписанным на наш канал!", show_alert=True
        )
        return

    try:
        cost = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer("Ошибка в данных о подарке.", show_alert=True)
        return

    referrals_count = await db.get_referrals_count(user_id)
    if referrals_count < 5:
        await callback.answer(
            f"Для вывода нужно пригласить минимум 5 друзей (у вас {referrals_count}).",
            show_alert=True,
        )
        return

    ok = await db.update_user_balance(user_id, -cost)
    if not ok:
        balance = await db.get_user_balance(user_id)
        await callback.answer(
            f"У вас недостаточно звёзд. Нужно {cost} ⭐, а у вас {balance} ⭐.",
            show_alert=True,
        )
        return

    gift_text = "Неизвестный подарок"
    for row in callback.message.reply_markup.inline_keyboard:
        for button in row:
            if button.callback_data == callback.data:
                gift_text = button.text
                break

    balance_after = await db.get_user_balance(user_id)
    for admin_id in ADMIN_IDS:
        try:
            admin_text = (
                f"❗️ Новая заявка на вывод!\n"
                f"Пользователь: @{callback.from_user.username or 'скрыт'} (ID: `{user_id}`)\n"
                f"Хочет получить: {html.escape(gift_text)}\n"
                f"Баланс после списания: {balance_after} ⭐"
            )
            await bot.send_message(admin_id, admin_text)
        except Exception as e:
            print(f"Не удалось отправить уведомление админу {admin_id}: {e}")

    reply = await bot.send_message(user_id, "Вывод принят, с вами свяжутся! 😍")
    await state.update_data(junk_message_id=reply.message_id)
    await callback.answer()


@router.callback_query(F.data == "promo_code")
async def promo_code_start(callback: CallbackQuery, state: FSMContext):
    await clean_junk_message(callback, state)
    await callback.message.edit_media(
        media=InputMediaPhoto(media=PHOTO_PROMO, caption=LEXICON["promo_prompt"]),
        reply_markup=back_to_main_menu_keyboard(),
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

    if isinstance(result, int):
        response_text = f"✅ Промокод успешно активирован! Вам начислено {result} ⭐"
        await message.answer(response_text)

        await db.grant_achievement(user_id, "code_breaker", bot)

        full_info = await db.get_full_user_info(user_id)
        if full_info and len(full_info["activated_codes"]) >= 3:
            await db.grant_achievement(user_id, "promo_master", bot)

    elif result == "not_found":
        response_text = "❌ Такого промокода не существует или его срок действия истёк."
        await message.answer(response_text)
    elif result == "already_activated":
        response_text = "❌ Вы уже активировали этот промокод."
        await message.answer(response_text)

    await message.delete()
