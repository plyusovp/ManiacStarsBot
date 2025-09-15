// --- Локальное API для работы с балансом через localStorage ---

const BALANCE_KEY = 'ms.balance';
const BONUS_KEY = 'ms.bonusAt';
const STARTING_BALANCE = 1000;

// Инициализация Telegram WebApp
const tg = window.Telegram.WebApp;

/**
 * Инициализирует баланс, если он не установлен
 */
function initBalance() {
    if (localStorage.getItem(BALANCE_KEY) === null) {
        localStorage.setItem(BALANCE_KEY, STARTING_BALANCE);
    }
}

/**
 * Возвращает данные пользователя (мок)
 * @returns {{id: number, name: string, photo_url: string|null}}
 */
export function getUser() {
    // В реальном приложении данные берутся из tg.initDataUnsafe
    if (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) {
        const user = tg.initDataUnsafe.user;
        return {
            id: user.id,
            name: user.first_name || user.username || 'User',
            photo_url: user.photo_url || null
        };
    }
    // Заглушка для отладки в браузере
    return {
        id: 123456,
        name: 'Test User',
        photo_url: null
    };
}

/**
 * Получает текущий баланс
 * @returns {number}
 */
export function getBalance() {
    initBalance();
    return parseInt(localStorage.getItem(BALANCE_KEY) || '0', 10);
}

/**
 * Устанавливает новое значение баланса
 * @param {number} amount
 */
export function setBalance(amount) {
    const newBalance = Math.max(0, amount); // Баланс не может быть отрицательным
    localStorage.setItem(BALANCE_KEY, newBalance);
}

/**
 * Добавляет указанную сумму к балансу
 * @param {number} amount
 */
export function addBalance(amount) {
    const currentBalance = getBalance();
    setBalance(currentBalance + amount);
}

/**
 * Вычитает указанную сумму из баланса. Возвращает true, если операция успешна.
 * @param {number} amount
 * @returns {boolean} - true, если средств хватило, иначе false
 */
export function subBalance(amount) {
    const currentBalance = getBalance();
    if (currentBalance >= amount) {
        setBalance(currentBalance - amount);
        return true;
    }
    return false;
}

/**
 * Имитирует пополнение баланса
 */
export function payInStarsMock() {
    addBalance(500);
    // В реальном приложении здесь будет вызов tg.openInvoice()
    console.log("Mock payment: +500 stars added.");
}


/**
 * Проверяет и выдает ежедневный бонус
 * @returns {{success: boolean, message: string, amount?: number}}
 */
export function claimDailyBonus() {
    const lastBonusTime = parseInt(localStorage.getItem(BONUS_KEY) || '0', 10);
    const now = new Date().getTime();
    const cooldown = 24 * 60 * 60 * 1000; // 24 часа в миллисекундах

    if (now - lastBonusTime > cooldown) {
        const bonusAmount = 100;
        addBalance(bonusAmount);
        localStorage.setItem(BONUS_KEY, now);
        return { success: true, message: `Вы получили ${bonusAmount} звёзд!`, amount: bonusAmount };
    } else {
        const timeLeft = cooldown - (now - lastBonusTime);
        const hours = Math.floor(timeLeft / (1000 * 60 * 60));
        const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
        return { success: false, message: `Бонус будет доступен через ${hours}ч ${minutes}м` };
    }
}

// Инициализируем баланс при загрузке модуля
initBalance();
