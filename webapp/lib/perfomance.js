/**
 * Определяет, является ли устройство низкопроизводительным.
 * Это помогает адаптировать UI, отключая "тяжелые" эффекты.
 * @returns {boolean} - true, если устройство считается "слабым".
 */
export function isLowPerfDevice() {
    // 1. Проверяем настройку системы "предпочитает меньше движений" (важно для доступности).
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (mediaQuery.matches) {
        return true;
    }

    // 2. Проверяем количество ядер процессора (если API доступно).
    // Устройства с 4 или менее логическими ядрами считаем кандидатами на низкую производительность.
    // Это простой эвристический метод.
    if (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4) {
        return true;
    }

    // В будущем можно добавить и другие проверки (например, объем RAM, если API станет доступно).
    return false;
}
