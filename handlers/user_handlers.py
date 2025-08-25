# handlers/user_handlers.py
import datetime
import html
import os
import time

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InputMediaPhoto, Message

from config import settings
from database import db
from economy import (BIG_EARN_THRESHOLD, NEW_USER_QUARANTINE_HOURS,
                     WITHDRAW_COOLDOWN_HOURS)
from handlers.menu_handler import show_main_menu
from handlers.utils import (clean_junk_message, generate_signed_payload,
                            verify_signed_payload)
# --- ИЗМЕНЕНО: Убран некорректный импорт main_reply_keyboard ---
from keyboards.inline import (back_to_main_menu_keyboard, earn_menu_keyboard,
                              withdraw_menu)
from lexicon.texts import ECONOMY_ERROR_MESSAGES, LEXICON

router = Router()


class PromoCode(StatesGroup):
    waiting_for_code = State()


async def check_subscription(user_id: int, bot: Bot):
    """Проверяет подписку пользователя на канал."""
    try:
        member = await bot.get_chat_member(chat_id=settings.CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Ошибка проверки подписки: {e}")
        return False


@router.message(CommandStart())
async def start_handler(
    message: Message, command: CommandObject, bot: Bot, state: FSMContext
):
    # --- ИЗМЕНЕНО: Удалена отправка лишнего сообщения, которое все ломало ---
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    referrer_id = None
    if command.args:
        payload = verify_signed_payload(command.args, settings.REFERRAL_LINK_TTL_HOURS)
        if payload and 'ref' in payload and payload['ref'] != user_id:
            referrer_id = int(payload['ref'])

    is_new = await db.add_user(user_id, username, full_name, referrer_id)

    if is_new:
        await db.grant_achievement(user_id, "first_steps", bot)

        flag_file = "compensation_sent.flag"
        if not os.path.exists(flag_file):
            await db.add_balance_unrestricted(user_id, 2, "compensation")
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

    # Сразу показываем правильное главное меню
    await show_main_menu(bot, chat_id=message.chat.id, user_id=user_id)


@router.message(F.text == "🏠 Меню")
async def main_menu_handler(message: Message, bot: Bot, state: FSMContext):
    await message.delete()
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

    await db.grant_achievement(user_id, "curious", bot)

    info = await db.get_full_user_info(user_id)
    if not info:
        return await callback.answer("Не удалось загрузить профиль.")

    user_data = info["user_data"]
    balance = user_data.get("balance", 0)
    referrals_count = await db.get_referrals_count(user_id)
    stats = await db.get_user_duel_stats(user_id)

    status_text = ""
    quarantine_status = ""
    cooldown_status = ""

    reg_ts = user_data.get("registration_date", 0)
    if time.time() - reg_ts < NEW_USER_QUARANTINE_HOURS * 3600:
        quarantine_status = "🔹 На вашем аккаунте действует карантин новичка (24ч). Вывод временно ограничен.\n"

    last_big_earn_str = user_data.get("last_big_earn")
    if last_big_earn_str:
        last_big_earn_dt = datetime.datetime.fromisoformat(last_big_earn_str)
        cooldown_end = last_big_earn_dt + datetime.timedelta(hours=WITHDRAW_COOLDOWN_HOURS)
        if datetime.datetime.now() < cooldown_end:
            remaining = cooldown_end - datetime.datetime.now()
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            cooldown_status = f"🔹 Ваш вывод на кулдауне после крупного выигрыша. Осталось: {hours}ч {minutes}м.\n"

    if quarantine_status or cooldown_status:
        status_text = LEXICON["profile_status"].format(
            quarantine_status=quarantine_status,
            cooldown_status=cooldown_status
        )

    text = LEXICON["profile"].format(
        full_name=html.escape(callback.from_user.full_name),
        user_id=user_id,
        referrals_count=referrals_count,
        duel_wins=stats["wins"],
        duel_losses=stats["losses"],
        balance=balance,
        status_text=status_text
    )
    await callback.message.edit_media(
        media=InputMediaPhoto(media=settings.PHOTO_PROFILE, caption=text),
        reply_markup=back_to_main_menu_keyboard(),
    )


@router.callback_query(F.data == "earn")
async def earn_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await clean_junk_message(callback, state)
    bot_info = await bot.get_me()
    user_id = callback.from_user.id
    
    payload_data = {"ref": user_id}
    signed_payload = generate_signed_payload(payload_data)
    ref_link = f"https://t.me/{bot_info.username}?start={signed_payload}"
    
    invited_count = await db.get_referrals_count(user_id)

    text = LEXICON["earn_menu"].format(ref_link=ref_link, invited_count=invited_count)
    await callback.message.edit_media(
        media=InputMediaPhoto(media=settings.PHOTO_EARN_STARS, caption=text),
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
        media=InputMediaPhoto(media=settings.PHOTO_TOP, caption=text),
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
        media=InputMediaPhoto(media=settings.PHOTO_WITHDRAW, caption=text),
        reply_markup=withdraw_menu(),
    )


@router.callback_query(F.data.startswith("gift_"))
async def withdraw_gift_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await clean_junk_message(callback, state)
    user_id = callback.from_user.id

    if not settings.REWARDS_ENABLED:
        return await callback.answer(ECONOMY_ERROR_MESSAGES['rewards_disabled'], show_alert=True)

    user_info = await db.get_full_user_info(user_id)
    if not user_info:
        return await callback.answer("Ошибка получения данных пользователя.", show_alert=True)
    
    user_data = user_info['user_data']
    reg_ts = user_data.get("registration_date", 0)
    if time.time() - reg_ts < NEW_USER_QUARANTINE_HOURS * 3600:
        return await callback.answer(ECONOMY_ERROR_MESSAGES['user_in_quarantine'], show_alert=True)

    last_big_earn_str = user_data.get("last_big_earn")
    if last_big_earn_str:
        last_big_earn_dt = datetime.datetime.fromisoformat(last_big_earn_str)
        cooldown_end = last_big_earn_dt + datetime.timedelta(hours=WITHDRAW_COOLDOWN_HOURS)
        if datetime.datetime.now() < cooldown_end:
            remaining = cooldown_end - datetime.datetime.now()
            hours, rem = divmod(int(remaining.total_seconds()), 3600)
            minutes, _ = divmod(rem, 60)
            return await callback.answer(
                ECONOMY_ERROR_MESSAGES['withdraw_cooldown'].format(hours=hours, minutes=minutes),
                show_alert=True
            )

    if not await check_subscription(user_id, bot):
        return await callback.answer(
            "Для вывода необходимо быть подписанным на наш канал!", show_alert=True
        )

    try:
        cost = int(callback.data.split("_")[1])
        item_id = callback.data
    except (ValueError, IndexError):
        return await callback.answer("Ошибка в данных о подарке.", show_alert=True)

    referrals_count = await db.get_referrals_count(user_id)
    if referrals_count < 5:
        return await callback.answer(
            f"Для вывода нужно пригласить минимум 5 друзей (у вас {referrals_count}).",
            show_alert=True,
        )

    result = await db.create_reward_request(user_id, item_id, cost, idem_key=callback.id)
    if not result.get("success"):
        reason = result.get("reason", "unknown_error")
        error_message = ECONOMY_ERROR_MESSAGES.get(reason, ECONOMY_ERROR_MESSAGES["unknown_error"])
        return await callback.answer(error_message, show_alert=True)

    if result.get("already_exists"):
        return await callback.answer("Ваша заявка уже принята!", show_alert=True)

    for admin_id in settings.ADMIN_IDS:
        try:
            admin_text = (
                f"❗️ Новая заявка на вывод #{result['reward_id']}!\n"
                f"Пользователь: @{callback.from_user.username or 'скрыт'} (ID: `{user_id}`)\n"
                f"Требуется модерация. Используйте /rewards для просмотра."
            )
            await bot.send_message(admin_id, admin_text)
        except Exception as e:
            print(f"Не удалось отправить уведомление админу {admin_id}: {e}")

    reply = await bot.send_message(user_id, "✅ Ваша заявка принята! Ожидайте, с вами свяжутся. 😍")
    await state.update_data(junk_message_id=reply.message_id)
    await callback.answer()


@router.callback_query(F.data == "promo_code")
async def promo_code_start(callback: CallbackQuery, state: FSMContext):
    await clean_junk_message(callback, state)
    await callback.message.edit_media(
        media=InputMediaPhoto(media=settings.PHOTO_PROMO, caption=LEXICON["promo_prompt"]),
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

    response_text = ""
    if isinstance(result, int):
        response_text = f"✅ Промокод успешно активирован! Вам начислено {result} ⭐"
        await db.grant_achievement(user_id, "code_breaker", bot)
        full_info = await db.get_full_user_info(user_id)
        if full_info and len(full_info["activated_codes"]) >= 3:
            await db.grant_achievement(user_id, "promo_master", bot)
    elif result in ECONOMY_ERROR_MESSAGES:
        response_text = f"❌ {ECONOMY_ERROR_MESSAGES[result]}"
    elif result == "not_found":
        response_text = "❌ Такого промокода не существует или его срок действия истёк."
    elif result == "already_activated":
        response_text = "❌ Вы уже активировали этот промокод."
    else:
        response_text = f"❌ {ECONOMY_ERROR_MESSAGES['unknown_error']}"

    await message.answer(response_text)
    await message.delete()
