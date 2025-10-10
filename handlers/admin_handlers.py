# plyusovp/maniacstarsbot/ManiacStarsBot-4df23ef8bd5b8766acddffe6bca30a128458c7a5/handlers/admin_handlers.py

import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from config import settings
from database import db
from filters.admin_filter import AdminFilter
from handlers.utils import get_user_info_text, safe_send_message
from keyboards.factories import AdminCallback
from keyboards.inline import (
    admin_back_keyboard,
    admin_confirm_keyboard,
    admin_main_menu,
    admin_manage_menu,
    admin_promos_menu,
    admin_reward_details_menu,
    admin_rewards_menu,
    admin_user_info_menu,
)

router = Router()


# --- FSM States ---
class AdminState(StatesGroup):
    get_broadcast_message = State()
    confirm_broadcast = State()
    get_user_id_for_info = State()
    get_promo_name = State()
    get_promo_reward = State()
    get_promo_activations = State()
    confirm_promo_creation = State()
    get_user_id_for_grant = State()
    get_amount_for_grant = State()
    confirm_grant = State()
    get_user_id_for_debit = State()
    get_amount_for_debit = State()
    confirm_debit = State()
    get_user_id_for_fsm_reset = State()
    confirm_fsm_reset = State()
    get_rejection_reason = State()


# --- Main Panel ---
@router.message(Command("admin"), AdminFilter())
async def admin_panel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Добро пожаловать в админ-панель!", reply_markup=admin_main_menu()
    )


@router.callback_query(AdminCallback.filter(F.action == "main_panel"), AdminFilter())
async def admin_panel_callback_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.message:
        await callback.message.edit_text(
            "Добро пожаловать в админ-панель!", reply_markup=admin_main_menu()
        )
    await callback.answer()


# --- Broadcast Section ---
@router.callback_query(AdminCallback.filter(F.action == "broadcast"), AdminFilter())
async def broadcast_start_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.get_broadcast_message)
    if callback.message:
        await callback.message.edit_text(
            "Введите сообщение для рассылки. Поддерживается HTML-разметка.",
            reply_markup=admin_back_keyboard(),
        )
    await callback.answer()


@router.message(AdminState.get_broadcast_message)
async def broadcast_message_handler(message: Message, state: FSMContext):
    if not message.text:
        return
    await state.update_data(broadcast_text=message.html_text)
    await state.set_state(AdminState.confirm_broadcast)
    await message.answer(
        f"<b>Предпросмотр рассылки:</b>\n\n{message.html_text}",
        reply_markup=admin_confirm_keyboard(action="broadcast"),
    )


@router.callback_query(
    AdminCallback.filter(F.action == "broadcast_confirm"), AdminFilter()
)
async def broadcast_confirm_handler(
    callback: CallbackQuery, state: FSMContext, bot: Bot
):
    fsm_data = await state.get_data()
    text = fsm_data.get("broadcast_text")
    await state.clear()

    if not text:
        if callback.message:
            await callback.message.edit_text(
                "Ошибка: текст рассылки не найден. Попробуйте снова.",
                reply_markup=admin_back_keyboard(),
            )
        return

    if callback.message:
        await callback.message.edit_text("⏳ Начинаю рассылку...", reply_markup=None)
    all_users = await db.get_all_users()
    sent_count = 0
    failed_count = 0

    logging.info(f"Starting broadcast for {len(all_users)} users.")

    for user_id in all_users:
        if await safe_send_message(bot, user_id, text):
            sent_count += 1
        else:
            failed_count += 1
        await asyncio.sleep(0.1)

    logging.info(f"Broadcast finished. Sent: {sent_count}, Failed: {failed_count}")

    if callback.message:
        summary = (
            f"✅ Рассылка завершена!\n\n"
            f"Отправлено: {sent_count}\n"
            f"Не удалось отправить: {failed_count}"
        )
        await callback.message.edit_text(summary, reply_markup=admin_back_keyboard())


