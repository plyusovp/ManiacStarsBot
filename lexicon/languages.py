# lexicon/languages.py

from typing import Dict, Optional

# Поддерживаемые языки
SUPPORTED_LANGUAGES = {
    "ru": "🇷🇺 Русский",
    "en": "🇺🇸 English",
    "uk": "🇺🇦 Українська",
    "es": "🇪🇸 Español",
}

# Многоязычные тексты
MULTILINGUAL_TEXTS = {
    "ru": {
        "start_message": "👋 **Привет, {full_name}!**\n\nДобро пожаловать в **Maniac Stars** — место где можно заработать и поиграть!\n\n🎯 **Что здесь есть:**\n• 💰 Заработок через рефералов\n• 🎮 Мини-игры на ставки\n• 🏆 Система достижений\n• 🎁 Призы за активность\n\nВыбери что тебя интересует ⬇️",
        "main_menu": "**⚔️ Maniac Stars ⚔️**\n\nИспользуй кнопки ниже для навигации.\n\n**💰 Баланс: {balance} ⭐**",
        "games_menu": "🎮 **Выберите игру** 🎮\n\nА также кликайте звезды в нашем бесплатном кликере! ⭐",
        "profile": "👤 **Твой профиль**\n\n"
        "**Имя:** {full_name}\n"
        "**ID:** `{user_id}`\n"
        "**Уровень:** {level_name}\n\n"
        "📈 **Статистика:**\n"
        "• Приглашено: {referrals_count} чел.\n"
        "• Дуэли: {duel_wins} побед / {duel_losses} поражений\n"
        "• Стрик: {streak_days} дней подряд\n"
        "• Баланс: {balance} ⭐\n\n"
        "{status_text}",
        "profile_status": "**Статус аккаунта:**\n{quarantine_status}{cooldown_status}",
        "referral_menu": "💰 **Заработок через рефералов** 💰\n\n"
        "Приглашай друзей и получай **+{ref_bonus} ⭐** за каждого!\n\n"
        "🔗 **Твоя реферальная ссылка:**\n"
        "`{ref_link}`\n\n"
        "✅ **Приглашено:** {invited_count} чел.\n"
        "📊 **Заработано:** {earned} ⭐",
        "referral_success_notification": "{username} присоединился по вашей ссылке! Вам начислено +{bonus} ⭐.",
        "top_menu": "🏆 **Лидеры по рефералам** 🏆\n\n{top_users_text}",
        "gifts_menu": "🎁 **Призы** 🎁\n\n"
        "Обменивай свои ⭐ на подарки! Для получения призов нужно пригласить минимум {min_refs} друзей и подписаться на наши ресурсы.\n\n"
        "💰 **Твой баланс:** {balance} ⭐\n"
        "👥 **Приглашено:** {referrals_count} чел.\n\n"
        "Выбери подарок:",
        "resources_menu": "🎁 **Наши ресурсы** 🎁\n\n"
        "Подписка на все наши ресурсы **обязательна** для вывода подарков. "
        "Подпишись, чтобы не пропустить важные анонсы и подтверждения выводов!",
        "gift_confirm": "Вы уверены, что хотите обменять **{cost} ⭐** на **{emoji} {name}**?\n\n"
        "Это действие нельзя будет отменить.",
        "withdrawal_success": "✅ Ваша заявка на вывод **{emoji} {name}** ({amount} ⭐) успешно создана! Администратор рассмотрит её в ближайшее время.",
        "promo_prompt": "🎟️ Введите ваш промокод:",
        "promo_success": "✅ Промокод успешно активирован! Вам начислено: {amount} ⭐",
        "promo_fail": "❌ Не удалось активировать промокод. Причина: {reason}",
        "entertainment_menu": "👾 **Развлечения** 👾\n\nВыбери, во что хочешь сыграть, или введи промокод.",
        "language_selection": "🌍 **Выберите язык** 🌍\n\nВыберите предпочитаемый язык для бота:",
        "language_changed": "✅ Язык изменен на {language}!",
        "settings_menu": "⚙️ **Настройки** ⚙️\n\nВыберите действие:",
        "current_language": "🌍 **Текущий язык:** {language}",
        "back_to_menu": "⬅️ Назад в меню",
        "back_to_profile": "⬅️ Назад в профиль",
        "back_to_games": "⬅️ Назад к играм",
        "back_to_gifts": "⬅️ Назад к подаркам",
        "cancel": "❌ Отмена",
        "confirm": "✅ Подтвердить",
        # Кнопки меню
        "earn_button": "Заработать",
        "games_button": "Развлечения",
        "profile_button": "Профиль",
        "gifts_button": "Призы",
        "leaders_button": "Лидеры",
        "resources_button": "Наши ресурсы",
        "achievements_button": "Достижения",
        "settings_button": "Настройки",
        "change_language": "Сменить язык",
        "error_unknown": "🔧 Произошла непредвиденная ошибка. Мы уже работаем над этим. Попробуйте, пожалуйста, позже.",
        "error_db": "🗄️ Ошибка при обращении к базе данных. Пожалуйста, повторите ваш запрос через несколько минут.",
        "error_timeout": "⏳ Сервер слишком долго отвечал. Возможно, временные неполадки. Попробуйте еще раз.",
        "error_not_subscribed": "❌ **Подписка не найдена!**\nДля вывода необходимо быть подписанным на все наши ресурсы. Проверьте подписки в разделе '🎁 Наши ресурсы'.",
        "error_not_enough_referrals": "❌ **Недостаточно друзей!**\nДля вывода нужно пригласить минимум {min_refs} друзей (у вас {current_refs}).",
        "gift_requirements_not_met": "Для вывода этого подарка не выполнены следующие условия:\n{errors}",
        "insufficient_funds": "Недостаточно средств на балансе.",
        "daily_cap_exceeded": "Достигнут дневной лимит на получение звёзд из этого источника.",
        "rate_limit_minute": "Слишком часто! Попробуйте через минуту.",
        "rate_limit_hour": "Достигнут часовой лимит. Попробуйте позже.",
        "user_in_quarantine": "Новые пользователи не могут выводить средства в течение 24 часов после регистрации.",
        "withdraw_cooldown": "Вывод временно недоступен после крупного выигрыша. Попробуйте через {hours}ч {minutes}м.",
        "rewards_disabled": "Вывод временно отключен администрацией.",
        "daily_ops_limit": "Вы достигли лимита на количество заявок в день.",
        "daily_amount_limit": "Вы достигли лимита на сумму вывода в день.",
        "not_subscribed": "Для этого действия необходимо быть подписанным на наш канал!",
        "not_enough_referrals": "Для вывода нужно пригласить минимум {min_refs} друзей (у вас {current_refs}).",
        "unknown_error": "Произошла неизвестная ошибка. Попробуйте позже.",
        "subscription_welcome": "🎉 **Добро пожаловать в Maniac Stars!**\n\nПодписка подтверждена! Теперь вы можете пользоваться всеми функциями бота.",
        "subscription_admin_welcome": "👑 **Добро пожаловать, администратор!**\n\nУ вас есть полный доступ ко всем функциям бота.",
        "subscription_required": "🔒 **Подписка обязательна**\n\nДля использования бота необходимо подписаться на наш канал.",
        "subscription_success": "✅ **Подписка подтверждена!**\n\nДобро пожаловать в бота!",
        "subscription_failed": "❌ **Подписка не найдена**\n\nПожалуйста, подпишитесь на канал и попробуйте снова.",
        # --- Game Texts ---
        "coinflip_menu": "🪙 **Орёл и Решка** 🪙\n\n"
        "Рискни и умножь свой выигрыш! Угадай, какая сторона выпадет.\n"
        "С каждым следующим выигрышем шанс уменьшается, а приз растет!\n\n"
        "💰 **Ваш баланс:** {balance} ⭐\n\nВыберите ставку:",
        "coinflip_process": "🪙 Подбрасываем монетку...",
        "coinflip_choice_prompt": "🎉 **Ставка {stake} ⭐ принята!** 🎉\n\n"
        "Что выбираешь?",
        "coinflip_continue": "🎉 **Победа!** 🎉\n\n"
        "Вы выиграли **{current_prize}** ⭐.\n"
        "Следующий бросок может принести **{next_prize}** ⭐ с шансом {next_chance}%.\n\n"
        "Рискнёте?",
        "coinflip_win_final": "🎉 **Поздравляем!** 🎉\n\n"
        "Вы забираете выигрыш: {prize} ⭐\n"
        "💰 Ваш новый баланс: {new_balance} ⭐",
        "coinflip_loss": "😕 **Увы, неудача...**\n\n"
        "Вы проиграли свою ставку: {stake} ⭐\n"
        "💰 Ваш новый баланс: {new_balance} ⭐",
        "slots_menu": "🎰 **Слоты** 🎰\n\nИспытай свою удачу! Собери три одинаковых символа в ряд, чтобы выиграть.\n\n💰 **Ваш баланс:** {balance} ⭐\n\nВыберите ставку:",
        "slots_win": "🎉 **ПОБЕДА!** 🎉\n\nВы выиграли {prize} ⭐!\n💰 Ваш новый баланс: {new_balance} ⭐",
        "slots_lose": "😕 **Увы, не повезло...**\n\nВы проиграли {cost} ⭐.\n💰 Ваш новый баланс: {new_balance} ⭐",
        "football_menu": "⚽️ **Футбол** ⚽️\n\nПробей пенальти! Если забьешь гол, получишь приз.\n\n💰 **Ваш баланс:** {balance} ⭐",
        "football_win": "🎉 **ГОООЛ!** 🎉\n\nТы забил и выиграл {prize} ⭐!\n💰 Ваш новый баланс: {new_balance} ⭐",
        "football_lose": "😕 **Промах...**\n\nВы проиграли {cost} ⭐.\n💰 Ваш новый баланс: {new_balance} ⭐",
        "bowling_menu": "🎳 **Боулинг** 🎳\n\nСможешь выбить страйк? Если собьешь все кегли одним броском - получишь приз!\n\n💰 **Ваш баланс:** {balance} ⭐\n\nВыберите ставку:",
        "bowling_win": "🎉 **СТРАЙК!** 🎉\n\nОтличный бросок! Ты выиграл {prize} ⭐!\n💰 Ваш новый баланс: {new_balance} ⭐",
        "bowling_lose": "😕 **Мимо...**\n\nВ следующий раз повезет больше. Вы проиграли {cost} ⭐.\n💰 Ваш новый баланс: {new_balance} ⭐",
        "basketball_menu": "🏀 **Баскетбол** 🏀\n\nПопади мячом в корзину, чтобы выиграть приз!\n\n💰 **Ваш баланс:** {balance} ⭐",
        "basketball_win": "🎉 **Точно в цель!** 🎉\n\nОтличный бросок! Ты выиграл {prize} ⭐!\n💰 Ваш новый баланс: {new_balance} ⭐",
        "basketball_lose": "😕 **Промах...**\n\nМяч пролетел мимо. Вы проиграли {cost} ⭐.\n💰 Ваш новый баланс: {new_balance} ⭐",
        "darts_menu": "🎯 **Дартс** 🎯\n\nПопади в яблочко, чтобы выиграть приз!\n\n💰 **Ваш баланс:** {balance} ⭐",
        "darts_win": "🎉 **Точно в цель!** 🎉\n\nОтличный бросок! Ты выиграл {prize} ⭐!\n💰 Ваш новый баланс: {new_balance} ⭐",
        "darts_lose": "😕 **Мимо...**\n\nДротик пролетел мимо. Вы проиграли {cost} ⭐.\n💰 Ваш новый баланс: {new_balance} ⭐",
        "dice_menu": "🎲 **Кости** 🎲\n\nУгадай, в каком диапазоне выпадет число на кубике! Ставь на (1-3) или (4-6).\n\n💰 **Ваш баланс:** {balance} ⭐",
        "dice_win": "🎉 **Победа!** 🎉\n\nТы поставил на ({choice}), а выпало число {value}! Ты выиграл {prize} ⭐!\n💰 Ваш новый баланс: {new_balance} ⭐",
        "dice_lose": "😕 **Увы, не угадал...**\n\nТы поставил на ({choice}), а выпало число {value}. Вы проиграли {cost} ⭐.\n💰 Ваш новый баланс: {new_balance} ⭐",
        # --- Transaction Texts ---
        "transactions_title": "📊 **История транзакций** 📊\n\n💰 **Текущий баланс:** {balance} ⭐\n\n📋 **Последние операции:**\n\n",
        "transactions_empty": "📊 **История транзакций** 📊\n\n💰 **Текущий баланс:** {balance} ⭐\n\n📭 **История пуста**\nПока что у вас нет транзакций. Начните играть или приглашайте друзей!",
        "transaction_item": "{emoji} **{amount_text}** - {reason_text}\n📅 {date}\n",
        # --- Social Content Texts ---
        "social_content": "📱 **ГОТОВЫЙ КОНТЕНТ ДЛЯ РЕПОСТОВ** 📱\n\n🎯 **Выберите платформу:**",
        "tiktok_content": "🎵 КОНТЕНТ ДЛЯ TIKTOK 🎵\n\n📝 Готовые тексты:\n\n🔥 Нашел способ зарабатывать в Telegram! За день уже {balance} ⭐. Кто со мной? {ref_link}\n\n💎 Этот бот платит реальные деньги за игры! Уже вывел {balance} ⭐. {ref_link}\n\n⚡ Пока все спят, я зарабатываю в Telegram! {balance} ⭐ за сегодня. Кто готов к заработку? {ref_link}\n\n🎯 Хештеги:\n\\#заработок \\#telegram \\#деньги \\#игры \\#рефералы \\#пассивныйдоход",
        "instagram_content": "📸 КОНТЕНТ ДЛЯ INSTAGRAM 📸\n\n📝 Готовые тексты:\n\n🌟 Новый способ заработка в Telegram! За неделю уже {balance} ⭐. Кто готов попробовать? {ref_link}\n\n💰 Этот бот реально платит! Уже вывел {balance} ⭐. {ref_link}\n\n🎮 Зарабатываю играя в Telegram! {balance} ⭐ за сегодня. Кто со мной? {ref_link}\n\n🎯 Хештеги:\n\\#заработок \\#telegram \\#деньги \\#игры \\#рефералы \\#пассивныйдоход \\#workfromhome",
        "telegram_content": "📱 КОНТЕНТ ДЛЯ TELEGRAM 📱\n\n📝 Готовые тексты:\n\n🚀 Ребят, нашел крутой бот для заработка! За день уже {balance} ⭐. Кто готов попробовать? {ref_link}\n\n💎 Этот бот реально платит деньги! Уже вывел {balance} ⭐. {ref_link}\n\n⚡ Пока все спят, я зарабатываю! {balance} ⭐ за сегодня. Кто со мной? {ref_link}\n\n🎯 Дополнительно:\n• Добавьте скриншот баланса\n• Покажите достижения\n• Расскажите о играх",
        "challenges_stub": "⚡ **ЧЕЛЛЕНДЖИ** ⚡\n\n🚧 **Скоро будет...**\n\nМы работаем над системой ежедневных челленджей, которые помогут вам зарабатывать еще больше звезд!\n\n💡 **Что вас ждет:**\n• Ежедневные задания\n• Бонусы за выполнение\n• Специальные награды\n• Турниры между пользователями\n\n⏰ Следите за обновлениями!",
        # Дополнительные переводы для инлайн кнопок
        "activate_promo_button": "Активировать промокод",
        "my_transactions_button": "Мои транзакции",
        "challenges_button": "Челленджи",
        "social_content_button": "Контент для репостов",
        "tiktok_button": "TikTok",
        "instagram_button": "Instagram",
        "telegram_button": "Telegram",
        "duels_button": "Дуэли",
        "timer_button": "Таймер",
        "coinflip_button": "Орёл/Решка",
        "slots_button": "Слоты",
        "football_button": "Футбол",
        "bowling_button": "Боулинг",
        "basketball_button": "Баскетбол",
        "darts_button": "Дартс",
        "dice_button": "Кости",
        "webapp_game_button": "Maniac Clic Game",
        "passive_income_button": "Пассивный доход",
        "daily_bonus_button": "Получить ежедневный бонус",
        "our_channel_button": "Наш канал",
        "our_chat_button": "Наш чат",
        "our_withdrawals_button": "Наши выводы",
        "our_manual_button": "Наш мануал",
        "tech_support_button": "Техподдержка 12:00-21:00 🆘",
        "heads_button": "Орёл",
        "tails_button": "Решка",
        "risk_button": "Рискнуть!",
        "cashout_button": "Забрать выигрыш",
        "play_again_button": "Играть снова",
        "to_other_games_button": "К другим играм",
        "training_button": "Обучение",
        "stats_button": "Статистика",
        "cancel_search_button": "Отменить поиск",
        "how_to_play_button": "Как играть?",
        "stop_button": "СТОП!",
        "surrender_button": "Сдаться",
        "boost_card_button": "Усилить карту",
        "new_cards_button": "Новые карты",
        "bet_low_button": "Поставить на 1-3",
        "bet_high_button": "Поставить на 4-6",
    },
    "en": {
        "start_message": "👋 **Hello, {full_name}!**\n\nWelcome to **Maniac Stars** — a place where you can earn and play!\n\n🎯 **What's here:**\n• 💰 Earning through referrals\n• 🎮 Mini-games with bets\n• 🏆 Achievement system\n• 🎁 Prizes for activity\n\nChoose what interests you ⬇️",
        "main_menu": "**⚔️ Maniac Stars ⚔️**\n\nUse the buttons below to navigate.\n\n**💰 Balance: {balance} ⭐**",
        "games_menu": "🎮 **Choose a game** 🎮\n\nAlso click stars in our free clicker! ⭐",
        "profile": "👤 **Your profile**\n\n"
        "**Name:** {full_name}\n"
        "**ID:** `{user_id}`\n"
        "**Level:** {level_name}\n\n"
        "📈 **Statistics:**\n"
        "• Invited: {referrals_count} people\n"
        "• Duels: {duel_wins} wins / {duel_losses} losses\n"
        "• Streak: {streak_days} days in a row\n"
        "• Balance: {balance} ⭐\n\n"
        "{status_text}",
        "profile_status": "**Account status:**\n{quarantine_status}{cooldown_status}",
        "referral_menu": "💰 **Earning through referrals** 💰\n\n"
        "Invite friends and get **+{ref_bonus} ⭐** for each!\n\n"
        "🔗 **Your referral link:**\n"
        "`{ref_link}`\n\n"
        "✅ **Invited:** {invited_count} people\n"
        "📊 **Earned:** {earned} ⭐",
        "referral_success_notification": "{username} joined via your link! You received +{bonus} ⭐.",
        "top_menu": "🏆 **Referral Leaders** 🏆\n\n{top_users_text}",
        "gifts_menu": "🎁 **Prizes** 🎁\n\n"
        "Exchange your ⭐ for gifts! To receive prizes, you need to invite at least {min_refs} friends and subscribe to our resources.\n\n"
        "💰 **Your balance:** {balance} ⭐\n"
        "👥 **Invited:** {referrals_count} people\n\n"
        "Choose a gift:",
        "resources_menu": "🎁 **Our resources** 🎁\n\n"
        "Subscription to all our resources is **mandatory** for gift withdrawals. "
        "Subscribe to not miss important announcements and withdrawal confirmations!",
        "gift_confirm": "Are you sure you want to exchange **{cost} ⭐** for **{emoji} {name}**?\n\n"
        "This action cannot be undone.",
        "withdrawal_success": "✅ Your withdrawal request for **{emoji} {name}** ({amount} ⭐) has been successfully created! The administrator will review it soon.",
        "promo_prompt": "🎟️ Enter your promo code:",
        "promo_success": "✅ Promo code successfully activated! You received: {amount} ⭐",
        "promo_fail": "❌ Failed to activate promo code. Reason: {reason}",
        "entertainment_menu": "👾 **Entertainment** 👾\n\nChoose what you want to play, or enter a promo code.",
        "language_selection": "🌍 **Choose Language** 🌍\n\nSelect your preferred language for the bot:",
        "language_changed": "✅ Language changed to {language}!",
        "settings_menu": "⚙️ **Settings** ⚙️\n\nChoose an action:",
        "current_language": "🌍 **Current language:** {language}",
        "back_to_menu": "⬅️ Back to menu",
        "back_to_profile": "⬅️ Back to profile",
        "back_to_games": "⬅️ Back to games",
        "back_to_gifts": "⬅️ Back to gifts",
        "cancel": "❌ Cancel",
        "confirm": "✅ Confirm",
        # Menu buttons
        "earn_button": "Earn",
        "games_button": "Entertainment",
        "profile_button": "Profile",
        "gifts_button": "Prizes",
        "leaders_button": "Leaders",
        "resources_button": "Our Resources",
        "achievements_button": "Achievements",
        "settings_button": "Settings",
        "change_language": "Change Language",
        "error_unknown": "🔧 An unexpected error occurred. We're already working on it. Please try again later.",
        "error_db": "🗄️ Database access error. Please repeat your request in a few minutes.",
        "error_timeout": "⏳ Server took too long to respond. There might be temporary issues. Please try again.",
        "error_not_subscribed": "❌ **Subscription not found!**\nTo withdraw, you must be subscribed to all our resources. Check subscriptions in the '🎁 Our resources' section.",
        "error_not_enough_referrals": "❌ **Not enough friends!**\nTo withdraw, you need to invite at least {min_refs} friends (you have {current_refs}).",
        "gift_requirements_not_met": "The following conditions are not met for this gift withdrawal:\n{errors}",
        "insufficient_funds": "Insufficient funds in balance.",
        "daily_cap_exceeded": "Daily limit for earning stars from this source has been reached.",
        "rate_limit_minute": "Too frequent! Try again in a minute.",
        "rate_limit_hour": "Hourly limit reached. Try again later.",
        "user_in_quarantine": "New users cannot withdraw funds within 24 hours of registration.",
        "withdraw_cooldown": "Withdrawal temporarily unavailable after a big win. Try again in {hours}h {minutes}m.",
        "rewards_disabled": "Withdrawal temporarily disabled by administration.",
        "daily_ops_limit": "You have reached the daily limit for number of requests.",
        "daily_amount_limit": "You have reached the daily limit for withdrawal amount.",
        "not_subscribed": "You must be subscribed to our channel for this action!",
        "not_enough_referrals": "To withdraw, you need to invite at least {min_refs} friends (you have {current_refs}).",
        "unknown_error": "An unknown error occurred. Please try again later.",
        "subscription_welcome": "🎉 **Welcome to Maniac Stars!**\n\nSubscription confirmed! Now you can use all bot features.",
        "subscription_admin_welcome": "👑 **Welcome, administrator!**\n\nYou have full access to all bot features.",
        "subscription_required": "🔒 **Subscription required**\n\nYou must subscribe to our channel to use the bot.",
        "subscription_success": "✅ **Subscription confirmed!**\n\nWelcome to the bot!",
        "subscription_failed": "❌ **Subscription not found**\n\nPlease subscribe to the channel and try again.",
        # --- Game Texts ---
        "coinflip_menu": "🪙 **Heads or Tails** 🪙\n\n"
        "Risk and multiply your winnings! Guess which side will come up.\n"
        "With each next win, the chance decreases and the prize grows!\n\n"
        "💰 **Your balance:** {balance} ⭐\n\nChoose your bet:",
        "coinflip_process": "🪙 Flipping coin...",
        "coinflip_choice_prompt": "🎉 **Bet {stake} ⭐ accepted!** 🎉\n\n"
        "What do you choose?",
        "coinflip_continue": "🎉 **Win!** 🎉\n\n"
        "You won **{current_prize}** ⭐.\n"
        "The next throw can bring **{next_prize}** ⭐ with {next_chance}% chance.\n\n"
        "Risk it?",
        "coinflip_win_final": "🎉 **Congratulations!** 🎉\n\n"
        "You take the winnings: {prize} ⭐\n"
        "💰 Your new balance: {new_balance} ⭐",
        "coinflip_loss": "😕 **Alas, failure...**\n\n"
        "You lost your bet: {stake} ⭐\n"
        "💰 Your new balance: {new_balance} ⭐",
        "slots_menu": "🎰 **Slots** 🎰\n\nTest your luck! Collect three identical symbols in a row to win.\n\n💰 **Your balance:** {balance} ⭐\n\nChoose your bet:",
        "slots_win": "🎉 **WIN!** 🎉\n\nYou won {prize} ⭐!\n💰 Your new balance: {new_balance} ⭐",
        "slots_lose": "😕 **Alas, no luck...**\n\nYou lost {cost} ⭐.\n💰 Your new balance: {new_balance} ⭐",
        "football_menu": "⚽️ **Football** ⚽️\n\nScore a penalty! If you score a goal, you get a prize.\n\n💰 **Your balance:** {balance} ⭐",
        "football_win": "🎉 **GOOOAL!** 🎉\n\nYou scored and won {prize} ⭐!\n💰 Your new balance: {new_balance} ⭐",
        "football_lose": "😕 **Miss...**\n\nYou lost {cost} ⭐.\n💰 Your new balance: {new_balance} ⭐",
        "bowling_menu": "🎳 **Bowling** 🎳\n\nCan you get a strike? If you knock down all pins with one throw - you get a prize!\n\n💰 **Your balance:** {balance} ⭐\n\nChoose your bet:",
        "bowling_win": "🎉 **STRIKE!** 🎉\n\nGreat throw! You won {prize} ⭐!\n💰 Your new balance: {new_balance} ⭐",
        "bowling_lose": "😕 **Miss...**\n\nBetter luck next time. You lost {cost} ⭐.\n💰 Your new balance: {new_balance} ⭐",
        "basketball_menu": "🏀 **Basketball** 🏀\n\nHit the ball into the basket to win a prize!\n\n💰 **Your balance:** {balance} ⭐",
        "basketball_win": "🎉 **Right on target!** 🎉\n\nGreat shot! You won {prize} ⭐!\n💰 Your new balance: {new_balance} ⭐",
        "basketball_lose": "😕 **Miss...**\n\nThe ball flew past. You lost {cost} ⭐.\n💰 Your new balance: {new_balance} ⭐",
        "darts_menu": "🎯 **Darts** 🎯\n\nHit the bullseye to win a prize!\n\n💰 **Your balance:** {balance} ⭐",
        "darts_win": "🎉 **Right on target!** 🎉\n\nGreat throw! You won {prize} ⭐!\n💰 Your new balance: {new_balance} ⭐",
        "darts_lose": "😕 **Miss...**\n\nThe dart flew past. You lost {cost} ⭐.\n💰 Your new balance: {new_balance} ⭐",
        "dice_menu": "🎲 **Dice** 🎲\n\nGuess in which range the number will fall on the dice! Bet on (1-3) or (4-6).\n\n💰 **Your balance:** {balance} ⭐",
        "dice_win": "🎉 **Win!** 🎉\n\nYou bet on ({choice}), and the number {value} came up! You won {prize} ⭐!\n💰 Your new balance: {new_balance} ⭐",
        "dice_lose": "😕 **Alas, didn't guess...**\n\nYou bet on ({choice}), and the number {value} came up. You lost {cost} ⭐.\n💰 Your new balance: {new_balance} ⭐",
        # --- Transaction Texts ---
        "transactions_title": "📊 **Transaction History** 📊\n\n💰 **Current balance:** {balance} ⭐\n\n📋 **Recent operations:**\n\n",
        "transactions_empty": "📊 **Transaction History** 📊\n\n💰 **Current balance:** {balance} ⭐\n\n📭 **History is empty**\nYou don't have any transactions yet. Start playing or invite friends!",
        "transaction_item": "{emoji} **{amount_text}** - {reason_text}\n📅 {date}\n",
        # --- Social Content Texts ---
        "social_content": "📱 **READY CONTENT FOR REPOSTS** 📱\n\n🎯 **Choose platform:**",
        "tiktok_content": "🎵 CONTENT FOR TIKTOK 🎵\n\n📝 Ready texts:\n\n🔥 Found a way to earn in Telegram! Already {balance} ⭐ today. Who's with me? {ref_link}\n\n💎 This bot pays real money for games! Already withdrew {balance} ⭐. {ref_link}\n\n⚡ While everyone sleeps, I earn in Telegram! {balance} ⭐ today. Who's ready to earn? {ref_link}\n\n🎯 Hashtags:\n\\#earnings \\#telegram \\#money \\#games \\#referrals \\#passiveincome",
        "instagram_content": "📸 CONTENT FOR INSTAGRAM 📸\n\n📝 Ready texts:\n\n🌟 New way to earn in Telegram! Already {balance} ⭐ this week. Who's ready to try? {ref_link}\n\n💰 This bot really pays! Already withdrew {balance} ⭐. {ref_link}\n\n🎮 Earning by playing in Telegram! {balance} ⭐ today. Who's with me? {ref_link}\n\n🎯 Hashtags:\n\\#earnings \\#telegram \\#money \\#games \\#referrals \\#passiveincome \\#workfromhome",
        "telegram_content": "📱 CONTENT FOR TELEGRAM 📱\n\n📝 Ready texts:\n\n🚀 Guys, found a cool bot for earning! Already {balance} ⭐ today. Who's ready to try? {ref_link}\n\n💎 This bot really pays money! Already withdrew {balance} ⭐. {ref_link}\n\n⚡ While everyone sleeps, I earn! {balance} ⭐ today. Who's with me? {ref_link}\n\n🎯 Additionally:\n• Add balance screenshot\n• Show achievements\n• Tell about games",
        "challenges_stub": "⚡ **CHALLENGES** ⚡\n\n🚧 **Coming soon...**\n\nWe are working on a daily challenges system that will help you earn even more stars!\n\n💡 **What awaits you:**\n• Daily tasks\n• Completion bonuses\n• Special rewards\n• User tournaments\n\n⏰ Stay tuned for updates!",
        # Additional translations for inline buttons
        "activate_promo_button": "Activate Promo Code",
        "my_transactions_button": "My Transactions",
        "challenges_button": "Challenges",
        "social_content_button": "Content for Reposts",
        "tiktok_button": "TikTok",
        "instagram_button": "Instagram",
        "telegram_button": "Telegram",
        "duels_button": "Duels",
        "timer_button": "Timer",
        "coinflip_button": "Heads/Tails",
        "slots_button": "Slots",
        "football_button": "Football",
        "bowling_button": "Bowling",
        "basketball_button": "Basketball",
        "darts_button": "Darts",
        "dice_button": "Dice",
        "webapp_game_button": "Maniac Clic Game",
        "passive_income_button": "Passive Income",
        "daily_bonus_button": "Get Daily Bonus",
        "our_channel_button": "Our Channel",
        "our_chat_button": "Our Chat",
        "our_withdrawals_button": "Our Withdrawals",
        "our_manual_button": "Our Manual",
        "tech_support_button": "Tech Support 12:00-21:00 🆘",
        "heads_button": "Heads",
        "tails_button": "Tails",
        "risk_button": "Risk it!",
        "cashout_button": "Take Winnings",
        "play_again_button": "Play Again",
        "to_other_games_button": "To Other Games",
        "training_button": "Training",
        "stats_button": "Statistics",
        "cancel_search_button": "Cancel Search",
        "how_to_play_button": "How to Play?",
        "stop_button": "STOP!",
        "surrender_button": "Surrender",
        "boost_card_button": "Boost Card",
        "new_cards_button": "New Cards",
        "bet_low_button": "Bet on 1-3",
        "bet_high_button": "Bet on 4-6",
    },
    "uk": {
        "start_message": "👋 **Привіт, {full_name}!**\n\nЛаскаво просимо до **Maniac Stars** — місце, де можна заробляти та грати!\n\n🎯 **Що тут є:**\n• 💰 Заробіток через рефералів\n• 🎮 Міні-ігри на ставки\n• 🏆 Система досягнень\n• 🎁 Призи за активність\n\nОбери що тебе цікавить ⬇️",
        "main_menu": "**⚔️ Maniac Stars ⚔️**\n\nВикористовуй кнопки нижче для навігації.\n\n**💰 Баланс: {balance} ⭐**",
        "games_menu": "🎮 **Оберіть гру** 🎮\n\nА також клікайте зірки в нашому безкоштовному клікері! ⭐",
        "profile": "👤 **Твій профіль**\n\n"
        "**Ім'я:** {full_name}\n"
        "**ID:** `{user_id}`\n"
        "**Рівень:** {level_name}\n\n"
        "📈 **Статистика:**\n"
        "• Запрошено: {referrals_count} осіб\n"
        "• Дуелі: {duel_wins} перемог / {duel_losses} поразок\n"
        "• Стрік: {streak_days} днів поспіль\n"
        "• Баланс: {balance} ⭐\n\n"
        "{status_text}",
        "profile_status": "**Статус акаунту:**\n{quarantine_status}{cooldown_status}",
        "referral_menu": "💰 **Заробіток через рефералів** 💰\n\n"
        "Запрошуй друзів і отримуй **+{ref_bonus} ⭐** за кожного!\n\n"
        "🔗 **Твоя реферальна посилання:**\n"
        "`{ref_link}`\n\n"
        "✅ **Запрошено:** {invited_count} осіб\n"
        "📊 **Зароблено:** {earned} ⭐",
        "referral_success_notification": "{username} приєднався за вашим посиланням! Вам нараховано +{bonus} ⭐.",
        "top_menu": "🏆 **Лідери за рефералами** 🏆\n\n{top_users_text}",
        "gifts_menu": "🎁 **Призи** 🎁\n\n"
        "Обмінюй свої ⭐ на подарунки! Для отримання призів потрібно запросити мінімум {min_refs} друзів і підписатися на наші ресурси.\n\n"
        "💰 **Твій баланс:** {balance} ⭐\n"
        "👥 **Запрошено:** {referrals_count} осіб\n\n"
        "Обери подарунок:",
        "resources_menu": "🎁 **Наші ресурси** 🎁\n\n"
        "Підписка на всі наші ресурси **обов'язкова** для виводу подарунків. "
        "Підпишись, щоб не пропустити важливі анонси та підтвердження виводів!",
        "gift_confirm": "Ви впевнені, що хочете обміняти **{cost} ⭐** на **{emoji} {name}**?\n\n"
        "Цю дію не можна буде скасувати.",
        "withdrawal_success": "✅ Ваша заявка на вивід **{emoji} {name}** ({amount} ⭐) успішно створена! Адміністратор розгляне її найближчим часом.",
        "promo_prompt": "🎟️ Введіть ваш промокод:",
        "promo_success": "✅ Промокод успішно активовано! Вам нараховано: {amount} ⭐",
        "promo_fail": "❌ Не вдалося активувати промокод. Причина: {reason}",
        "entertainment_menu": "👾 **Розваги** 👾\n\nОбери, у що хочеш зіграти, або введи промокод.",
        "language_selection": "🌍 **Оберіть мову** 🌍\n\nВиберіть бажану мову для бота:",
        "language_changed": "✅ Мову змінено на {language}!",
        "settings_menu": "⚙️ **Налаштування** ⚙️\n\nОберіть дію:",
        "current_language": "🌍 **Поточна мова:** {language}",
        "back_to_menu": "⬅️ Назад в меню",
        "back_to_profile": "⬅️ Назад в профіль",
        "back_to_games": "⬅️ Назад до ігор",
        "back_to_gifts": "⬅️ Назад до подарунків",
        "cancel": "❌ Скасувати",
        "confirm": "✅ Підтвердити",
        # Кнопки меню
        "earn_button": "Заробляти",
        "games_button": "Розваги",
        "profile_button": "Профіль",
        "gifts_button": "Призи",
        "leaders_button": "Лідери",
        "resources_button": "Наші ресурси",
        "achievements_button": "Досягнення",
        "settings_button": "Налаштування",
        "change_language": "Змінити мову",
        "error_unknown": "🔧 Сталася непередбачена помилка. Ми вже працюємо над цим. Спробуйте, будь ласка, пізніше.",
        "error_db": "🗄️ Помилка при зверненні до бази даних. Будь ласка, повторіть ваш запит через кілька хвилин.",
        "error_timeout": "⏳ Сервер занадто довго відповідав. Можливо, тимчасові неполадки. Спробуйте ще раз.",
        "error_not_subscribed": "❌ **Підписка не знайдена!**\nДля виводу необхідно бути підписаним на всі наші ресурси. Перевірте підписки в розділі '🎁 Наші ресурси'.",
        "error_not_enough_referrals": "❌ **Недостатньо друзів!**\nДля виводу потрібно запросити мінімум {min_refs} друзів (у вас {current_refs}).",
        "gift_requirements_not_met": "Для виводу цього подарунка не виконані наступні умови:\n{errors}",
        "insufficient_funds": "Недостатньо коштів на балансі.",
        "daily_cap_exceeded": "Досягнуто денний ліміт на отримання зірок з цього джерела.",
        "rate_limit_minute": "Занадто часто! Спробуйте через хвилину.",
        "rate_limit_hour": "Досягнуто годинний ліміт. Спробуйте пізніше.",
        "user_in_quarantine": "Нові користувачі не можуть виводити кошти протягом 24 годин після реєстрації.",
        "withdraw_cooldown": "Вивід тимчасово недоступний після великого виграшу. Спробуйте через {hours}г {minutes}хв.",
        "rewards_disabled": "Вивід тимчасово відключений адміністрацією.",
        "daily_ops_limit": "Ви досягли ліміту на кількість заявок на день.",
        "daily_amount_limit": "Ви досягли ліміту на суму виводу на день.",
        "not_subscribed": "Для цієї дії необхідно бути підписаним на наш канал!",
        "not_enough_referrals": "Для виводу потрібно запросити мінімум {min_refs} друзів (у вас {current_refs}).",
        "unknown_error": "Сталася невідома помилка. Спробуйте пізніше.",
        "subscription_welcome": "🎉 **Ласкаво просимо до Maniac Stars!**\n\nПідписка підтверджена! Тепер ви можете користуватися всіма функціями бота.",
        "subscription_admin_welcome": "👑 **Ласкаво просимо, адміністратор!**\n\nУ вас є повний доступ до всіх функцій бота.",
        "subscription_required": "🔒 **Підписка обов'язкова**\n\nДля використання бота необхідно підписатися на наш канал.",
        "subscription_success": "✅ **Підписка підтверджена!**\n\nЛаскаво просимо в бота!",
        "subscription_failed": "❌ **Підписка не знайдена**\n\nБудь ласка, підпишіться на канал і спробуйте знову.",
        # --- Game Texts ---
        "coinflip_menu": "🪙 **Орел і Решка** 🪙\n\n"
        "Ризикни і помнож свій виграш! Вгадай, яка сторона випаде.\n"
        "З кожним наступним виграшем шанс зменшується, а приз росте!\n\n"
        "💰 **Твій баланс:** {balance} ⭐\n\nОберіть ставку:",
        "coinflip_process": "🪙 Підкидаємо монетку...",
        "coinflip_choice_prompt": "🎉 **Ставка {stake} ⭐ прийнята!** 🎉\n\n"
        "Що обираєш?",
        "coinflip_continue": "🎉 **Перемога!** 🎉\n\n"
        "Ти виграв **{current_prize}** ⭐.\n"
        "Наступний кидок може принести **{next_prize}** ⭐ з шансом {next_chance}%.\n\n"
        "Ризикнеш?",
        "coinflip_win_final": "🎉 **Вітаємо!** 🎉\n\n"
        "Ти забираєш виграш: {prize} ⭐\n"
        "💰 Твій новий баланс: {new_balance} ⭐",
        "coinflip_loss": "😕 **На жаль, невдача...**\n\n"
        "Ти програв свою ставку: {stake} ⭐\n"
        "💰 Твій новий баланс: {new_balance} ⭐",
        "slots_menu": "🎰 **Слоти** 🎰\n\nСпробуй свою удачу! Збери три однакових символи в ряд, щоб виграти.\n\n💰 **Твій баланс:** {balance} ⭐\n\nОберіть ставку:",
        "slots_win": "🎉 **ПЕРЕМОГА!** 🎉\n\nТи виграв {prize} ⭐!\n💰 Твій новий баланс: {new_balance} ⭐",
        "slots_lose": "😕 **На жаль, не пощастило...**\n\nТи програв {cost} ⭐.\n💰 Твій новий баланс: {new_balance} ⭐",
        "football_menu": "⚽️ **Футбол** ⚽️\n\nПробей пенальті! Якщо заб'єш гол, отримаєш приз.\n\n💰 **Твій баланс:** {balance} ⭐",
        "football_win": "🎉 **ГОООЛ!** 🎉\n\nТи забив і виграв {prize} ⭐!\n💰 Твій новий баланс: {new_balance} ⭐",
        "football_lose": "😕 **Промах...**\n\nТи програв {cost} ⭐.\n💰 Твій новий баланс: {new_balance} ⭐",
        "bowling_menu": "🎳 **Боулінг** 🎳\n\nЗможеш вибити страйк? Якщо збиєш всі кеглі одним кидком - отримаєш приз!\n\n💰 **Твій баланс:** {balance} ⭐\n\nОберіть ставку:",
        "bowling_win": "🎉 **СТРАЙК!** 🎉\n\nВідмінний кидок! Ти виграв {prize} ⭐!\n💰 Твій новий баланс: {new_balance} ⭐",
        "bowling_lose": "😕 **Мимо...**\n\nНаступного разу пощастить більше. Ти програв {cost} ⭐.\n💰 Твій новий баланс: {new_balance} ⭐",
        "basketball_menu": "🏀 **Баскетбол** 🏀\n\nПопади м'ячем в кошик, щоб виграти приз!\n\n💰 **Твій баланс:** {balance} ⭐",
        "basketball_win": "🎉 **Точно в ціль!** 🎉\n\nВідмінний кидок! Ти виграв {prize} ⭐!\n💰 Твій новий баланс: {new_balance} ⭐",
        "basketball_lose": "😕 **Промах...**\n\nМ'яч пролетів мимо. Ти програв {cost} ⭐.\n💰 Твій новий баланс: {new_balance} ⭐",
        "darts_menu": "🎯 **Дартс** 🎯\n\nПопади в яблучко, щоб виграти приз!\n\n💰 **Твій баланс:** {balance} ⭐",
        "darts_win": "🎉 **Точно в ціль!** 🎉\n\nВідмінний кидок! Ти виграв {prize} ⭐!\n💰 Твій новий баланс: {new_balance} ⭐",
        "darts_lose": "😕 **Мимо...**\n\nДротик пролетів мимо. Ти програв {cost} ⭐.\n💰 Твій новий баланс: {new_balance} ⭐",
        "dice_menu": "🎲 **Кістки** 🎲\n\nВгадай, в якому діапазоні випаде число на кубику! Став на (1-3) або (4-6).\n\n💰 **Твій баланс:** {balance} ⭐",
        "dice_win": "🎉 **Перемога!** 🎉\n\nТи поставив на ({choice}), а випало число {value}! Ти виграв {prize} ⭐!\n💰 Твій новий баланс: {new_balance} ⭐",
        "dice_lose": "😕 **На жаль, не вгадав...**\n\nТи поставив на ({choice}), а випало число {value}. Ти програв {cost} ⭐.\n💰 Твій новий баланс: {new_balance} ⭐",
        # --- Transaction Texts ---
        "transactions_title": "📊 **Історія транзакцій** 📊\n\n💰 **Поточний баланс:** {balance} ⭐\n\n📋 **Останні операції:**\n\n",
        "transactions_empty": "📊 **Історія транзакцій** 📊\n\n💰 **Поточний баланс:** {balance} ⭐\n\n📭 **Історія порожня**\nПоки що у вас немає транзакцій. Почніть грати або запрошуйте друзів!",
        "transaction_item": "{emoji} **{amount_text}** - {reason_text}\n📅 {date}\n",
        # --- Social Content Texts ---
        "social_content": "📱 **ГОТОВИЙ КОНТЕНТ ДЛЯ РЕПОСТІВ** 📱\n\n🎯 **Оберіть платформу:**",
        "tiktok_content": "🎵 КОНТЕНТ ДЛЯ TIKTOK 🎵\n\n📝 Готові тексти:\n\n🔥 Знайшов спосіб заробляти в Telegram! За день вже {balance} ⭐. Хто зі мною? {ref_link}\n\n💎 Цей бот платить реальні гроші за ігри! Вже вивів {balance} ⭐. {ref_link}\n\n⚡ Поки всі сплять, я заробляю в Telegram! {balance} ⭐ сьогодні. Хто готовий до заробітку? {ref_link}\n\n🎯 Хештеги:\n\\#заробіток \\#telegram \\#гроші \\#ігри \\#реферали \\#пасивнийдохід",
        "instagram_content": "📸 КОНТЕНТ ДЛЯ INSTAGRAM 📸\n\n📝 Готові тексти:\n\n🌟 Новий спосіб заробітку в Telegram! За тиждень вже {balance} ⭐. Хто готовий спробувати? {ref_link}\n\n💰 Цей бот реально платить! Вже вивів {balance} ⭐. {ref_link}\n\n🎮 Заробляю граючи в Telegram! {balance} ⭐ сьогодні. Хто зі мною? {ref_link}\n\n🎯 Хештеги:\n\\#заробіток \\#telegram \\#гроші \\#ігри \\#реферали \\#пасивнийдохід \\#workfromhome",
        "telegram_content": "📱 КОНТЕНТ ДЛЯ TELEGRAM 📱\n\n📝 Готові тексти:\n\n🚀 Хлопці, знайшов крутий бот для заробітку! За день вже {balance} ⭐. Хто готовий спробувати? {ref_link}\n\n💎 Цей бот реально платить гроші! Вже вивів {balance} ⭐. {ref_link}\n\n⚡ Поки всі сплять, я заробляю! {balance} ⭐ сьогодні. Хто зі мною? {ref_link}\n\n🎯 Додатково:\n• Додайте скріншот балансу\n• Покажіть досягнення\n• Розкажіть про ігри",
        "challenges_stub": "⚡ **ЧЕЛЛЕНДЖІ** ⚡\n\n🚧 **Незабаром...**\n\nМи працюємо над системою щоденних челленджів, які допоможуть вам заробляти ще більше зірок!\n\n💡 **Що вас чекає:**\n• Щоденні завдання\n• Бонуси за виконання\n• Спеціальні нагороди\n• Турніри між користувачами\n\n⏰ Слідкуйте за оновленнями!",
        # Додаткові переклади для інлайн кнопок
        "activate_promo_button": "Активувати промокод",
        "my_transactions_button": "Мої транзакції",
        "challenges_button": "Челленджі",
        "social_content_button": "Контент для репостів",
        "tiktok_button": "TikTok",
        "instagram_button": "Instagram",
        "telegram_button": "Telegram",
        "duels_button": "Дуелі",
        "timer_button": "Таймер",
        "coinflip_button": "Орел/Решка",
        "slots_button": "Слоти",
        "football_button": "Футбол",
        "bowling_button": "Боулінг",
        "basketball_button": "Баскетбол",
        "darts_button": "Дартс",
        "dice_button": "Кістки",
        "webapp_game_button": "Maniac Clic Game",
        "passive_income_button": "Пасивний дохід",
        "daily_bonus_button": "Отримати щоденний бонус",
        "our_channel_button": "Наш канал",
        "our_chat_button": "Наш чат",
        "our_withdrawals_button": "Наші виводи",
        "our_manual_button": "Наш мануал",
        "tech_support_button": "Техпідтримка 12:00-21:00 🆘",
        "heads_button": "Орел",
        "tails_button": "Решка",
        "risk_button": "Ризикнути!",
        "cashout_button": "Забрати виграш",
        "play_again_button": "Грати знову",
        "to_other_games_button": "До інших ігор",
        "training_button": "Навчання",
        "stats_button": "Статистика",
        "cancel_search_button": "Скасувати пошук",
        "how_to_play_button": "Як грати?",
        "stop_button": "СТОП!",
        "surrender_button": "Здатися",
        "boost_card_button": "Підсилити карту",
        "new_cards_button": "Нові карти",
        "bet_low_button": "Поставити на 1-3",
        "bet_high_button": "Поставити на 4-6",
    },
    "es": {
        "start_message": "👋 **¡Hola, {full_name}!**\n\n¡Bienvenido a **Maniac Stars** — un lugar donde puedes ganar y jugar!\n\n🎯 **Qué hay aquí:**\n• 💰 Ganancias a través de referidos\n• 🎮 Mini-juegos con apuestas\n• 🏆 Sistema de logros\n• 🎁 Premios por actividad\n\nElige lo que te interesa ⬇️",
        "main_menu": "**⚔️ Maniac Stars ⚔️**\n\nUsa los botones de abajo para navegar.\n\n**💰 Balance: {balance} ⭐**",
        "games_menu": "🎮 **Elige un juego** 🎮\n\n¡También haz clic en las estrellas en nuestro clicker gratuito! ⭐",
        "profile": "👤 **Tu perfil**\n\n"
        "**Nombre:** {full_name}\n"
        "**ID:** `{user_id}`\n"
        "**Nivel:** {level_name}\n\n"
        "📈 **Estadísticas:**\n"
        "• Invitados: {referrals_count} personas\n"
        "• Duelos: {duel_wins} victorias / {duel_losses} derrotas\n"
        "• Racha: {streak_days} días seguidos\n"
        "• Balance: {balance} ⭐\n\n"
        "{status_text}",
        "profile_status": "**Estado de la cuenta:**\n{quarantine_status}{cooldown_status}",
        "referral_menu": "💰 **Ganancias a través de referidos** 💰\n\n"
        "¡Invita amigos y obtén **+{ref_bonus} ⭐** por cada uno!\n\n"
        "🔗 **Tu enlace de referido:**\n"
        "`{ref_link}`\n\n"
        "✅ **Invitados:** {invited_count} personas\n"
        "📊 **Ganado:** {earned} ⭐",
        "referral_success_notification": "¡{username} se unió a través de tu enlace! Recibiste +{bonus} ⭐.",
        "top_menu": "🏆 **Líderes de referidos** 🏆\n\n{top_users_text}",
        "gifts_menu": "🎁 **Premios** 🎁\n\n"
        "¡Intercambia tus ⭐ por regalos! Para recibir premios necesitas invitar al menos {min_refs} amigos y suscribirte a nuestros recursos.\n\n"
        "💰 **Tu balance:** {balance} ⭐\n"
        "👥 **Invitados:** {referrals_count} personas\n\n"
        "Elige un regalo:",
        "resources_menu": "🎁 **Nuestros recursos** 🎁\n\n"
        "La suscripción a todos nuestros recursos es **obligatoria** para retirar regalos. "
        "¡Suscríbete para no perder anuncios importantes y confirmaciones de retiro!",
        "gift_confirm": "¿Estás seguro de que quieres intercambiar **{cost} ⭐** por **{emoji} {name}**?\n\n"
        "Esta acción no se puede deshacer.",
        "withdrawal_success": "✅ ¡Tu solicitud de retiro para **{emoji} {name}** ({amount} ⭐) ha sido creada exitosamente! El administrador la revisará pronto.",
        "promo_prompt": "🎟️ Ingresa tu código promocional:",
        "promo_success": "✅ ¡Código promocional activado exitosamente! Recibiste: {amount} ⭐",
        "promo_fail": "❌ No se pudo activar el código promocional. Razón: {reason}",
        "entertainment_menu": "👾 **Entretenimiento** 👾\n\nElige en qué quieres jugar, o ingresa un código promocional.",
        "coinflip_process": "🪙 Lanzando moneda...",
        "language_selection": "🌍 **Elige idioma** 🌍\n\nSelecciona tu idioma preferido para el bot:",
        "language_changed": "✅ ¡Idioma cambiado a {language}!",
        "settings_menu": "⚙️ **Configuración** ⚙️\n\nElige una acción:",
        "current_language": "🌍 **Idioma actual:** {language}",
        "back_to_menu": "⬅️ Volver al menú",
        "back_to_profile": "⬅️ Volver al perfil",
        "back_to_games": "⬅️ Volver a juegos",
        "back_to_gifts": "⬅️ Volver a regalos",
        "cancel": "❌ Cancelar",
        "confirm": "✅ Confirmar",
        # Botones del menú
        "earn_button": "Ganar",
        "games_button": "Entretenimiento",
        "profile_button": "Perfil",
        "gifts_button": "Premios",
        "leaders_button": "Líderes",
        "resources_button": "Nuestros Recursos",
        "achievements_button": "Logros",
        "settings_button": "Configuración",
        "change_language": "Cambiar Idioma",
        "error_unknown": "🔧 Ocurrió un error inesperado. Ya estamos trabajando en ello. Por favor, inténtalo más tarde.",
        "error_db": "🗄️ Error al acceder a la base de datos. Por favor, repite tu solicitud en unos minutos.",
        "error_timeout": "⏳ El servidor tardó demasiado en responder. Puede haber problemas temporales. Inténtalo de nuevo.",
        "error_not_subscribed": "❌ **¡Suscripción no encontrada!**\nPara retirar, debes estar suscrito a todos nuestros recursos. Verifica las suscripciones en la sección '🎁 Nuestros recursos'.",
        "error_not_enough_referrals": "❌ **¡No hay suficientes amigos!**\nPara retirar, necesitas invitar al menos {min_refs} amigos (tienes {current_refs}).",
        "gift_requirements_not_met": "No se cumplen las siguientes condiciones para retirar este regalo:\n{errors}",
        "insufficient_funds": "Fondos insuficientes en el balance.",
        "daily_cap_exceeded": "Se alcanzó el límite diario para ganar estrellas de esta fuente.",
        "rate_limit_minute": "¡Muy frecuente! Inténtalo en un minuto.",
        "rate_limit_hour": "Límite horario alcanzado. Inténtalo más tarde.",
        "user_in_quarantine": "Los nuevos usuarios no pueden retirar fondos dentro de las 24 horas posteriores al registro.",
        "withdraw_cooldown": "Retiro temporalmente no disponible después de una gran ganancia. Inténtalo en {hours}h {minutes}m.",
        "rewards_disabled": "Retiro temporalmente deshabilitado por la administración.",
        "daily_ops_limit": "Has alcanzado el límite diario de solicitudes.",
        "daily_amount_limit": "Has alcanzado el límite diario de cantidad de retiro.",
        "not_subscribed": "¡Debes estar suscrito a nuestro canal para esta acción!",
        "not_enough_referrals": "Para retirar, necesitas invitar al menos {min_refs} amigos (tienes {current_refs}).",
        "unknown_error": "Ocurrió un error desconocido. Por favor, inténtalo más tarde.",
        "subscription_welcome": "🎉 **¡Bienvenido a Maniac Stars!**\n\n¡Suscripción confirmada! Ahora puedes usar todas las funciones del bot.",
        "subscription_admin_welcome": "👑 **¡Bienvenido, administrador!**\n\nTienes acceso completo a todas las funciones del bot.",
        "subscription_required": "🔒 **Suscripción requerida**\n\nDebes suscribirte a nuestro canal para usar el bot.",
        "subscription_success": "✅ **¡Suscripción confirmada!**\n\n¡Bienvenido al bot!",
        "subscription_failed": "❌ **Suscripción no encontrada**\n\nPor favor, suscríbete al canal e inténtalo de nuevo.",
        # --- Social Content Texts ---
        "social_content": "📱 **CONTENIDO LISTO PARA REPOSTS** 📱\n\n🎯 **Elige plataforma:**",
        "tiktok_content": "🎵 CONTENIDO PARA TIKTOK 🎵\n\n📝 Textos listos:\n\n🔥 ¡Encontré una forma de ganar en Telegram! Ya {balance} ⭐ hoy. ¿Quién está conmigo? {ref_link}\n\n💎 ¡Este bot paga dinero real por juegos! Ya retiré {balance} ⭐. {ref_link}\n\n⚡ ¡Mientras todos duermen, yo gano en Telegram! {balance} ⭐ hoy. ¿Quién está listo para ganar? {ref_link}\n\n🎯 Hashtags:\n\\#ganancias \\#telegram \\#dinero \\#juegos \\#referidos \\#ingresopasivo",
        "instagram_content": "📸 CONTENIDO PARA INSTAGRAM 📸\n\n📝 Textos listos:\n\n🌟 ¡Nueva forma de ganar en Telegram! Ya {balance} ⭐ esta semana. ¿Quién está listo para probar? {ref_link}\n\n💰 ¡Este bot realmente paga! Ya retiré {balance} ⭐. {ref_link}\n\n🎮 ¡Ganando jugando en Telegram! {balance} ⭐ hoy. ¿Quién está conmigo? {ref_link}\n\n🎯 Hashtags:\n\\#ganancias \\#telegram \\#dinero \\#juegos \\#referidos \\#ingresopasivo \\#workfromhome",
        "telegram_content": "📱 CONTENIDO PARA TELEGRAM 📱\n\n📝 Textos listos:\n\n🚀 ¡Chicos, encontré un bot genial para ganar! Ya {balance} ⭐ hoy. ¿Quién está listo para probar? {ref_link}\n\n💎 ¡Este bot realmente paga dinero! Ya retiré {balance} ⭐. {ref_link}\n\n⚡ ¡Mientras todos duermen, yo gano! {balance} ⭐ hoy. ¿Quién está conmigo? {ref_link}\n\n🎯 Adicionalmente:\n• Agrega captura de pantalla del balance\n• Muestra logros\n• Cuenta sobre juegos",
        "challenges_stub": "⚡ **DESAFÍOS** ⚡\n\n🚧 **Próximamente...**\n\n¡Estamos trabajando en un sistema de desafíos diarios que te ayudará a ganar aún más estrellas!\n\n💡 **Lo que te espera:**\n• Tareas diarias\n• Bonificaciones por completar\n• Recompensas especiales\n• Torneos entre usuarios\n\n⏰ ¡Mantente atento a las actualizaciones!",
        # Traducciones adicionales para botones inline
        "activate_promo_button": "Activar Código Promocional",
        "my_transactions_button": "Mis Transacciones",
        "challenges_button": "Desafíos",
        "social_content_button": "Contenido para Reposts",
        "tiktok_button": "TikTok",
        "instagram_button": "Instagram",
        "telegram_button": "Telegram",
        "duels_button": "Duelos",
        "timer_button": "Temporizador",
        "coinflip_button": "Cara/Cruz",
        "slots_button": "Tragamonedas",
        "football_button": "Fútbol",
        "bowling_button": "Bolos",
        "basketball_button": "Baloncesto",
        "darts_button": "Dardos",
        "dice_button": "Dados",
        "webapp_game_button": "Maniac Clic Game",
        "passive_income_button": "Ingreso Pasivo",
        "daily_bonus_button": "Obtener Bono Diario",
        "our_channel_button": "Nuestro Canal",
        "our_chat_button": "Nuestro Chat",
        "our_withdrawals_button": "Nuestros Retiros",
        "our_manual_button": "Nuestro Manual",
        "tech_support_button": "Soporte Técnico 12:00-21:00 🆘",
        "heads_button": "Cara",
        "tails_button": "Cruz",
        "risk_button": "¡Arriesgarse!",
        "cashout_button": "Tomar Ganancias",
        "play_again_button": "Jugar de Nuevo",
        "to_other_games_button": "A Otros Juegos",
        "training_button": "Entrenamiento",
        "stats_button": "Estadísticas",
        "cancel_search_button": "Cancelar Búsqueda",
        "how_to_play_button": "¿Cómo Jugar?",
        "stop_button": "¡PARAR!",
        "surrender_button": "Rendirse",
        "boost_card_button": "Mejorar Carta",
        "new_cards_button": "Nuevas Cartas",
        "bet_low_button": "Apostar en 1-3",
        "bet_high_button": "Apostar en 4-6",
    },
}


def get_text(
    key: str, language_code: str = "ru", default: Optional[str] = None, **kwargs
) -> str:
    """
    Получает текст на указанном языке.

    Args:
        key: Ключ текста
        language_code: Код языка (ru, en, uk, es)
        default: Значение по умолчанию, если текст не найден
        **kwargs: Параметры для форматирования строки

    Returns:
        Отформатированный текст на выбранном языке
    """
    if language_code not in SUPPORTED_LANGUAGES:
        language_code = "ru"  # Fallback to Russian

    text = MULTILINGUAL_TEXTS.get(language_code, {}).get(key, "")

    if not text:
        # Fallback to Russian if text not found
        text = MULTILINGUAL_TEXTS.get("ru", {}).get(key, "")

        # If still not found, use default or key name
        if not text:
            text = default if default is not None else f"[{key}]"

    try:
        return text.format(**kwargs)
    except KeyError:
        # If formatting fails, return the text as is
        return text


def get_language_name(language_code: str) -> str:
    """Получает название языка по коду."""
    return SUPPORTED_LANGUAGES.get(language_code, "🇷🇺 Русский")


def get_available_languages() -> Dict[str, str]:
    """Возвращает словарь доступных языков."""
    return SUPPORTED_LANGUAGES.copy()
