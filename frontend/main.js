import { renderNav } from './ui/components/nav.js';
import { navigate, getRoute } from './core/router.js';
import { playTap, initAudio } from './core/audio.js';
import { initI18n } from './core/i18n.js';

/**
 * Главная функция инициализации приложения.
 * Она будет вызвана только после полной загрузки DOM.
 */
function initializeApp() {
    // Сначала инициализируем систему перевода (i18n)
    initI18n().then(() => {
        // После успешной загрузки переводов, отрисовываем навигацию
        renderNav();

        // Выполняем первоначальную навигацию на основе URL или на главную страницу
        navigate(getRoute() || '/games');
    });

    // Добавляем глобальный обработчик кликов для звука нажатия и инициализации аудио
    document.body.addEventListener('click', (e) => {
        // При первом клике пользователя инициализируем AudioContext.
        // Функция сама проверит, нужно ли ей выполняться.
        initAudio();

        // Воспроизводим звук только если клик был по кнопке или ссылке
        if (e.target.closest('button, a')) {
            playTap();
        }
    });

    // Добавляем обработчик для кнопок навигации
    const navContainer = document.getElementById('bottom-nav');
    if (navContainer) {
        navContainer.addEventListener('click', (event) => {
            const navButton = event.target.closest('.nav-btn');
            if (navButton && navButton.dataset.route) {
                navigate(navButton.dataset.route);
            }
        });
    } else {
        console.error('Navigation container #bottom-nav not found during initialization!');
    }
}

// Ждем, пока весь HTML-документ не будет готов, и только после этого запускаем наше приложение.
document.addEventListener('DOMContentLoaded', initializeApp);