# --- User Info Section ---
@router.callback_query(
    AdminCallback.filter(F.action == "user_info_prompt"), AdminFilter()
)
async def user_info_prompt_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.get_user_id_for_info)
    if callback.message:
        await callback.message.edit_text(
            "Введите ID или username пользователя для получения информации:",
            reply_markup=admin_back_keyboard(),
        )
    await callback.answer()


@router.message(AdminState.get_user_id_for_info)
async def user_info_process_handler(message: Message, state: FSMContext):
    user_id = None

    try:
        if message.text:
            user_id = int(message.text)
    except (ValueError, TypeError):
        if message.text:
            user_id = await db.get_user_by_username(message.text.replace("@", ""))

    logging.info(f"Admin requested info for user: {message.text} -> {user_id}")

    if not user_id or not await db.user_exists(user_id):
        await message.answer(
            "Пользователь с таким ID или username не найден.",
            reply_markup=admin_back_keyboard(),
        )
        return

    info_text = await get_user_info_text(user_id, for_admin=True)
    await message.answer(info_text, reply_markup=admin_user_info_menu())
    await state.clear()


@router.callback_query(AdminCallback.filter(F.action == "user_info"), AdminFilter())
async def user_info_callback_handler(
    callback: CallbackQuery, callback_data: AdminCallback
):
    user_id = callback_data.target_id
    if user_id and callback.message:
        info_text = await get_user_info_text(user_id, for_admin=True)
        await callback.message.edit_text(info_text, reply_markup=admin_user_info_menu())
    await callback.answer()


# --- Withdrawal Rewards Section ---
@router.callback_query(AdminCallback.filter(F.action == "rewards_list"), AdminFilter())
async def rewards_list_handler(
    callback: CallbackQuery, callback_data: AdminCallback, bot: Bot
):
    page = callback_data.page or 1
    rewards = await db.get_pending_rewards(page, settings.ADMIN_PAGE_SIZE)
    total_rewards = await db.get_pending_rewards_count()
    total_pages = (
        (total_rewards + settings.ADMIN_PAGE_SIZE - 1) // settings.ADMIN_PAGE_SIZE
    ) or 1

    if not rewards:
        if callback.message:
            await callback.message.edit_text(
                "Нет активных заявок на вывод.", reply_markup=admin_back_keyboard()
            )
        await callback.answer()
        return

    bot_info = await bot.get_me()
    bot_username = bot_info.username

    text = f"Активные заявки на вывод ({total_rewards} шт.):\n\n"
    for r in rewards:
        deep_link = f"https://t.me/{bot_username}?start=reward_{r['id']}"
        text += (
            f"ID: `{r['id']}` | Сумма: {r['stars_cost']} ⭐\n"
            f"Юзер: `{r['user_id']}` ({r.get('username', 'N/A')})\n"
            f"— [Посмотреть детали]({deep_link})\n\n"
        )
    text += f"Страница {page}/{total_pages}"

    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=admin_rewards_menu(page, total_pages),
            disable_web_page_preview=True,
        )
    await callback.answer()


@router.message(CommandStart(F.args.startswith("reward_")), AdminFilter())
async def reward_details_handler(
    message: Message, state: FSMContext, command: CommandObject
):
    await state.clear()
    try:
        if not command.args:
            raise ValueError("No args")
        reward_id = int(command.args.split("_")[1])
        details = await db.get_reward_full_details(reward_id)
        if not details:
            await message.answer("Заявка не найдена.")
            return

        reward = details["reward"]
        text = (
            f"Детали заявки ID: `{reward['id']}`\n\n"
            f"Пользователь: {reward['full_name']} (`{reward['user_id']}`)\n"
            f"Сумма: {reward['stars_cost']} ⭐\n"
            f"Статус: {reward['status']}\n"
            f"Дата: {reward['created_at']}"
        )
        await message.answer(
            text,
            reply_markup=admin_reward_details_menu(reward["id"], reward["user_id"]),
        )
    except (IndexError, ValueError):
        await message.answer("Неверный формат ссылки.")


