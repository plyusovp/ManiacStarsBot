# handlers/admin_handlers.py
import html
import re
from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from config import settings
from database import db
from lexicon.texts import ECONOMY_ERROR_MESSAGES, LEXICON

from keyboards.inline import (admin_main_menu, admin_manage_menu,
                              admin_promos_menu, admin_reward_details_menu,
                              admin_rewards_menu)

router = Router()
router.message.filter(F.from_user.id.in_(settings.ADMIN_IDS))
router.callback_query.filter(F.from_user.id.in_(settings.ADMIN_IDS))


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


@router.message(Command("admin"))
async def admin_panel_handler(message: Message):
    await message.answer("Добро пожаловать в админ-панель!", reply_markup=admin_main_menu())


@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback_handler(callback: CallbackQuery):
    await callback.message.edit_text("Добро пожаловать в админ-панель!", reply_markup=admin_main_menu())


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
        text,
        reply_markup=admin_rewards_menu(page, total_pages)
    )


@router.callback_query(F.data.startswith("admin_rewards_page_"))
async def admin_rewards_page_handler(callback: CallbackQuery, state: FSMContext):
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
        text,
        reply_markup=admin_rewards_menu(page, total_pages)
    )


# --- ИЗМЕНЕНО: Исправлен фильтр для команды ---
@router.message(Command(re.compile(r"reward_\d+")))
async def reward_details_command_handler(message: Message, state: FSMContext):
    try:
        # Логика извлечения ID из текста команды
        reward_id = int(message.text.split("_")[1])
    except (ValueError, IndexError):
        return await message.answer("Неверный формат команды.")
# --- КОНЕЦ ИЗМЕНЕНИЙ ---

    details = await db.get_reward_full_details(reward_id)
    if not details:
        return await message.answer(f"Заявка #{reward_id} не найдена.")

    reward = details["reward"]
    user = details["reward"] 
    ledger = details["ledger"]

    ledger_text = "\n".join([f"• {l['amount']}⭐ за `{l['reason']}` ({l['created_at']})" for l in ledger])

    text = (
        f"<b>Детали заявки #{reward_id}</b>\n\n"
        f"<b>Пользователь:</b> @{user['username']} (<code>{user['user_id']}</code>)\n"
        f"<b>Имя:</b> {html.escape(user['full_name'])}\n"
        f"<b>Статус заявки:</b> {reward['status']}\n"
        f"<b>Запрошено:</b> {reward['item_id']} за {reward['stars_cost']} ⭐\n"
        f"<b>Дата создания:</b> {reward['created_at']}\n\n"
        f"<b>Баланс юзера:</b> {user['balance']} ⭐\n"
        f"<b>Дата регистрации:</b> {user['registration_date']}\n"
        f"<b>Уровень риска:</b> {user['risk_level']}\n\n"
        f"<b>Последние транзакции:</b>\n{ledger_text}"
    )

    await message.answer(
        text,
        reply_markup=admin_reward_details_menu(reward_id, user['user_id'])
    )


