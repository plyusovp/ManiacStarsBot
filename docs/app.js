// --- Экраны ---
import * as taper from './ui/components/screens/taper.js';
import * as games from './ui/components/screens/games.js';
import * as referrals from './ui/components/screens/referrals.js';
import * as profile from './ui/components/screens/profile.js';
import * as settings from './ui/components/screens/settings.js';

// --- Ядро ---
import { getBalance, fmt, isFirstLaunch, setVisited } from './core/state.js';
import * as audio from './core/audio.js';
import { hapticFeedback } from './core/utils.js';
import * as particles from './core/particles.js';
import { isLowPerfDevice } from './core/performance.js';
import * as i18n from './core/i18n.js';
import * as effects from './core/effects.js';

// --- КОНФИГУРАЦИЯ ---
const routes = {
    '/taper': taper,
    '/games': games,
    '/referrals': referrals,
    '/profile': profile,
    '/settings': settings,
};

let currentView = null;
let tg;

// --- DOM-элементы ---
const DOMElements = {
    app: document.getElementById('app'),
    splash: document.getElementById('splash-screen'),
    headerTitle: document.getElementById('header-title'),
    balanceValue: document.getElementById('balance-value'),
    mainContent: document.getElementById('main-content'),
    navContainer: document.getElementById('bottom-nav'),
    particleCanvas: document.getElementById('particle-canvas'),
};

const updateBalanceDisplay = () => {
    DOMElements.balanceValue.textContent = fmt(getBalance());
};

// --- Навигация ---
async function navigateTo(path) {
    // Если это путь к игре, загружаем модуль динамически
    if (path.startsWith('/game/')) {
        const gameId = path.split('/')[2];
        try {
            // Динамический импорт позволяет подгружать код игры только когда он нужен
            const gameModule = await import(`./games/${gameId}.js`);
            mountView(gameModule, path);
        } catch (e) {
            console.error(`Failed to load game module: ${gameId}`, e);
            navigateTo('/games'); // Если игра не найдена, возвращаемся к списку игр
        }
    } else {
        // Для обычных экранов используем статический импорт
        mountView(routes[path] || routes['/taper'], path);
    }
}

function mountView(viewModule, path) {
    if (currentView && currentView.unmount) {
        currentView.unmount();
    }

    currentView = viewModule;
    currentView.path = path; // Сохраняем текущий путь

    const title = viewModule.titleKey ? i18n.t(viewModule.titleKey) : (viewModule.title || '');
    DOMElements.headerTitle.textContent = title;
    DOMElements.mainContent.innerHTML = '';
    DOMElements.mainContent.className = 'main-content view';
    currentView.mount(DOMElements.mainContent);

    // Обновляем активную иконку в навигации
    document.querySelectorAll('.nav-item').forEach(item => {
        const itemPath = item.dataset.path;
        item.classList.toggle('active', itemPath === path || (path.startsWith('/game') && itemPath === '/games'));
    });
}

async function changeLanguage(lang) {
    i18n.setLanguage(lang);
    generateNavigation(); // Перерисовываем навигацию с новым языком
    if (currentView) {
        // Перезагружаем текущий экран, чтобы обновить тексты
        navigateTo(currentView.path);
    }
}

// --- ГЕНЕРАЦИЯ НАВИГАЦИИ ---
function generateNavigation() {
    const navItems = [
        { path: '/taper', icon: 'star', labelKey: 'nav_main' },
        { path: '/games', icon: 'gamepad-2', labelKey: 'nav_games' },
        { path: '/referrals', icon: 'users', labelKey: 'nav_friends' },
        { path: '/profile', icon: 'user', labelKey: 'nav_profile' },
        { path: '/settings', icon: 'sliders-horizontal', labelKey: 'nav_settings' },
    ];
    // Просто для примера, иконки можно заменить на SVG, как было раньше
    const icons = { 'star': '⭐', 'gamepad-2': '🎮', 'users': '👥', 'user': '👤', 'sliders-horizontal': '⚙️' };

    DOMElements.navContainer.innerHTML = navItems.map(item => `
        <a href="#" data-path="${item.path}" class="nav-item">
            <div style="font-size: 24px;">${icons[item.icon]}</div>
            <span>${i18n.t(item.labelKey)}</span>
        </a>
    `).join('');
    bindNavEventListeners();
}

function bindNavEventListeners() {
    DOMElements.navContainer.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            navigateTo(item.dataset.path);
            hapticFeedback('light');
        });
    });
}

// --- ИНИЦИАЛИЗАЦИЯ ПРИЛОЖЕНИЯ ---
const initApp = async () => {
     try {
        await i18n.init();

        try {
            tg = window.Telegram.WebApp;
            tg.ready();
            tg.expand();
        } catch (e) {
            console.warn("Telegram WebApp API not found. Running in dev mode.");
        }

        // Создаем глобальный объект для доступа из других модулей
        window.ManiacGames = {
            updateBalance: updateBalanceDisplay,
            navigateTo,
            hapticFeedback,
            t: i18n.t,
            changeLanguage,
            // ... другие глобальные функции, если нужны
        };

        // Скрываем сплэш-скрин и показываем приложение
        DOMElements.splash.style.opacity = '0';
        DOMElements.app.classList.remove('hidden');
        DOMElements.splash.addEventListener('transitionend', () => DOMElements.splash.remove());

        generateNavigation();
        updateBalanceDisplay();
        navigateTo('/taper'); // Стартовый экран

     } catch (e) {
        console.error("Critical error during app initialization:", e);
        document.body.innerHTML = `<div style="color:white; padding:20px;"><h3>Критическая ошибка</h3><p>${e.message}</p><pre>${e.stack}</pre></div>`;
    }
 };

document.addEventListener('DOMContentLoaded', initApp);