@router.callback_query(
    AdminCallback.filter(F.action == "reward_approve"), AdminFilter()
)
async def reward_approve_handler(
    callback: CallbackQuery, callback_data: AdminCallback, bot: Bot
):
    reward_id = callback_data.target_id
    if not reward_id:
        return

    success = await db.approve_reward(reward_id, callback.from_user.id)
    if success:
        logging.info(f"Reward {reward_id} approved by {callback.from_user.id}")
        reward_details = await db.get_reward_full_details(reward_id)
        if reward_details:
            reward = reward_details["reward"]
            await safe_send_message(
                bot,
                reward["user_id"],
                f"Пополнение баланса: +{reward['stars_cost']} звёзды 🌟 (Maniac Clic)",
            )
        await callback.answer("Заявка одобрена.", show_alert=True)
        await rewards_list_handler(
            callback, AdminCallback(action="rewards_list", page=1), bot
        )
    else:
        logging.warning(f"Failed to approve reward {reward_id} (already processed?)")
        await callback.answer(
            "Не удалось одобрить заявку (возможно, уже обработана).", show_alert=True
        )


@router.callback_query(AdminCallback.filter(F.action == "reward_reject"), AdminFilter())
async def reward_reject_start_handler(
    callback: CallbackQuery, callback_data: AdminCallback, state: FSMContext
):
    await state.set_state(AdminState.get_rejection_reason)
    await state.update_data(reward_id_to_reject=callback_data.target_id)
    if callback.message:
        await callback.message.edit_text("Введите причину отклонения:")
    await callback.answer()


@router.message(AdminState.get_rejection_reason, F.text)
async def reward_reject_reason_handler(message: Message, state: FSMContext, bot: Bot):
    if not message.text:
        return
    fsm_data = await state.get_data()
    reward_id = fsm_data.get("reward_id_to_reject")
    reason = message.text
    if not reward_id or not reason:
        return

    success = await db.reject_reward(reward_id, message.from_user.id, reason)

    if success:
        logging.info(
            f"Reward {reward_id} rejected by {message.from_user.id}. Reason: {reason}"
        )
        reward_details = await db.get_reward_full_details(reward_id)
        if reward_details:
            reward = reward_details["reward"]
            await safe_send_message(
                bot,
                reward["user_id"],
                f"❌ Ваша заявка #{reward_id} на вывод {reward['stars_cost']} ⭐ была отклонена. Причина: {reason}. Средства возвращены на баланс.",
            )
        await message.answer(f"Заявка #{reward_id} отклонена.")
    else:
        logging.warning(f"Failed to reject reward {reward_id} (already processed?)")
        await message.answer(
            f"Не удалось отклонить заявку #{reward_id} (возможно, уже обработана)."
        )

    await state.clear()
    await admin_panel_handler(message, state)


@router.callback_query(
    AdminCallback.filter(F.action == "reward_fulfill"), AdminFilter()
)
async def reward_fulfill_handler(
    callback: CallbackQuery, callback_data: AdminCallback, bot: Bot
):
    reward_id = callback_data.target_id
    if not reward_id:
        return

    success = await db.fulfill_reward(reward_id, callback.from_user.id)
    if success:
        logging.info(f"Reward {reward_id} fulfilled by {callback.from_user.id}")
        reward_details = await db.get_reward_full_details(reward_id)
        if reward_details:
            reward = reward_details["reward"]
            await safe_send_message(
                bot,
                reward["user_id"],
                f"🎉 Ваша заявка #{reward_id} на вывод {reward['stars_cost']} ⭐ была выполнена!",
            )
        await callback.answer("Заявка отмечена как выполненная.", show_alert=True)
        await rewards_list_handler(
            callback, AdminCallback(action="rewards_list", page=1), bot
        )
    else:
        logging.warning(f"Failed to fulfill reward {reward_id} (already processed?)")
        await callback.answer(
            "Не удалось выполнить заявку (возможно, уже обработана).", show_alert=True
        )


