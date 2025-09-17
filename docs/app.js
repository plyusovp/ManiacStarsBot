// --- ИЗМЕНЕНА СТРУКТУРА ИМПОРТОВ ---
// Экраны
import * as taper from './ui/components/screens/taper.js';
import * as games from './ui/components/screens/games.js';
import * as referrals from './ui/components/screens/referrals.js';
import * as profile from './ui/components/screens/profile.js';
import * as settings from './ui/components/screens/settings.js';
import * as uikit from './ui/components/screens/uikit.js';

// Игры (статический импорт для решения проблемы с локальным запуском)
import * as coinGame from './games/coin.js';
import * as crashGame from './games/crash.js';
import * as diceGame from './games/dice.js';
import * as slotsGame from './games/slots.js';


// Ядро
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
    '/uikit': uikit,
};

// Карта игровых модулей для роутера
const gameModules = {
    'coin': coinGame,
    'crash': crashGame,
    'dice': diceGame,
    'slots': slotsGame
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

// --- Менеджер тем ---
const themeManager = {
    THEME_KEY: 'mg.theme',
    currentTheme: 'dark',

    init() {
        this.currentTheme = localStorage.getItem(this.THEME_KEY) || 'dark';
        this.applyTheme(this.currentTheme);

        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            if (this.currentTheme === 'system') {
                this._applyActualTheme(this.getSystemTheme());
            }
        });
    },

    applyTheme(theme) {
        this.currentTheme = theme;
        localStorage.setItem(this.THEME_KEY, theme);
        let themeToApply = theme === 'system' ? this.getSystemTheme() : theme;
        this._applyActualTheme(themeToApply);
    },

    _applyActualTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        if(window.ManiacGames && window.ManiacGames.tg) {
             window.ManiacGames.tg.setHeaderColor(theme === 'dark' ? '#111823' : '#FFFFFF');
             window.ManiacGames.tg.setBackgroundColor(theme === 'dark' ? '#0B0E12' : '#F0F2F5');
        }
    },

    getSystemTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    },

    getCurrentTheme() { return this.currentTheme; }
};


// --- UI-ХЕЛПЕРЫ ---
const updateBalanceDisplay = () => {
    DOMElements.balanceValue.textContent = fmt(getBalance());
};

const showToast = (message, type = 'info') => {
    if (window.ManiacGames && window.ManiacGames.showNotification) {
        window.ManiacGames.showNotification(message, type);
    } else {
        console.log(`[Toast-${type}]: ${message}`);
    }
};


// --- ИСПРАВЛЕНО: Новая система навигации ---
async function navigateTo(path) {
    let gameId = null;

    if (path.startsWith('/game/')) {
        gameId = path.split('/')[2];
        path = '/game'; // Общий маршрут для всех игр
    }

    if (currentView && currentView.unmount) {
        currentView.unmount();
    }

    DOMElements.mainContent.innerHTML = '';

    let viewModule;
    if (gameId) {
        viewModule = gameModules[gameId];
        if (!viewModule) {
            console.error(`Game module not found: ${gameId}`);
            navigateTo('/games'); // Редирект на список игр
            return;
        }
    } else {
        viewModule = routes[path];
    }

    if (viewModule) {
        currentView = viewModule;
        // Сохраняем путь для перезагрузки языка
        currentView.path = path;
        const title = viewModule.titleKey ? i18n.t(viewModule.titleKey) : (viewModule.title || '');
        DOMElements.headerTitle.textContent = title;
        DOMElements.mainContent.className = 'main-content view';
        currentView.mount(DOMElements.mainContent);
    } else {
        navigateTo('/taper'); // Фоллбэк на главный экран
    }

    // Обновляем активную иконку в навигации
    document.querySelectorAll('.nav-item').forEach(item => {
        const itemPath = item.dataset.path;
        item.classList.toggle('active', itemPath === path || (path === '/game' && itemPath === '/games'));
    });
};

