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
        const navContainer = document.getElementById('bottom-nav');
        const currentRoute = getRoute() || 'games';

        // После успешной загрузки переводов, отрисовываем навигацию
        renderNav(navContainer, currentRoute);

        // Выполняем первоначальную навигацию на основе URL или на главную страницу
        navigate(currentRoute);
    });

    /**
     * Обработчик для самого первого клика пользователя.
     * Инициализирует аудио и заменяет себя на более простой обработчик.
     */
    const handleFirstClick = (e) => {
        // 1. Инициализируем аудио
        initAudio();

        // 2. Воспроизводим звук, если это был клик по кнопке или ссылке
        if (e.target.closest('button, a')) {
            playTap();
        }

        // 3. Удаляем этот обработчик, чтобы он больше никогда не выполнялся
        document.body.removeEventListener('click', handleFirstClick);

        // 4. Вешаем новый, более простой обработчик, который отвечает только за звуки
        document.body.addEventListener('click', (event) => {
            if (event.target.closest('button, a')) {
                playTap();
            }
        });
    };

    // Добавляем глобальный обработчик для ПЕРВОГО клика
    document.body.addEventListener('click', handleFirstClick);

    // Добавляем обработчик для кнопок навигации
    const navContainer = document.getElementById('bottom-nav');
    if (navContainer) {
        navContainer.addEventListener('click', (event) => {
            const navLink = event.target.closest('.nav-link');
            // Проверяем, что кликнули именно по ссылке навигации
            if (navLink && navLink.hash) {
                event.preventDefault(); // Предотвращаем стандартное поведение ссылки
                const route = navLink.hash.substring(1); // Получаем маршрут из href (убираем #)
                navigate(route);
                renderNav(navContainer, route); // Перерисовываем навигацию для подсветки активной кнопки
            }
        });
    } else {
        console.error('Navigation container #bottom-nav not found during initialization!');
    }
}

// Ждем, пока весь HTML-документ не будет готов, и только после этого запускаем наше приложение.
document.addEventListener('DOMContentLoaded', initializeApp);