@router.callback_query(F.data.startswith("admin_reward_"))
async def reward_action_handler(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split("_")
    action = parts[2]
    reward_id = int(parts[3])
    admin_id = callback.from_user.id

    details = await db.get_reward_full_details(reward_id)
    if not details:
        return await callback.answer("Заявка не найдена.", show_alert=True)
    
    user_id = details['reward']['user_id']
    username = details['reward']['username']
    
    success = False
    notify_text = ""

    if action == "approve":
        success = await db.approve_reward(reward_id, admin_id)
        notify_text = f"✅ Ваша заявка #{reward_id} была одобрена администратором. Ожидайте выдачи."
    elif action == "reject":
        success = await db.reject_reward(reward_id, admin_id, "Отклонено администратором")
        notify_text = f"❌ Ваша заявка #{reward_id} была отклонена. Звёзды возвращены на ваш баланс."
    elif action == "fulfill":
        success = await db.fulfill_reward(reward_id, admin_id)
        notify_text = f"🎉 Ваша заявка #{reward_id} выполнена! Подарок отправлен."

    if success:
        await callback.answer(f"Статус заявки #{reward_id} изменен на '{action}'.", show_alert=True)
        try:
            await bot.send_message(user_id, notify_text)
        except Exception as e:
            await callback.message.answer(f"Не удалось уведомить пользователя @{username}: {e}")
        await admin_rewards_handler(callback, FSMContext(storage=router.fsm.storage, key=callback.message.chat.id, bot=bot, data={})) # Обновляем список
    else:
        await callback.answer("Не удалось изменить статус. Возможно, он уже был изменен.", show_alert=True)


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
    await callback.message.edit_text("Введите название нового промокода (например, `NEWYEAR2024`):")
    await state.set_state(Promo.waiting_for_name)


@router.message(Promo.waiting_for_name)
async def process_promo_name(message: Message, state: FSMContext):
    await state.update_data(promo_name=message.text.strip().upper())
    await message.answer("Отлично. Теперь введите количество звёзд, которое он даёт (например, `10`):")
    await state.set_state(Promo.waiting_for_reward)


@router.message(Promo.waiting_for_reward)
async def process_promo_reward(message: Message, state: FSMContext):
    try:
        reward = int(message.text)
        if reward <= 0: raise ValueError
        await state.update_data(promo_reward=reward)
        await message.answer("Хорошо. Теперь введите общее количество активаций (например, `100`):")
        await state.set_state(Promo.waiting_for_uses)
    except ValueError:
        await message.answer("Неверное число. Введите целое положительное число.")


@router.message(Promo.waiting_for_uses)
async def process_promo_uses(message: Message, state: FSMContext):
    try:
        uses = int(message.text)
        if uses <= 0: raise ValueError
        data = await state.get_data()
        name = data['promo_name']
        reward = data['promo_reward']
        
        await db.add_promo_code(name, reward, uses)
        await message.answer(f"✅ Промокод `{name}` на {reward} ⭐ ({uses} активаций) успешно создан!")
        await state.clear()
    except ValueError:
        await message.answer("Неверное число. Введите целое положительное число.")


@router.callback_query(F.data == "admin_manage")
async def admin_manage_handler(callback: CallbackQuery):
    await callback.message.edit_text("Выберите действие:", reply_markup=admin_manage_menu())


@router.callback_query(F.data.in_({"admin_grant", "admin_debit"}))
async def manage_balance_start(callback: CallbackQuery, state: FSMContext):
    is_debit = callback.data == "admin_debit"
    await state.update_data(is_debit=is_debit)
    action_word = "списания" if is_debit else "начисления"
    await callback.message.edit_text(f"Введите ID или @username пользователя для {action_word}:")
    await state.set_state(ManageBalance.waiting_for_user)


@router.message(ManageBalance.waiting_for_user)
async def process_manage_user(message: Message, state: FSMContext):
    user_input = message.text.strip()
    user_id = None
    if user_input.isdigit():
        user_id = int(user_input)
    elif user_input.startswith('@'):
        user_id = await db.get_user_by_username(user_input[1:])
    
    if not user_id:
        await message.answer("Пользователь не найден. Попробуйте еще раз.")
        return
    
    await state.update_data(target_user_id=user_id)
    await message.answer("Теперь введите сумму (целое положительное число):")
    await state.set_state(ManageBalance.waiting_for_amount)


@router.message(ManageBalance.waiting_for_amount)
async def process_manage_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
        if amount <= 0: raise ValueError
    except ValueError:
        await message.answer("Неверная сумма. Введите целое положительное число.")
        return

    data = await state.get_data()
    user_id = data['target_user_id']
    is_debit = data['is_debit']
    admin_id = message.from_user.id

    if is_debit:
        success = await db.spend_balance(user_id, amount, "admin_debit", ref_id=str(admin_id))
        if success:
            await message.answer(f"✅ У пользователя `{user_id}` списано {amount} ⭐.")
        else:
            await message.answer(f"❌ Не удалось списать. Недостаточно средств.")
    else:
        await db.add_balance_unrestricted(user_id, amount, "admin_grant", ref_id=str(admin_id))
        await message.answer(f"✅ Пользователю `{user_id}` начислено {amount} ⭐.")
    
    await state.clear()