# --- Stats Section ---
@router.callback_query(AdminCallback.filter(F.action == "stats"), AdminFilter())
async def stats_handler(callback: CallbackQuery):
    if not callback.message:
        await callback.answer()
        return
    try:
        stats = await db.get_bot_statistics()
        logging.info(f"Admin {callback.from_user.id} requested stats")

        text = (
            f"📊 <b>Статистика бота:</b>\n\n"
            f"👤 Всего пользователей: <b>{stats['total_users']}</b>\n"
            f"☀️ Новых за 24ч: <b>{stats['new_today']}</b>\n"
            f"📅 Новых за неделю: <b>{stats['new_week']}</b>\n"
            f"👀 Активных за 24ч: <b>{stats['active_day']}</b>\n"
            f"💰 Общий банк звезд: <b>{stats['total_balance']}</b> ⭐"
        )
        await callback.message.edit_text(text, reply_markup=admin_back_keyboard())
    except Exception:
        logging.exception("Failed to load statistics")
        await callback.message.edit_text(
            "❌ Не удалось загрузить статистику. Проверьте логи.",
            reply_markup=admin_back_keyboard(),
        )
    finally:
        await callback.answer()


# --- Promo Section ---
@router.callback_query(AdminCallback.filter(F.action == "promos"), AdminFilter())
async def promos_menu_handler(callback: CallbackQuery):
    if callback.message:
        await callback.message.edit_text(
            "Раздел управления промокодами.", reply_markup=admin_promos_menu()
        )
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "promo_create"), AdminFilter())
async def promo_create_start_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.get_promo_name)
    if callback.message:
        await callback.message.edit_text(
            "Введите название нового промокода (ЗАГЛАВНЫМИ БУКВАМИ):",
            reply_markup=admin_back_keyboard(),
        )
    await callback.answer()


@router.message(AdminState.get_promo_name)
async def promo_name_handler(message: Message, state: FSMContext):
    if not message.text:
        return
    promo_name = message.text.upper()
    if await db.get_promocode(promo_name):
        await message.answer(
            "Промокод с таким названием уже существует. Попробуйте другое.",
            reply_markup=admin_back_keyboard(),
        )
        return
    await state.update_data(promo_name=promo_name)
    await state.set_state(AdminState.get_promo_reward)
    await message.answer("Введите сумму награды (целое число):")


@router.message(AdminState.get_promo_reward)
async def promo_reward_handler(message: Message, state: FSMContext):
    if not message.text:
        return
    try:
        reward = int(message.text)
        if reward <= 0:
            raise ValueError
        await state.update_data(promo_reward=reward)
        await state.set_state(AdminState.get_promo_activations)
        await message.answer("Введите количество активаций (целое число):")
    except (ValueError, TypeError):
        await message.answer("Неверный формат. Введите положительное целое число.")


@router.message(AdminState.get_promo_activations)
async def promo_activations_handler(message: Message, state: FSMContext):
    if not message.text:
        return
    try:
        activations = int(message.text)
        if activations < 0:
            raise ValueError
        await state.update_data(promo_activations=activations)
        fsm_data = await state.get_data()

        text = (
            f"Подтвердите создание промокода:\n\n"
            f"Название: `{fsm_data['promo_name']}`\n"
            f"Награда: {fsm_data['promo_reward']} ⭐\n"
            f"Активации: {fsm_data['promo_activations']}"
        )
        await state.set_state(AdminState.confirm_promo_creation)
        await message.answer(
            text, reply_markup=admin_confirm_keyboard(action="promo_create")
        )
    except (ValueError, TypeError):
        await message.answer("Неверный формат. Введите целое число.")


