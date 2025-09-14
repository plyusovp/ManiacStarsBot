# handlers/user_handlers.py
import logging
import uuid
from typing import List

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InputMediaPhoto, Message

from config import settings
from database import db
from gifts import GIFTS_CATALOG
from handlers.utils import (
    clean_junk_message,
    generate_referral_link,
    get_user_info_text,
    safe_delete,
    safe_edit_caption,
    safe_send_message,
)
from keyboards.factories import GiftCallback, MenuCallback, UserCallback
from keyboards.inline import (
    back_to_menu_keyboard,
    gift_confirm_keyboard,
    gifts_catalog_keyboard,
    main_menu_keyboard,
    profile_keyboard,
    promo_back_keyboard,
    top_users_keyboard,
)
from keyboards.reply import persistent_menu_keyboard
from lexicon.texts import LEXICON, LEXICON_ERRORS

router = Router()
logger = logging.getLogger(__name__)


# --- FSM States ---
class UserState(StatesGroup):
    enter_promo = State()
    confirm_gift = State()
    current_view = State()


# --- Command Handlers ---
@router.message(Command("start"))
async def start_handler(
    message: Message,
    state: FSMContext,
    bot: Bot,
    command: CommandObject,
):
    if command.args and command.args.startswith("reward_"):
        return

    await state.clear()
    user = message.from_user
    if not user:
        return

    user_id = user.id
    username = user.username
    full_name = user.full_name

    referrer_id = None
    if command.args:
        try:
            # Проверяем, является ли аргумент числом
            validated_id = int(command.args)
            # Нельзя пригласить самого себя
            if validated_id != user_id:
                referrer_id = validated_id
                logger.info(f"User {user_id} joined with referrer {referrer_id}")
        except (ValueError, TypeError):
            logger.warning(f"Invalid referral code received: {command.args}")

    is_new_user = await db.add_user(user_id, username, full_name, referrer_id)

    if is_new_user and referrer_id:
        # Проверяем, существует ли пригласивший пользователь
        if await db.user_exists(referrer_id):
            await db.add_balance_with_checks(
                referrer_id,
                settings.REFERRAL_BONUS,
                "referral_bonus",
                ref_id=str(user_id),
            )
            await safe_send_message(
                bot,
                referrer_id,
                f"По вашей ссылке зарегистрировался новый пользователь! Вам начислено {settings.REFERRAL_BONUS} ⭐.",
            )
        else:
            logger.warning(f"Referrer with ID {referrer_id} not found in database.")

    balance = await db.get_user_balance(user_id)
    caption = LEXICON["main_menu"].format(balance=balance)

    try:
        if message.reply_to_message and message.reply_to_message.photo:
            await bot.delete_message(
                message.chat.id, message.reply_to_message.message_id
            )
    except Exception as e:
        logger.debug(f"Could not delete previous message in start_handler: {e}")

    await message.answer_photo(
        photo=settings.PHOTO_MAIN_MENU,
        caption=caption,
        reply_markup=main_menu_keyboard(),
    )
    await state.update_data(current_view="main_menu")

    await message.answer(
        "Нажмите «Меню», чтобы открыть навигацию",
        reply_markup=persistent_menu_keyboard(),
    )


@router.message(or_f(Command("menu"), F.text == "Меню"))
async def menu_handler(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    if not message.from_user:
        return
    balance = await db.get_user_balance(message.from_user.id)
    caption = LEXICON["main_menu"].format(balance=balance)

    await message.answer_photo(
        photo=settings.PHOTO_MAIN_MENU,
        caption=caption,
        reply_markup=main_menu_keyboard(),
    )
    await state.update_data(current_view="main_menu")


@router.message(Command("bonus"))
async def bonus_handler(message: Message):
    if not message.from_user:
        return

    result = await db.get_daily_bonus(message.from_user.id)
    status = result.get("status")
    if status == "success":
        reward = result.get("reward", 0)
        await message.answer(f"🎁 Вы получили {reward} ⭐ дневного бонуса!")
    elif status == "wait":
        seconds = result.get("seconds_left", 0)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        await message.answer(f"⏳ Бонус будет доступен через {hours} ч {minutes} м.")
    else:
        await message.answer("❌ Не удалось получить бонус. Попробуйте позже.")


# --- Callback Handlers (Main Menu Navigation) ---
@router.callback_query(MenuCallback.filter(F.name == "main_menu"))
async def back_to_main_menu_handler(
    callback: CallbackQuery, state: FSMContext, bot: Bot
):
    data = await state.get_data()
    if data.get("current_view") == "main_menu":
        await callback.answer()
        return

    await state.clear()
    await clean_junk_message(state, bot)
    if callback.message:
        balance = await db.get_user_balance(callback.from_user.id)
        caption = LEXICON["main_menu"].format(balance=balance)
        media = InputMediaPhoto(media=settings.PHOTO_MAIN_MENU, caption=caption)
        try:
            await bot.edit_message_media(
                media=media,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=main_menu_keyboard(),
            )
            await state.update_data(current_view="main_menu")
        except TelegramBadRequest as e:
            logger.warning(f"Failed to edit message to main menu: {e}")
            await safe_delete(
                bot, callback.message.chat.id, callback.message.message_id
            )
            await bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=settings.PHOTO_MAIN_MENU,
                caption=caption,
                reply_markup=main_menu_keyboard(),
            )
            await state.update_data(current_view="main_menu")
    await callback.answer()


