// plyusovp/maniacstarsbot/ManiacStarsBot-4df23ef8bd5b8766acddffe6bca30a128458c7a5/frontend/core/houseedge.js

// --- 1. Преимущество казино (Edge) для каждой игры ---
// Здесь мы храним "процент жадности" для каждой игры.
// 0.02 = 2%, 0.04 = 4% и так далее.
const EDGES = {
    coin: 0.02,
    dice: 0.02,
    crash: 0.04,
    slots: 0.05,
    taper: 0.03,
};

// --- 2. Жёсткие лимиты максимальной ставки для каждой игры ---
const HARD_MAX_BETS = {
    coin: 10000,
    dice: 15000,
    crash: 25000,
    slots: 20000,
    taper: 15000,
};

/**
 * Получает преимущество казино для указанной игры.
 * @param {string} gameName - Название игры (например, 'coin').
 * @returns {number} - Возвращает преимущество (например, 0.02).
 */
export function getEdge(gameName) {
    return EDGES[gameName] || 0.03; // Если игра не найдена, вернём 3% по умолчанию
}

/**
 * Рассчитывает максимально допустимую ставку для игрока.
 * @param {string} gameName - Название игры.
 * @param {number} currentBalance - Текущий баланс игрока.
 * @returns {number} - Максимальная ставка.
 */
export function getMaxBet(gameName, currentBalance) {
    const hardMax = HARD_MAX_BETS[gameName] || 10000; // Жёсткий лимит
    const balanceMax = Math.floor(currentBalance * 0.1); // 10% от баланса
    
    // Возвращаем то, что меньше: жёсткий лимит или 10% от баланса
    return Math.min(hardMax, balanceMax);
}

/**
 * Проверяет, является ли ставка допустимой.
 * @param {string} gameName - Название игры.
 * @param {number} betAmount - Сумма ставки.
 * @param {number} currentBalance - Текущий баланс игрока.
 * @returns {boolean} - true, если ставка в пределах лимитов.
 */
export function isBetValid(gameName, betAmount, currentBalance) {
    const minBet = 1;
    const maxBet = getMaxBet(gameName, currentBalance);
    
    return betAmount >= minBet && betAmount <= maxBet;
}
