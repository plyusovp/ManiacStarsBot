const BALANCE_KEY = 'mg.balance';
const STATS_KEY = 'mg.stats';
const VISITED_KEY = 'mg.visited'; // <-- НОВОЕ: Ключ для отслеживания первого запуска
const STARTING_BALANCE = 1000;

/**
 * Initializes storage keys if they don't exist.
 */
function initStorage() {
    if (localStorage.getItem(BALANCE_KEY) === null) {
        localStorage.setItem(BALANCE_KEY, STARTING_BALANCE.toString());
    }
    if (localStorage.getItem(STATS_KEY) === null) {
        localStorage.setItem(STATS_KEY, JSON.stringify({
            wins: 0,
            losses: 0,
            maxCrashMultiplier: 0,
            topWin: 0,
        }));
    }
    // <-- НОВОЕ: Инициализация флага первого визита -->
    if (localStorage.getItem(VISITED_KEY) === null) {
        localStorage.setItem(VISITED_KEY, 'false');
    }
}

/**
 * Formats a number with spaces as thousands separators.
 * e.g., 1234567 -> "1 234 567"
 * @param {number} n The number to format.
 * @returns {string} The formatted number string.
 */
export function fmt(n) {
    if (n === null || n === undefined) return '0';
    return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

/**
 * Gets the current balance.
 * @returns {number}
 */
export function getBalance() {
    initStorage();
    return parseInt(localStorage.getItem(BALANCE_KEY), 10);
}

/**
 * Sets the balance to a specific amount.
 * @param {number} n The new balance amount.
 */
export function setBalance(n) {
    initStorage();
    localStorage.setItem(BALANCE_KEY, Math.floor(n).toString());
}

/**
 * Adds an amount to the balance.
 * @param {number} n The amount to add.
 */
export function addBalance(n) {
    const current = getBalance();
    setBalance(current + n);
}

/**
 * Subtracts an amount from the balance.
 * @param {number} n The amount to subtract.
 */
export function subBalance(n) {
    const current = getBalance();
    setBalance(current - n);
}

/**
 * Retrieves game statistics.
 * @returns {object} The statistics object.
 */
export function getStats() {
    initStorage();
    return JSON.parse(localStorage.getItem(STATS_KEY));
}

/**
 * Updates game statistics.
 * @param {object} newStats - An object with stats to update (e.g., { wins: 1, topWin: 500 }).
 */
export function updateStats(newStats) {
    const currentStats = getStats();
    const updated = { ...currentStats, ...newStats };

    // Ensure specific values only increase
    if (newStats.maxCrashMultiplier && newStats.maxCrashMultiplier > currentStats.maxCrashMultiplier) {
        updated.maxCrashMultiplier = newStats.maxCrashMultiplier;
    }
    if (newStats.topWin && newStats.topWin > currentStats.topWin) {
        updated.topWin = newStats.topWin;
    }
    if (newStats.wins) {
        updated.wins = currentStats.wins + newStats.wins;
    }
     if (newStats.losses) {
        updated.losses = currentStats.losses + newStats.losses;
    }

    localStorage.setItem(STATS_KEY, JSON.stringify(updated));
}

// <-- НОВЫЕ ФУНКЦИИ -->
/**
 * Checks if this is the user's first launch.
 * @returns {boolean}
 */
export function isFirstLaunch() {
    initStorage();
    return localStorage.getItem(VISITED_KEY) === 'false';
}

/**
 * Sets the visited flag to true after the first launch.
 */
export function setVisited() {
    localStorage.setItem(VISITED_KEY, 'true');
}


/**
 * Resets all local data (balance and stats).
 */
export function resetLocalData() {
    localStorage.removeItem(BALANCE_KEY);
    localStorage.removeItem(STATS_KEY);
    localStorage.removeItem(VISITED_KEY); // Сбрасываем и флаг визита
    initStorage(); // Re-initialize with default values
}

// Initialize on load
initStorage();