@router.callback_query(
    AdminCallback.filter(F.action == "promo_create_confirm"), AdminFilter()
)
async def promo_create_confirm_handler(callback: CallbackQuery, state: FSMContext):
    fsm_data = await state.get_data()
    if not all(
        k in fsm_data for k in ["promo_name", "promo_reward", "promo_activations"]
    ):
        if callback.message:
            await callback.message.edit_text(
                "Ошибка: не все данные были введены. Попробуйте снова."
            )
        await state.clear()
        return

    await db.add_promo_code(
        fsm_data["promo_name"], fsm_data["promo_reward"], fsm_data["promo_activations"]
    )
    await state.clear()

    logging.info(
        f"Admin {callback.from_user.id} created promo code {fsm_data['promo_name']}"
    )

    if callback.message:
        await callback.message.edit_text(
            f"✅ Промокод `{fsm_data['promo_name']}` успешно создан.",
            reply_markup=admin_back_keyboard(),
        )
    await callback.answer()


# --- Manage Section ---
@router.callback_query(AdminCallback.filter(F.action == "manage"), AdminFilter())
async def manage_menu_handler(callback: CallbackQuery):
    if callback.message:
        await callback.message.edit_text(
            "Раздел управления пользователями.", reply_markup=admin_manage_menu()
        )
    await callback.answer()


# --- Grant ---
@router.callback_query(AdminCallback.filter(F.action == "grant"), AdminFilter())
async def grant_start_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.get_user_id_for_grant)
    if callback.message:
        await callback.message.edit_text(
            "Введите ID пользователя для начисления:",
            reply_markup=admin_back_keyboard(),
        )
    await callback.answer()


@router.message(AdminState.get_user_id_for_grant)
async def grant_user_id_handler(message: Message, state: FSMContext):
    try:
        if not message.text:
            raise ValueError
        user_id = int(message.text)
        if not await db.user_exists(user_id):
            await message.answer("Пользователь не найден.")
            return
        await state.update_data(target_id=user_id)
        await state.set_state(AdminState.get_amount_for_grant)
        await message.answer("Введите сумму для начисления:")
    except (ValueError, TypeError):
        await message.answer("Неверный формат ID.")


@router.message(AdminState.get_amount_for_grant)
async def grant_amount_handler(message: Message, state: FSMContext):
    try:
        if not message.text:
            raise ValueError
        amount = int(message.text)
        if amount <= 0:
            raise ValueError
        fsm_data = await state.get_data()
        await state.update_data(amount=amount)
        await state.set_state(AdminState.confirm_grant)
        await message.answer(
            f"Начислить {amount} ⭐ пользователю `{fsm_data['target_id']}`?",
            reply_markup=admin_confirm_keyboard("grant", fsm_data["target_id"], amount),
        )
    except (ValueError, TypeError):
        await message.answer("Неверный формат суммы.")


@router.callback_query(AdminCallback.filter(F.action == "grant_confirm"), AdminFilter())
async def grant_confirm_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    fsm_data = await state.get_data()
    target_id = fsm_data.get("target_id")
    amount = fsm_data.get("amount")
    if not target_id or not amount:
        return

    logging.info(f"Admin {callback.from_user.id} granting {amount} to {target_id}")

    await db.add_balance_unrestricted(
        target_id, amount, "admin_grant", ref_id=str(callback.from_user.id)
    )
    await safe_send_message(bot, target_id, f"Администратор начислил вам {amount} ⭐.")
    await state.clear()
    if callback.message:
        await callback.message.edit_text(
            f"✅ Успешно начислено {amount} ⭐ пользователю `{target_id}`.",
            reply_markup=admin_back_keyboard(),
        )
    await callback.answer()


# --- Debit ---
@router.callback_query(AdminCallback.filter(F.action == "debit"), AdminFilter())
async def debit_start_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.get_user_id_for_debit)
    if callback.message:
        await callback.message.edit_text(
            "Введите ID пользователя для списания:", reply_markup=admin_back_keyboard()
        )
    await callback.answer()


