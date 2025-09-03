# handlers/admin_handlers.py
import datetime
import html
import logging
import re
from typing import Union

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import CallbackQuery, Message

from config import settings
from database import db
from keyboards.inline import (
    admin_main_menu,
    admin_manage_menu,
    admin_promos_menu,
    admin_reward_details_menu,
    admin_rewards_menu,
    admin_user_info_menu,
)

router = Router()
router.message.filter(F.from_user.id.in_(settings.ADMIN_IDS))
router.callback_query.filter(F.from_user.id.in_(settings.ADMIN_IDS))
logger = logging.getLogger(__name__)


# --- FSM Состояния ---
class Broadcast(StatesGroup):
    waiting_for_message = State()


class Promo(StatesGroup):
    waiting_for_name = State()
    waiting_for_reward = State()
    waiting_for_uses = State()


class ManageBalance(StatesGroup):
    waiting_for_user = State()
    waiting_for_amount = State()
    is_debit = State()


class UserInfo(StatesGroup):
    waiting_for_user = State()


# --- НОВОЕ: FSM для сброса состояния пользователя ---
class ResetFSM(StatesGroup):
    waiting_for_user = State()


# --- Универсальный обработчик отмены для FSM ---
@router.message(Command("cancel"))
@router.message(F.text.lower() == "отмена")
async def cancel_handler(message: Message, state: FSMContext):
    """Отменяет любое FSM состояние."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активных действий для отмены.")
        return

    await state.clear()
    await message.answer("Действие отменено.")
    await admin_panel_handler(message)


# --- Основные обработчики админ-панели ---
@router.message(Command("admin"))
async def admin_panel_handler(message: Message):
    await message.answer(
        "Добро пожаловать в админ-панель!", reply_markup=admin_main_menu()
    )


@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback_handler(
    callback_or_message: Union[CallbackQuery, Message],
):
    text = "Добро пожаловать в админ-панель!"
    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.message.edit_text(
            text, reply_markup=admin_main_menu()
        )
    else:
        await callback_or_message.answer(text, reply_markup=admin_main_menu())


# --- Управление заявками на вывод ---
@router.callback_query(F.data == "admin_rewards")
async def admin_rewards_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    page = 1
    limit = 5
    pending_rewards = await db.get_pending_rewards(page, limit)
    total_count = await db.get_pending_rewards_count()
    total_pages = (total_count + limit - 1) // limit

    text = f"⏳ Новые заявки на вывод ({total_count} шт.)\n\n"
    if not pending_rewards:
        text += "Нет активных заявок."
    else:
        for reward in pending_rewards:
            text += (
                f"🔹 /reward_{reward['id']} от @{reward['username']} "
                f"({reward['stars_cost']} ⭐) - {reward['created_at']}\n"
            )

    await callback.message.edit_text(
        text, reply_markup=admin_rewards_menu(page, total_pages)
    )


@router.callback_query(F.data.startswith("admin_rewards_page_"))
async def admin_rewards_page_handler(callback: CallbackQuery):
    page = int(callback.data.split("_")[-1])
    limit = 5
    pending_rewards = await db.get_pending_rewards(page, limit)
    total_count = await db.get_pending_rewards_count()
    total_pages = (total_count + limit - 1) // limit

    text = f"⏳ Новые заявки на вывод ({total_count} шт.)\n\n"
    if not pending_rewards:
        text += "Нет активных заявок."
    else:
        for reward in pending_rewards:
            text += (
                f"🔹 /reward_{reward['id']} от @{reward['username']} "
                f"({reward['stars_cost']} ⭐) - {reward['created_at']}\n"
            )

    await callback.message.edit_text(
        text, reply_markup=admin_rewards_menu(page, total_pages)
    )


@router.message(Command(re.compile(r"reward_\d+")))
async def reward_details_command_handler(message: Message, state: FSMContext):
    try:
        reward_id = int(message.text.split("_")[1])
    except (ValueError, IndexError):
        return await message.answer("Неверный формат команды.")

    details = await db.get_reward_full_details(reward_id)
    if not details:
        return await message.answer(f"Заявка #{reward_id} не найдена.")

    reward = details["reward"]
    user_id = reward["user_id"]
    user_details = await db.get_user_full_details_for_admin(user_id)

    ledger_text = "\n".join(
        [
            f"• {l['amount']}⭐ за `{l['reason']}` ({l['created_at']})"
            for l in user_details["ledger"]
        ]
    )

    text = (
        f"<b>Детали заявки #{reward_id}</b>\n\n"
        f"<b>Пользователь:</b> @{reward['username']} (<code>{user_id}</code>)\n"
        f"<b>Имя:</b> {html.escape(user_details['user_data']['full_name'])}\n"
        f"<b>Статус заявки:</b> {reward['status']}\n"
        f"<b>Запрошено:</b> {reward['item_id']} за {reward['stars_cost']} ⭐\n"
        f"<b>Дата создания:</b> {reward['created_at']}\n\n"
        f"<b>Баланс юзера:</b> {user_details['user_data']['balance']} ⭐\n"
        f"<b>Дата регистрации:</b> {user_details['user_data']['created_at']}\n"
        f"<b>Уровень риска:</b> {user_details['user_data']['risk_level']}\n\n"
        f"<b>Последние транзакции:</b>\n{ledger_text}"
    )

    await message.answer(
        text, reply_markup=admin_reward_details_menu(reward_id, user_id)
    )


@router.callback_query(F.data.startswith("admin_reward_"))
async def reward_action_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    parts = callback.data.split("_")
    action = parts[2]
    reward_id = int(parts[3])
    admin_id = callback.from_user.id

    details = await db.get_reward_full_details(reward_id)
    if not details:
        return await callback.answer("Заявка не найдена.", show_alert=True)

    user_id = details["reward"]["user_id"]
    username = details["reward"]["username"]

    success = False
    notify_text = ""

    if action == "approve":
        success = await db.approve_reward(reward_id, admin_id)
        notify_text = f"✅ Ваша заявка #{reward_id} была одобрена администратором. Ожидайте выдачи."
    elif action == "reject":
        success = await db.reject_reward(
            reward_id, admin_id, "Отклонено администратором"
        )
        notify_text = f"❌ Ваша заявка #{reward_id} была отклонена. Звёзды возвращены на ваш баланс."
    elif action == "fulfill":
        success = await db.fulfill_reward(reward_id, admin_id)
        notify_text = f"🎉 Ваша заявка #{reward_id} выполнена! Подарок отправлен."

    if success:
        await callback.answer(
            f"Статус заявки #{reward_id} изменен на '{action}'.", show_alert=True
        )
        try:
            await bot.send_message(user_id, notify_text)
        except Exception as e:
            await callback.message.answer(
                f"Не удалось уведомить пользователя @{username}: {e}"
            )
        await admin_rewards_handler(callback, state)  # Обновляем список
    else:
        await callback.answer(
            "Не удалось изменить статус. Возможно, он уже был изменен.", show_alert=True
        )


# --- Управление промокодами ---
@router.callback_query(F.data == "admin_promos")
async def admin_promos_handler(callback: CallbackQuery):
    promos = await db.get_active_promos()
    text = "🎟️ Активные промокоды:\n\n"
    if not promos:
        text += "Нет активных промокодов."
    else:
        for code, reward, left, total in promos:
            text += f"`{code}` — {reward} ⭐ (осталось {left}/{total})\n"

    await callback.message.edit_text(text, reply_markup=admin_promos_menu())


@router.callback_query(F.data == "admin_promo_create")
async def admin_promo_create_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите название нового промокода (например, `NEWYEAR2024`).\n\nДля отмены введите /cancel"
    )
    await state.set_state(Promo.waiting_for_name)


@router.message(Promo.waiting_for_name)
async def process_promo_name(message: Message, state: FSMContext):
    await state.update_data(promo_name=message.text.strip().upper())
    await message.answer(
        "Отлично. Теперь введите количество звёзд, которое он даёт (например, `10`).\n\nДля отмены введите /cancel"
    )
    await state.set_state(Promo.waiting_for_reward)


@router.message(Promo.waiting_for_reward)
async def process_promo_reward(message: Message, state: FSMContext):
    try:
        reward = int(message.text)
        if reward <= 0:
            raise ValueError
        await state.update_data(promo_reward=reward)
        await message.answer(
            "Хорошо. Теперь введите общее количество активаций (например, `100`).\n\nДля отмены введите /cancel"
        )
        await state.set_state(Promo.waiting_for_uses)
    except ValueError:
        await message.answer("Неверное число. Введите целое положительное число.")
        # ИСПРАВЛЕНИЕ: Очищаем состояние при ошибке
        await state.clear()
        await admin_panel_handler(message)


@router.message(Promo.waiting_for_uses)
async def process_promo_uses(message: Message, state: FSMContext):
    try:
        uses = int(message.text)
        if uses <= 0:
            raise ValueError
        data = await state.get_data()
        name = data["promo_name"]
        reward = data["promo_reward"]

        await db.add_promo_code(name, reward, uses)
        await message.answer(
            f"✅ Промокод `{name}` на {reward} ⭐ ({uses} активаций) успешно создан!"
        )
    except ValueError:
        await message.answer("Неверное число. Введите целое положительное число.")
    finally:
        # ИСПРАВЛЕНИЕ: Очищаем состояние в любом случае (успех или ошибка)
        await state.clear()
        await admin_panel_handler(message)


# --- Управление пользователями ---
@router.callback_query(F.data == "admin_manage")
async def admin_manage_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выберите действие:", reply_markup=admin_manage_menu()
    )


@router.callback_query(F.data.in_({"admin_grant", "admin_debit"}))
async def manage_balance_start(callback: CallbackQuery, state: FSMContext):
    is_debit = callback.data == "admin_debit"
    await state.update_data(is_debit=is_debit)
    action_word = "списания" if is_debit else "начисления"
    await callback.message.edit_text(
        f"Введите ID или @username пользователя для {action_word}:\n\nДля отмены введите /cancel"
    )
    await state.set_state(ManageBalance.waiting_for_user)


@router.message(ManageBalance.waiting_for_user)
async def process_manage_user(message: Message, state: FSMContext, bot: Bot):
    user_input = message.text.strip()
    user_id = None
    if user_input.isdigit():
        user_id = int(user_input)
    elif user_input.startswith("@"):
        user_id = await db.get_user_by_username(user_input[1:])

    if not user_id:
        await message.answer(
            "Пользователь не найден. Попросите его сначала запустить /start или проверьте правильность введенных данных.\n\nДля отмены введите /cancel"
        )
        # ИСПРАВЛЕНИЕ: Не оставляем пользователя в состоянии, если юзер не найден
        await state.clear()
        await admin_panel_handler(message)
        return

    try:
        user_exists = await db.get_full_user_info(user_id)
        if not user_exists:
            chat = await bot.get_chat(user_id)
            await db.add_user(
                user_id=chat.id, username=chat.username, full_name=chat.full_name
            )
            await message.answer(
                f"Зарегистрирован новый пользователь: @{chat.username}."
            )
    except Exception as e:
        await message.answer(
            f"Не удалось найти пользователя в Telegram или добавить его в базу. Ошибка: {e}\n\n"
            f"Попросите его сначала запустить бота командой /start."
        )
        # ИСПРАВЛЕНИЕ: Очищаем состояние при ошибке
        await state.clear()
        await admin_panel_handler(message)
        return

    await state.update_data(target_user_id=user_id)
    await message.answer(
        "Пользователь найден. Теперь введите сумму (целое положительное число):\n\nДля отмены введите /cancel"
    )
    await state.set_state(ManageBalance.waiting_for_amount)


@router.message(ManageBalance.waiting_for_amount)
async def process_manage_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
        if amount <= 0:
            raise ValueError

        data = await state.get_data()
        user_id = data["target_user_id"]
        is_debit = data["is_debit"]
        admin_id = message.from_user.id

        if is_debit:
            success = await db.spend_balance(
                user_id, amount, "admin_debit", ref_id=str(admin_id)
            )
            if success:
                await message.answer(
                    f"✅ У пользователя `{user_id}` списано {amount} ⭐."
                )
            else:
                await message.answer("❌ Не удалось списать. Недостаточно средств.")
        else:
            await db.add_balance_unrestricted(
                user_id, amount, "admin_grant", ref_id=str(admin_id)
            )
            await message.answer(f"✅ Пользователю `{user_id}` начислено {amount} ⭐.")

    except ValueError:
        await message.answer("Неверная сумма. Введите целое положительное число.")
    finally:
        # ИСПРАВЛЕНИЕ: Очищаем состояние в любом случае
        await state.clear()
        await admin_panel_handler(message)


# --- НОВОЕ: Раздел сброса FSM состояния ---
@router.callback_query(F.data == "admin_reset_fsm")
async def reset_fsm_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите ID или @username пользователя, которому нужно сбросить состояние FSM:\n\nДля отмены введите /cancel",
    )
    await state.set_state(ResetFSM.waiting_for_user)


@router.message(ResetFSM.waiting_for_user)
async def reset_fsm_process(message: Message, state: FSMContext, bot: Bot):
    user_input = message.text.strip()
    user_id = None
    if user_input.isdigit():
        user_id = int(user_input)
    elif user_input.startswith("@"):
        user_id = await db.get_user_by_username(user_input[1:])

    if not user_id:
        await message.answer(
            "Пользователь не найден. Проверьте данные и попробуйте снова."
        )
        await state.clear()
        await admin_panel_handler(message)
        return

    try:
        # Для сброса состояния нужен dispatcher, который мы передадим в main
        dp = router.parent_router
        if not dp:
            raise RuntimeError(
                "Could not get dispatcher from router. Make sure router is included into a parent."
            )

        # Создаем ключ хранилища для нужного пользователя
        storage_key = StorageKey(bot_id=bot.id, chat_id=user_id, user_id=user_id)
        # Создаем FSMContext для этого ключа
        user_context = FSMContext(storage=dp.fsm.storage, key=storage_key)
        # Очищаем состояние
        await user_context.clear()

        await message.answer(
            f"✅ Состояние FSM для пользователя `{user_id}` было принудительно сброшено."
        )
        logger.info(
            f"Admin {message.from_user.id} cleared FSM state for user {user_id}"
        )

    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при сбросе состояния: {e}")
        logger.error(f"Failed to reset FSM for user {user_id}: {e}")
    finally:
        await state.clear()
        await admin_panel_handler(message)


# --- Раздел статистики ---
@router.callback_query(F.data == "admin_stats")
async def admin_stats_handler(callback: CallbackQuery):
    stats = await db.get_bot_statistics()
    text = (
        "<b>📊 Статистика бота</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"🌱 Новых за сегодня: <b>{stats['new_today']}</b>\n"
        f"📈 Новых за неделю: <b>{stats['new_week']}</b>\n"
        f"🏃 Активных за 24ч: <b>{stats['active_day']}</b>\n"
        f"💰 Всего звёзд в системе: <b>{stats['total_balance']}</b> ⭐"
    )
    await callback.message.edit_text(text, reply_markup=admin_main_menu())


# --- Раздел информации о пользователе ---
@router.callback_query(F.data == "admin_user_info")
async def admin_user_info_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите ID или @username пользователя для просмотра информации:\n\nДля отмены введите /cancel",
    )
    await state.set_state(UserInfo.waiting_for_user)


@router.callback_query(F.data.startswith("admin_user_info_"))
async def admin_user_info_from_reward(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[-1])
    await process_user_info_request(user_id, callback, state)


@router.message(UserInfo.waiting_for_user)
async def process_user_info_search(message: Message, state: FSMContext):
    user_input = message.text.strip()
    user_id = None
    if user_input.isdigit():
        user_id = int(user_input)
    elif user_input.startswith("@"):
        user_id = await db.get_user_by_username(user_input[1:])

    if not user_id:
        await message.answer(
            "Пользователь не найден. Попробуйте еще раз или введите /cancel."
        )
        # ИСПРАВЛЕНИЕ: Не оставляем в состоянии, если не нашли юзера
        await state.clear()
        await admin_panel_handler(message)
        return

    await process_user_info_request(user_id, message, state)


async def process_user_info_request(
    user_id: int, message_or_callback: Union[Message, CallbackQuery], state: FSMContext
):
    """Общая функция для отображения информации о пользователе."""
    # ИСПРАВЛЕНИЕ: Очищаем состояние в самом начале, чтобы не забыть
    await state.clear()

    details = await db.get_user_full_details_for_admin(user_id)
    if not details:
        error_text = "Не удалось получить информацию о пользователе."
        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.answer(error_text, show_alert=True)
            # Возвращаемся в админку, т.к. показать нечего
            await admin_panel_callback_handler(message_or_callback)
        else:
            await message_or_callback.answer(error_text)
            await admin_panel_handler(message_or_callback)
        return

    udata = details["user_data"]
    reg_date = datetime.datetime.fromtimestamp(udata["registration_date"]).strftime(
        "%Y-%m-%d %H:%M"
    )
    last_seen_date = datetime.datetime.fromtimestamp(udata["last_seen"]).strftime(
        "%Y-%m-%d %H:%M"
    )

    ledger_text = "\n".join(
        [
            f"• {l['amount']:+d}⭐ за `{l['reason']}` ({l['created_at']})"
            for l in details["ledger"]
        ]
    )
    if not ledger_text:
        ledger_text = "Нет транзакций."

    text = (
        f"<b>ℹ️ Информация о пользователе</b>\n\n"
        f"<b>ID:</b> <code>{udata['user_id']}</code>\n"
        f"<b>Username:</b> @{udata['username']}\n"
        f"<b>Имя:</b> {html.escape(udata['full_name'])}\n"
        f"<b>Баланс:</b> {udata['balance']} ⭐\n\n"
        f"<b>Регистрация:</b> {reg_date}\n"
        f"<b>Последняя активность:</b> {last_seen_date}\n"
        f"<b>Пригласил:</b> {details['referrals_count']} чел.\n"
        f"<b>Дуэли (В/П):</b> {details['duel_stats']['wins']}/{details['duel_stats']['losses']}\n\n"
        f"<b>Последние 15 транзакций:</b>\n{ledger_text}"
    )

    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.edit_text(
            text, reply_markup=admin_user_info_menu()
        )
    else:
        await message_or_callback.answer(text, reply_markup=admin_user_info_menu())