async function changeLanguage(lang) {
    await i18n.setLanguage(lang);
    generateNavigation();
    // Перерисовываем текущий экран с новым языком
    if (currentView && currentView.path) {
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
    const icons = {
        'star': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>',
        'gamepad-2': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="6" y1="12" x2="10" y2="12"></line><line x1="8" y1="10" x2="8" y2="14"></line><line x1="15" y1="13" x2="15.01" y2="13"></line><line x1="18" y1="11" x2="18.01" y2="11"></line><path d="M10 21a9 9 0 0 0-4.42-16.9"></path><path d="M14 3a9 9 0 0 1 4.42 16.9"></path></svg>',
        'users': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>',
        'user': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>',
        'sliders-horizontal': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="21" y1="10" x2="3" y2="10"></line><line x1="21" y1="6" x2="3" y2="6"></line><line x1="21" y1="14" x2="3" y2="14"></line><line x1="21" y1="18" x2="3" y2="18"></line></svg>'
    };

    DOMElements.navContainer.innerHTML = navItems.map(item => `
        <a href="#" data-path="${item.path}" class="nav-item">
            ${icons[item.icon]}
            <span>${i18n.t(item.labelKey)}</span>
        </a>
    `).join('');
    bindNavEventListeners();
}

function bindNavEventListeners() {
    DOMElements.navContainer.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const path = item.dataset.path;
            navigateTo(path);
            hapticFeedback('light');
            audio.play('tap');
        });
    });
}


// --- ОБУЧЕНИЕ ПРИ ПЕРВОМ ЗАПУСКЕ ---
function showFirstLaunchTutorial() {
    if (!isFirstLaunch()) {
        return;
    }

    const tutorialOverlay = document.createElement('div');
    tutorialOverlay.id = 'tutorial-overlay';
    tutorialOverlay.className = 'tutorial-overlay';

    tutorialOverlay.innerHTML = `
        <div class="tutorial-card">
            <div class="tutorial-icon">⭐</div>
            <h2>Добро пожаловать!</h2>
            <p>Тапай звезду, играй в игры — зарабатывай очки!</p>
            <button id="tutorial-close-btn" class="btn btn-primary">Понятно!</button>
        </div>
    `;

    document.body.appendChild(tutorialOverlay);

    const closeBtn = document.getElementById('tutorial-close-btn');
    effects.applyRippleEffect(closeBtn);

    closeBtn.addEventListener('click', () => {
        tutorialOverlay.classList.add('fade-out');
        hapticFeedback('medium');
        audio.play('tap');
        tutorialOverlay.addEventListener('animationend', () => {
            tutorialOverlay.remove();
            setVisited();
        });
    });
}


// --- ИНИЦИАЛИЗАЦИЯ ПРИЛОЖЕНИЯ ---
const initApp = async () => {
    // ***** ИЗМЕНЕНИЕ ЗДЕСЬ *****
    try {
        const settingsPromise = i18n.init();
        themeManager.init();

        const lowPerf = isLowPerfDevice();
        if (lowPerf) {
            document.body.classList.add('low-perf');
            console.log("Low performance mode enabled.");
        }
        
        try {
            tg = window.Telegram.WebApp;
            tg.ready();
            tg.expand();
            console.log("Telegram WebApp API initialized.");
        } catch (e) {
            console.warn("Telegram WebApp API not found. Running in dev mode.");
        }

        particles.init(DOMElements.particleCanvas);
        if (!lowPerf) {
            requestAnimationFrame(particles.loop);
        }
        
        await settingsPromise;

        window.ManiacGames = {
            updateBalance: updateBalanceDisplay,
            showNotification: showToast,
            playSound: audio.play,
            hapticFeedback,
            particles,
            effects,
            t: i18n.t,
            changeLanguage,
            getCurrentLanguage: i18n.getCurrentLanguage,
            changeTheme: (theme) => themeManager.applyTheme(theme),
            getCurrentTheme: () => themeManager.getCurrentTheme(),
            navigateTo,
            tg,
        };

        DOMElements.splash.style.opacity = '0';
        DOMElements.app.classList.remove('hidden');
        DOMElements.splash.addEventListener('transitionend', () => DOMElements.splash.remove());

        generateNavigation();
        updateBalanceDisplay();
        navigateTo('/taper');

        setTimeout(showFirstLaunchTutorial, 400);
    } catch (e) {
        // Если что-то пойдет не так, мы увидим ошибку прямо на экране
        console.error("Critical error during app initialization:", e);
        document.body.innerHTML = `<div style="color: white; padding: 20px; font-family: monospace; word-break: break-all;">
            <h3>Критическая ошибка</h3>
            <p>Не удалось запустить приложение.</p>
            <p><b>Сообщение:</b> ${e.message}</p>
            <hr>
            <p><b>Стек вызовов:</b><br>${e.stack}</p>
        </div>`;
    }
};


// --- Точка входа в приложение ---
document.addEventListener('DOMContentLoaded', initApp);