# --- Profile Section ---
@router.callback_query(MenuCallback.filter(F.name == "profile"))
async def profile_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await clean_junk_message(state, bot)
    if callback.message:
        profile_text = await get_user_info_text(callback.from_user.id)
        media = InputMediaPhoto(media=settings.PHOTO_PROFILE, caption=profile_text)
        await bot.edit_message_media(
            media=media,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=profile_keyboard(),
        )
        await state.update_data(current_view="profile")
    await callback.answer()


# --- Referral Section ---
@router.callback_query(MenuCallback.filter(F.name == "earn_bread"))
async def referral_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await clean_junk_message(state, bot)
    if callback.message:
        referral_link = generate_referral_link(callback.from_user.id)
        referrals_count = await db.get_referrals_count(callback.from_user.id)
        text = LEXICON["referral_menu"].format(
            ref_link=referral_link,
            invited_count=referrals_count,
            ref_bonus=settings.REFERRAL_BONUS,
        )
        media = InputMediaPhoto(media=settings.PHOTO_EARN_STARS, caption=text)
        await bot.edit_message_media(
            media=media,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=back_to_menu_keyboard(),
        )
        await state.update_data(current_view="earn_bread")
    await callback.answer()


# --- Top Users Section ---
@router.callback_query(MenuCallback.filter(F.name == "top_users"))
async def top_users_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await clean_junk_message(state, bot)
    if callback.message:
        top_users = await db.get_top_referrers()
        top_users_text = ""
        if top_users:
            for i, user in enumerate(top_users, 1):
                top_users_text += (
                    f"{i}. {user['full_name']} — {user['ref_count']} 🙋‍♂️\n"
                )
        else:
            top_users_text = "Пока никто не пригласил друзей."

        text = LEXICON["top_menu"].format(top_users_text=top_users_text)
        media = InputMediaPhoto(media=settings.PHOTO_TOP, caption=text)
        await bot.edit_message_media(
            media=media,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=top_users_keyboard(),
        )
        await state.update_data(current_view="top_users")
    await callback.answer()


# --- Promo Code Section ---
@router.callback_query(UserCallback.filter(F.action == "enter_promo"))
async def enter_promo_start_handler(
    callback: CallbackQuery, state: FSMContext, bot: Bot
):
    await state.set_state(UserState.enter_promo)
    if callback.message:
        media = InputMediaPhoto(
            media=settings.PHOTO_PROMO, caption="✏️ Введите ваш промокод:"
        )
        await bot.edit_message_media(
            media=media,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=promo_back_keyboard(),
        )
        await state.update_data(current_view="enter_promo")
    await callback.answer()


@router.message(UserState.enter_promo, F.text)
async def process_promo_handler(message: Message, state: FSMContext, bot: Bot):
    if not message.text or not message.from_user:
        return
    promo_code = message.text.upper()
    user_id = message.from_user.id
    await safe_delete(bot, message.chat.id, message.message_id)

    idem_key = f"promo-{user_id}-{promo_code}"
    result = await db.activate_promo(user_id, promo_code, idem_key)

    if isinstance(result, int):
        await message.answer(
            f"✅ Промокод `{promo_code}` успешно активирован! Вам начислено {result} ⭐."
        )
    elif result == "already_activated":
        await message.answer("❌ Вы уже активировали этот промокод.")
    elif result == "not_found":
        await message.answer(
            "❌ Такого промокода не существует или у него закончились активации."
        )
    else:
        await message.answer(f"❌ Не удалось активировать промокод. Ошибка: {result}")

    await state.clear()
    await menu_handler(message, state, bot)


