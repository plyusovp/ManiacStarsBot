/**
 * Triggers haptic feedback if available in the Telegram WebApp.
 * @param {string} type - 'light', 'medium', 'heavy', 'success', 'warning', 'error'
 */
export function hapticFeedback(type) {
    try {
        const tg = window.Telegram?.WebApp;
        if (tg && tg.HapticFeedback) {
            switch (type) {
                case 'light':
                    tg.HapticFeedback.impactOccurred('light');
                    break;
                case 'medium':
                    tg.HapticFeedback.impactOccurred('medium');
                    break;
                case 'heavy':
                    tg.HapticFeedback.impactOccurred('heavy');
                    break;
                case 'success':
                    tg.HapticFeedback.notificationOccurred('success');
                    break;
                case 'warning':
                    tg.HapticFeedback.notificationOccurred('warning');
                    break;
                case 'error':
                    tg.HapticFeedback.notificationOccurred('error');
                    break;
                default:
                    break;
            }
        }
    } catch (e) {
        console.warn('Haptic feedback failed:', e);
    }
}
