# handlers/user_handlers.py
import logging
import uuid

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from config import settings
from database import db
from handlers.menu_handler import show_main_menu
from handlers.utils import clean_junk_message, safe_delete
from keyboards.inline import promo_back_keyboard
from keyboards.reply import get_main_menu_keyboard
from lexicon.texts import LEXICON, LEXICON_ERRORS

router = Router()
logger = logging.getLogger(__name__)


class PromoCodeStates(StatesGroup):
    waiting_for_promo_code = State()


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    """Handler for the /start command. Handles user registration and referrals."""
    if not message.from_user:
        return

    await state.clear()
    args = message.text.split()
    referrer_id = None
    if len(args) > 1:
        try:
            referrer_id = int(args[1])
            if referrer_id == message.from_user.id:
                referrer_id = None
        except ValueError:
            referrer_id = None
            logger.warning(
                f"Invalid referrer ID provided for user {message.from_user.id}"
            )

    is_new_user = await db.add_user(
        user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
        referrer_id=referrer_id,
    )

    if is_new_user and referrer_id:
        # ИСПРАВЛЕНО: Заменено на add_balance, так как update_balance не существует
        await db.add_balance(
            referrer_id,
            settings.REFERRAL_BONUS,
            transaction_type="referral",
            idem_key=f"ref-{message.from_user.id}-{referrer_id}",
        )
        # ИСПРАВЛЕНО: Заменено на increment_referral_count (в единственном числе)
        await db.increment_referral_count(referrer_id)
        if message.bot:
            try:
                await message.bot.send_message(
                    referrer_id,
                    f"🎉 У вас новый реферал! Вы получили {settings.REFERRAL_BONUS} ⭐",
                )
            except Exception as e:
                logger.error(
                    f"Could not notify referrer {referrer_id} about new referral: {e}"
                )

        # This sends the reply keyboard.
        await message.answer(
            "👇 Внизу появилось меню для удобной навигации",
            reply_markup=get_main_menu_keyboard(),
        )
        # This sends the inline menu.
        await show_main_menu(message.bot, message.from_user.id, state=state)


@router.message(F.text.in_(["📖 Меню", "▶️ Старт"]))
async def menu_text_handler(message: Message, state: FSMContext):
    """Handler for the 'Menu' and 'Start' reply buttons."""
    if message.from_user:
        await show_main_menu(message.bot, message.from_user.id, state=state)


@router.message(F.text == "🎁 Бонус")
async def bonus_text_handler(message: Message):
    """Обработчик для кнопки 'Бонус'."""
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


@router.message(F.text)
async def unknown_command(message: Message):
    """Handler for unknown text commands."""
    await message.delete()


async def process_promo_code(message: Message, state: FSMContext):
    """Processes the entered promo code."""
    if not message.text or not message.from_user:
        return

    code = message.text.strip()
    user_id = message.from_user.id
    # Исправлено: добавлен обязательный аргумент idem_key
    result = await db.activate_promo(code, user_id, idem_key=str(uuid.uuid4()))
    data = await state.get_data()
    prompt_msg_id = data.get("promo_prompt_msg")

    if prompt_msg_id:
        await safe_delete(message.bot, message.chat.id, prompt_msg_id)

    if result["status"] == "success":
        reward_text = f"и {result['reward']} ⭐" if result.get("reward", 0) > 0 else ""
        response_text = (
            f"✅ Промокод '{code}' успешно активирован! Вы получили {reward_text}."
        )
    elif result["status"] == "not_found":
        response_text = LEXICON_ERRORS["promo_not_found"]
    elif result["status"] == "expired":
        response_text = LEXICON_ERRORS["promo_expired"]
    elif result["status"] == "already_used":
        response_text = LEXICON_ERRORS["promo_already_used"]
    else:
        response_text = LEXICON_ERRORS["promo_failed"]

    await message.answer(response_text)
    await clean_junk_message(state, message.bot)
    await state.clear()
    await show_main_menu(message.bot, message.chat.id, state=state)


async def enter_promo_code(message, state: FSMContext):
    """Asks the user to enter a promo code."""
    prompt_msg = await message.answer(
        LEXICON["enter_promo"], reply_markup=promo_back_keyboard()
    )
    await state.set_state(PromoCodeStates.waiting_for_promo_code)
    await state.update_data(promo_prompt_msg=prompt_msg.message_id)