# --- Gifts/Withdrawal Section ---
async def check_withdrawal_requirements(user_id: int, bot: Bot) -> List[str]:
    errors = []
    try:
        member = await bot.get_chat_member(settings.CHANNEL_ID, user_id)
        if member.status not in ["member", "administrator", "creator"]:
            errors.append("Вы не подписаны на основной канал.")
    except TelegramBadRequest:
        errors.append("Не удалось проверить подписку на канал.")

    referrals = await db.get_referrals_count(user_id)
    if referrals < settings.MIN_REFERRALS_FOR_WITHDRAW:
        errors.append(
            f"Нужно пригласить еще {settings.MIN_REFERRALS_FOR_WITHDRAW - referrals} друзей."
        )
    return errors


@router.callback_query(MenuCallback.filter(F.name == "gifts"))
async def gifts_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    await clean_junk_message(state, bot)
    if not callback.message:
        return await callback.answer()

    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)
    referrals = await db.get_referrals_count(user_id)

    text = LEXICON["gifts_menu"].format(
        balance=balance,
        min_refs=settings.MIN_REFERRALS_FOR_WITHDRAW,
        referrals_count=referrals,
    )
    media = InputMediaPhoto(media=settings.PHOTO_WITHDRAW, caption=text)

    await bot.edit_message_media(
        media=media,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=gifts_catalog_keyboard(),
    )
    await state.update_data(current_view="gifts")
    await callback.answer()


@router.callback_query(GiftCallback.filter(F.action == "select"))
async def select_gift_handler(
    callback: CallbackQuery, callback_data: GiftCallback, state: FSMContext, bot: Bot
):
    if not callback.message:
        return
    user_id = callback.from_user.id
    cost = callback_data.cost
    item_id = callback_data.item_id

    errors = await check_withdrawal_requirements(user_id, bot)
    if errors:
        error_text = LEXICON_ERRORS["gift_requirements_not_met"].format(
            errors="\n".join(f"- {e}" for e in errors)
        )
        return await callback.answer(error_text, show_alert=True)

    balance = await db.get_user_balance(user_id)
    if balance < cost:
        return await callback.answer(
            f"Недостаточно средств. Нужно {cost} ⭐, у вас {balance} ⭐.",
            show_alert=True,
        )

    gift = next((g for g in GIFTS_CATALOG if g["id"] == item_id), None)
    if not gift:
        return await callback.answer("Ошибка: подарок не найден.", show_alert=True)

    await state.set_state(UserState.confirm_gift)
    text = LEXICON["gift_confirm"].format(
        cost=cost, emoji=gift["emoji"], name=gift["name"]
    )
    await safe_edit_caption(
        bot,
        text,
        callback.message.chat.id,
        callback.message.message_id,
        reply_markup=gift_confirm_keyboard(item_id, cost),
    )
    await state.update_data(current_view="gift_confirm")
    await callback.answer()


@router.callback_query(
    UserState.confirm_gift, GiftCallback.filter(F.action == "confirm")
)
async def confirm_gift_handler(
    callback: CallbackQuery, callback_data: GiftCallback, state: FSMContext, bot: Bot
):
    await state.clear()
    if not callback.message:
        return
    user_id = callback.from_user.id
    cost = callback_data.cost
    item_id = callback_data.item_id

    balance = await db.get_user_balance(user_id)
    if balance < cost:
        await callback.answer("Недостаточно средств!", show_alert=True)
        return await gifts_handler(callback, state, bot)

    idem_key = f"reward-{user_id}-{uuid.uuid4()}"
    result = await db.create_reward_request(user_id, item_id, cost, idem_key)

    gift = next((g for g in GIFTS_CATALOG if g["id"] == item_id), None)
    if not gift:
        return await callback.answer("Ошибка: подарок не найден.", show_alert=True)

    if result["success"]:
        reward_id = result["reward_id"]
        admin_text = (
            f"❗️ Новая заявка на вывод!\n\n"
            f"<b>ID заявки:</b> <code>{reward_id}</code>\n"
            f"<b>Пользователь:</b> <a href='tg://user?id={user_id}'>{callback.from_user.full_name}</a> (<code>{user_id}</code>)\n"
            f"<b>Подарок:</b> {gift['emoji']} {gift['name']}\n"
            f"<b>Стоимость:</b> {cost} ⭐"
        )
        for admin_id in settings.ADMIN_IDS:
            await safe_send_message(bot, admin_id, admin_text)

        await safe_edit_caption(
            bot=bot,
            caption=LEXICON["withdrawal_success"].format(
                emoji=gift["emoji"], name=gift["name"], amount=cost
            ),
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=back_to_menu_keyboard(),
        )
        await state.update_data(current_view="main_menu")
        await callback.answer("✅ Заявка создана!", show_alert=True)
    else:
        await callback.answer(
            f"Ошибка создания заявки: {result.get('reason', 'unknown')}",
            show_alert=True,
        )
        await gifts_handler(callback, state, bot)
