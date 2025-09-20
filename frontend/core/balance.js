// Этот модуль будет отвечать за все операции с балансом.
// Пока он работает с фейковыми данными, но в будущем будет общаться с бэкендом.

import { bus } from './bus.js';

let currentBalance = 5000; // Стартовый баланс для теста

export const balance = {
    /**
     * Получить текущий баланс.
     */
    get() {
        return currentBalance;
    },

    /**
     * Проверить, можно ли сделать такую ставку.
     * @param {number} amount - Сумма ставки.
     * @returns {boolean}
     */
    canBet(amount) {
        return currentBalance >= amount;
    },

    /**
     * Списать ставку с баланса.
     * @param {number} amount - Сумма ставки.
     */
    async commitBet(amount) {
        if (!this.canBet(amount)) {
            console.error("Попытка сделать ставку больше баланса!");
            return;
        }
        currentBalance -= amount;
        console.log(`Ставка ${amount}. Новый баланс: ${currentBalance}`);
        // Отправляем событие, чтобы UI (например, шапка сайта) обновился
        bus.publish('balance-changed');
    },

    /**
     * Начислить выигрыш на баланс.
     * @param {number} amount - Сумма выигрыша.
     */
    async applyPayout(amount) {
        currentBalance += amount;
        console.log(`Выигрыш ${amount}. Новый баланс: ${currentBalance}`);
        bus.publish('balance-changed');
    },
    
    /**
     * Установить новое значение баланса (например, при загрузке данных с сервера).
     * @param {number} newBalance 
     */
    set(newBalance) {
        currentBalance = newBalance;
        bus.publish('balance-changed');
    }
};

// Подписываемся на событие изменения баланса и выводим в консоль для отладки
bus.subscribe('balance-changed', () => {
    console.log(`Баланс обновлён. Новое значение: ${balance.get()}`);
});