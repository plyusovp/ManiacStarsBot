// Этот модуль отвечает за сбор и отправку аналитических событий.
// Пока что он просто выводит события в консоль, чтобы мы видели, что всё работает.

let eventsBatch = []; // Массив для накопления событий перед "отправкой"
const BATCH_SIZE = 5; // Отправлять события пачками по 5 штук

/**
 * Основная функция для отслеживания событий.
 * @param {string} eventType - Название события (например, 'game_start').
 * @param {object} payload - Дополнительные данные о событии (например, { game: 'coin', bet: 100 }).
 */
export function trackEvent(eventType, payload = {}) {
    const event = {
        type: eventType,
        timestamp: new Date().toISOString(),
        payload: payload,
    };

    eventsBatch.push(event);
    console.log('[Analytics Event]', event); // Сразу выводим в консоль для отладки

    // Если накопилось достаточно событий, "отправляем" их
    if (eventsBatch.length >= BATCH_SIZE) {
        sendBatch();
    }
}

/**
 * "Отправляет" накопленные события.
 * В будущем здесь будет реальный запрос на бэкенд.
 */
function sendBatch() {
    if (eventsBatch.length === 0) return;

    console.log(`--- [Analytics] Отправляем пачку из ${eventsBatch.length} событий: ---`);
    console.table(eventsBatch); // Выводим в виде красивой таблицы

    // Очищаем массив после "отправки"
    eventsBatch = [];
}

// Пример использования (этот код можно будет вызывать из других файлов):
// trackEvent('app_open');
// trackEvent('game_start', { game: 'coin', bet: 100 });
// trackEvent('game_result', { game: 'coin', bet: 100, win: 196 });