// Этот модуль - "главный мотор" для всех анимаций (игр, частиц).
// Он создаёт один цикл requestAnimationFrame, чтобы всё было синхронно и плавно.

const subscribers = new Set(); // Список подписчиков, которые хотят получать "тики" анимации
let lastTime = 0;
let isRunning = false;
let isLowPerf = false; // Флаг для слабых устройств

/**
 * Простая проверка на "слабое" устройство.
 * Можно будет улучшить в будущем.
 */
function detectLowPerformance() {
    // Если у пользователя меньше 4 ядер процессора, считаем устройство слабым
    if (navigator.hardwareConcurrency && navigator.hardwareConcurrency < 4) {
        isLowPerf = true;
    }
    // Если пользователь сам включил в браузере/системе режим экономии
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        isLowPerf = true;
    }
    if (isLowPerf) {
        console.warn('[Performance] Обнаружено слабое устройство. Эффекты будут упрощены.');
        document.body.classList.add('low-performance');
    }
}

/**
 * Главный цикл анимации.
 * @param {number} currentTime - Время, переданное браузером.
 */
function gameLoop(currentTime) {
    if (!isRunning) return;

    const deltaTime = (currentTime - lastTime) / 1000; // Время в секундах с прошлого кадра
    lastTime = currentTime;

    // Оповещаем всех подписчиков о новом кадре
    for (const callback of subscribers) {
        callback(deltaTime);
    }

    requestAnimationFrame(gameLoop);
}

/**
 * Добавляет функцию в цикл анимации.
 * @param {function} callback - Функция, которая будет вызываться каждый кадр.
 */
function subscribe(callback) {
    subscribers.add(callback);
}

/**
 * Удаляет функцию из цикла анимации.
 * @param {function} callback - Функция для удаления.
 */
function unsubscribe(callback) {
    subscribers.delete(callback);
}

/**
 * Запускает главный цикл анимации.
 */
function start() {
    if (isRunning) return;
    console.log('[Performance] Главный цикл запущен.');
    isRunning = true;
    lastTime = performance.now();
    requestAnimationFrame(gameLoop);
}

/**
 * Останавливает главный цикл анимации.
 */
function stop() {
    isRunning = false;
}

export const performance = {
    init: detectLowPerformance,
    isLow: () => isLowPerf,
    start,
    stop,
    subscribe,
    unsubscribe,
};