# handlers/user_handlers.py
import logging
import uuid

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject, CommandStart, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InputMediaPhoto, Message

from config import settings
from database import db
from handlers.utils import (
    clean_junk_message,
    generate_referral_link,
    get_user_info_text,
    safe_delete,
    safe_edit_caption,
    safe_send_message,
    validate_referral_code,
)
from keyboards.factories import MenuCallback, UserCallback
from keyboards.inline import (
    gifts_keyboard,
    main_menu_keyboard,
    profile_keyboard,
    promo_back_keyboard,
    referral_keyboard,
    top_users_keyboard,
)
from keyboards.reply import persistent_menu_keyboard
from lexicon.texts import LEXICON, LEXICON_ERRORS

router = Router()
logger = logging.getLogger(__name__)


# --- FSM States ---
class UserState(StatesGroup):
    enter_promo = State()
    enter_withdrawal_amount = State()
    confirm_withdrawal = State()


# --- Command Handlers ---
@router.message(CommandStart())
async def start_handler(
    message: Message, state: FSMContext, bot: Bot, command: CommandObject
):
    # Этот обработчик теперь будет игнорироваться, если аргументы начинаются с 'reward_'
    # благодаря более специфичному фильтру в admin_handlers.
    if command.args and command.args.startswith("reward_"):
        # Это команда для админа, этот хендлер не должен ее обрабатывать.
        # Aiogram должен был уже отфильтровать это, но на всякий случай.
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
        ref_code = command.args
        validated_id = validate_referral_code(ref_code)
        if validated_id and validated_id != user_id:
            referrer_id = validated_id
            logger.info(f"User {user_id} joined with referrer {referrer_id}")

    is_new_user = await db.add_user(user_id, username, full_name, referrer_id)

    if is_new_user and referrer_id:
        await db.add_balance_with_checks(
            referrer_id, settings.REFERRAL_BONUS, "referral_bonus", ref_id=str(user_id)
        )
        await safe_send_message(
            bot,
            referrer_id,
            f"По вашей ссылке зарегистрировался новый пользователь! Вам начислено {settings.REFERRAL_BONUS} ⭐.",
        )

    balance = await db.get_user_balance(user_id)
    caption = LEXICON["main_menu"].format(balance=balance)

    await message.answer_photo(
        photo=settings.PHOTO_MAIN_MENU,
        caption=caption,
        reply_markup=main_menu_keyboard(),
    )

    # Отправляем постоянную клавиатуру с кнопкой "Меню"
    await message.answer(
        "Нажмите «Меню», чтобы открыть навигацию",
        reply_markup=persistent_menu_keyboard(),
    )


@router.message(or_f(Command("menu"), F.text == "Меню"))
async def menu_handler(message: Message, state: FSMContext):
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


@router.message(Command("bonus"))
async def bonus_handler(message: Message):
    """Обрабатывает команду /bonus для получения ежедневного бонуса."""
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
    await state.clear()
    await clean_junk_message(state, bot)
    if callback.message:
        balance = await db.get_user_balance(callback.from_user.id)
        caption = LEXICON["main_menu"].format(balance=balance)
        media = InputMediaPhoto(media=settings.PHOTO_MAIN_MENU, caption=caption)
        await bot.edit_message_media(
            media=media,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=main_menu_keyboard(),
        )
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
    await callback.answer()


# --- Referral Section ---
@router.callback_query(MenuCallback.filter(F.name == "referrals"))
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
            reply_markup=referral_keyboard(),
        )
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
    await callback.answer()


@router.message(UserState.enter_promo, F.text)
async def process_promo_handler(message: Message, state: FSMContext, bot: Bot):
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
    await menu_handler(message, state)


# --- Gifts/Withdrawal Section ---
@router.callback_query(MenuCallback.filter(F.name == "gifts"))
async def gifts_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await clean_junk_message(state, bot)
    if not callback.message:
        return await callback.answer()

    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)
    referrals = await db.get_referrals_count(user_id)

    error_text = ""
    can_withdraw = True
    try:
        member = await bot.get_chat_member(settings.CHANNEL_ID, user_id)
        if member.status not in ["member", "administrator", "creator"]:
            error_text = LEXICON_ERRORS["error_not_subscribed"]
            can_withdraw = False
    except TelegramBadRequest:
        error_text = "Не удалось проверить подписку."
        can_withdraw = False

    if can_withdraw and referrals < settings.MIN_REFERRALS_FOR_WITHDRAW:
        error_text = LEXICON_ERRORS["error_not_enough_referrals"].format(
            min_refs=settings.MIN_REFERRALS_FOR_WITHDRAW
        )
        can_withdraw = False

    text = LEXICON["gifts_menu"].format(
        balance=balance,
        min_refs=settings.MIN_REFERRALS_FOR_WITHDRAW,
        referrals_count=referrals,
        error_text=error_text,
    )
    media = InputMediaPhoto(media=settings.PHOTO_WITHDRAW, caption=text)

    await bot.edit_message_media(
        media=media,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=gifts_keyboard(can_withdraw),
    )
    await callback.answer()