@router.message(AdminState.get_user_id_for_debit)
async def debit_user_id_handler(message: Message, state: FSMContext):
    try:
        if not message.text:
            raise ValueError
        user_id = int(message.text)
        if not await db.user_exists(user_id):
            await message.answer("Пользователь не найден.")
            return
        await state.update_data(target_id=user_id)
        await state.set_state(AdminState.get_amount_for_debit)
        await message.answer("Введите сумму для списания:")
    except (ValueError, TypeError):
        await message.answer("Неверный формат ID.")


@router.message(AdminState.get_amount_for_debit)
async def debit_amount_handler(message: Message, state: FSMContext):
    try:
        if not message.text:
            raise ValueError
        amount = int(message.text)
        if amount <= 0:
            raise ValueError
        fsm_data = await state.get_data()
        balance = await db.get_user_balance(fsm_data["target_id"])
        if amount > balance:
            await message.answer(
                f"Нельзя списать больше, чем есть у пользователя на балансе ({balance} ⭐)."
            )
            return

        await state.update_data(amount=amount)
        await state.set_state(AdminState.confirm_debit)
        await message.answer(
            f"Списать {amount} ⭐ у пользователя `{fsm_data['target_id']}`?",
            reply_markup=admin_confirm_keyboard("debit", fsm_data["target_id"], amount),
        )
    except (ValueError, TypeError):
        await message.answer("Неверный формат суммы.")


@router.callback_query(AdminCallback.filter(F.action == "debit_confirm"), AdminFilter())
async def debit_confirm_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    fsm_data = await state.get_data()
    target_id = fsm_data.get("target_id")
    amount = fsm_data.get("amount")
    if not target_id or not amount:
        return

    logging.info(f"Admin {callback.from_user.id} debiting {amount} from {target_id}")

    await db.spend_balance(
        target_id, amount, "admin_debit", ref_id=str(callback.from_user.id)
    )
    await safe_send_message(bot, target_id, f"Администратор списал у вас {amount} ⭐.")
    await state.clear()
    if callback.message:
        await callback.message.edit_text(
            f"✅ Успешно списано {amount} ⭐ у пользователя `{target_id}`.",
            reply_markup=admin_back_keyboard(),
        )
    await callback.answer()


# --- FSM Reset ---
@router.callback_query(AdminCallback.filter(F.action == "reset_fsm"), AdminFilter())
async def reset_fsm_start_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.get_user_id_for_fsm_reset)
    if callback.message:
        await callback.message.edit_text(
            "Введите ID пользователя для сброса состояния (FSM):",
            reply_markup=admin_back_keyboard(),
        )
    await callback.answer()


@router.message(AdminState.get_user_id_for_fsm_reset)
async def reset_fsm_user_id_handler(message: Message, state: FSMContext):
    try:
        if not message.text:
            raise ValueError
        user_id = int(message.text)
        if not await db.user_exists(user_id):
            await message.answer("Пользователь не найден.")
            return
        await state.update_data(target_id=user_id)
        await state.set_state(AdminState.confirm_fsm_reset)
        await message.answer(
            f"Вы уверены, что хотите сбросить состояние для пользователя `{user_id}`?",
            reply_markup=admin_confirm_keyboard("reset_fsm", user_id),
        )
    except (ValueError, TypeError):
        await message.answer("Неверный формат ID.")


@router.callback_query(
    AdminCallback.filter(F.action == "reset_fsm_confirm"), AdminFilter()
)
async def reset_fsm_confirm_handler(callback: CallbackQuery, state: FSMContext):
    fsm_data = await state.get_data()
    target_id = fsm_data.get("target_id")
    if not target_id:
        return
    bot_id = state.key.bot_id

    logging.info(f"Admin {callback.from_user.id} resetting FSM for {target_id}")

    user_fsm_context = FSMContext(
        storage=state.storage,
        key=state.key.__class__(bot_id=bot_id, chat_id=target_id, user_id=target_id),
    )
    await user_fsm_context.clear()

    await state.clear()
    if callback.message:
        await callback.message.edit_text(
            f"✅ Состояние для пользователя `{target_id}` успешно сброшено.",
            reply_markup=admin_back_keyboard(),
        )
    await callback.answer()
