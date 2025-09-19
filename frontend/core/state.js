// Этот файл управляет глобальным состоянием приложения.

// Инициализируем объект состояния.
// Это пример, реальные данные будут загружаться из Firestore.
const state = {
    user: {
        userId: null,
        balance: 1000.00
    },
    // Добавь здесь другие переменные состояния
};

// Функция для установки ID пользователя
export function setUserId(userId) {
    state.user.userId = userId;
}

// Функция для получения ID пользователя
export function getUserId() {
    return state.user.userId;
}

// Функция для установки баланса
export function setBalance(balance) {
    state.user.balance = balance;
}

// Функция для получения баланса
export function getBalance() {
    return state.user.balance;
}

// Экспортируем весь объект состояния, чтобы его можно было использовать в других файлах.
export { state };