@router.callback_query(UserCallback.filter(F.action == "withdraw"))
async def withdraw_start_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(UserState.enter_withdrawal_amount)
    if callback.message:
        # Сохраняем ID оригинального сообщения, чтобы потом его отредактировать
        await state.update_data(original_message_id=callback.message.message_id)
        await safe_edit_caption(
            bot=bot,
            caption="💰 Введите сумму, которую хотите вывести:",
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=promo_back_keyboard(),
        )
    await callback.answer()


@router.message(UserState.enter_withdrawal_amount, F.text)
async def process_withdrawal_amount_handler(
    message: Message, state: FSMContext, bot: Bot
):
    data = await state.get_data()
    original_message_id = data.get("original_message_id")
    await safe_delete(bot, message.chat.id, message.message_id)

    if not original_message_id:
        await state.clear()
        return await menu_handler(message, state)

    try:
        amount = int(message.text)
        balance = await db.get_user_balance(message.from_user.id)
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной.")
        if amount > balance:
            await message.answer("❌ На вашем балансе недостаточно средств.")
            await state.clear()
            return await menu_handler(message, state)
        if amount < settings.MIN_WITHDRAWAL_AMOUNT:
            await message.answer(
                f"❌ Минимальная сумма для вывода: {settings.MIN_WITHDRAWAL_AMOUNT} ⭐."
            )
            await state.clear()
            return await menu_handler(message, state)

        await state.update_data(withdrawal_amount=amount)
        await state.set_state(UserState.confirm_withdrawal)

        await safe_edit_caption(
            bot,
            f"Вы уверены, что хотите подать заявку на вывод {amount} ⭐?",
            message.chat.id,
            original_message_id,
            reply_markup=gifts_keyboard(can_withdraw=True, confirm_mode=True),
        )

    except (ValueError, TypeError):
        await message.answer("❌ Неверный формат. Введите целое число.")
        await state.clear()
        return await menu_handler(message, state)


@router.callback_query(
    UserState.confirm_withdrawal, UserCallback.filter(F.action == "confirm_withdraw")
)
async def process_withdrawal_confirm_handler(
    callback: CallbackQuery, state: FSMContext, bot: Bot
):
    data = await state.get_data()
    amount = data.get("withdrawal_amount")
    user_id = callback.from_user.id

    if not amount:
        await state.clear()
        return await back_to_main_menu_handler(callback, state, bot)

    balance = await db.get_user_balance(user_id)
    if amount > balance:
        await callback.answer("Недостаточно средств!", show_alert=True)
        await state.clear()
        return await gifts_handler(callback, state, bot)

    idem_key = f"reward-{user_id}-{uuid.uuid4()}"
    result = await db.create_reward_request(
        user_id, f"withdraw_{amount}", amount, idem_key
    )

    await state.clear()

    if result["success"]:
        reward_id = result["reward_id"]
        admin_text = (
            f"❗️ Новая заявка на вывод!\n"
            f"ID заявки: `{reward_id}`\n"
            f"Пользователь: [{callback.from_user.full_name}](tg://user?id={user_id}) (`{user_id}`)\n"
            f"Сумма: {amount} ⭐"
        )
        for admin_id in settings.ADMIN_IDS:
            await safe_send_message(bot, admin_id, admin_text, parse_mode="Markdown")

        if callback.message:
            await safe_edit_caption(
                bot=bot,
                caption=LEXICON["withdrawal_success"].format(amount=amount),
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=main_menu_keyboard(back_only=True),
            )
    else:
        await callback.answer(
            f"Ошибка создания заявки: {result.get('reason', 'unknown')}",
            show_alert=True,
        )
        await back_to_main_menu_handler(callback, state, bot)

    await callback.answer()
