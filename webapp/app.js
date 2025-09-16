// --- ИЗМЕНЕНА СТРУКТУРА ИМПОРТОВ ---
// Экраны
import * as taper from './ui/screens/taper.js';
import * as games from './ui/screens/games.js';
import * as referrals from './ui/screens/referrals.js';
import * as profile from './ui/screens/profile.js';
import * as settings from './ui/screens/settings.js';
import * as uikit from './ui/screens/uikit.js';

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


// --- UI-ХЕЛПЕРЫ (без изменений) ---
const updateBalanceDisplay = () => { /* ... */ };
const showToast = (message, type = 'info') => { /* ... */ };

// --- РОУТЕР (без изменений) ---
const router = async () => { /* ... */ };
async function changeLanguage(lang) { /* ... */ };

// --- ГЕНЕРАЦИЯ НАВИГАЦИИ (без изменений) ---
function generateNavigation() { /* ... */ };
function bindNavEventListeners() { /* ... */ };

// --- НОВАЯ ФУНКЦИЯ: Показ обучения при первом запуске ---
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
    effects.applyRippleEffect(closeBtn); // Добавим эффект на кнопку

    closeBtn.addEventListener('click', () => {
        tutorialOverlay.classList.add('fade-out');
        hapticFeedback('medium');
        audio.play('tap');
        tutorialOverlay.addEventListener('animationend', () => {
            tutorialOverlay.remove();
            setVisited(); // Отмечаем, что пользователь видел обучение
        });
    });
}


// --- ОБНОВЛЕННАЯ ФУНКЦИЯ ИНИЦИАЛИЗАЦИИ ---
const initApp = async () => {
    console.log("Maniac Stars: Application Start");

    // Пункт 17.1: Прочитать localStorage (настройки темы и языка)
    const settingsPromise = i18n.init(); // Асинхронная загрузка переводов
    themeManager.init(); // Синхронно, чтобы избежать мигания темы

    // Пункт 17.2: Определить производительность
    const lowPerf = isLowPerfDevice();
    if (lowPerf) {
        document.body.classList.add('low-perf');
        console.log("Low performance mode enabled.");
    }

    // Пункт 17.3: Предзагрузить ресурсы (ассеты встроены в код, предзагрузка не требуется)
    console.log("Assets are code-integrated, no pre-fetch needed.");

    // Инициализация Telegram API и фоновых систем
    try {
        tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();
        console.log("Telegram WebApp API initialized.");
    } catch (e) {
        console.warn("Telegram WebApp API not found. Running in dev mode.");
    }

    particles.init(DOMElements.particleCanvas);
    if (!lowPerf) { // Запускаем цикл частиц только на мощных устройствах
        requestAnimationFrame(particles.loop);
    }

    // Дожидаемся загрузки переводов перед отрисовкой
    await settingsPromise;

    // Создаем глобальный объект для доступа из других модулей
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
        tg,
    };

    // Пункт 17.4: Отрисовать базу и скрыть сплэш-экран
    DOMElements.splash.style.opacity = '0';
    DOMElements.app.classList.remove('hidden');
    DOMElements.splash.addEventListener('transitionend', () => DOMElements.splash.remove());

    // Пункт 17.5: Активировать роутер
    generateNavigation();
    window.addEventListener('hashchange', router);
    updateBalanceDisplay();
    await router(); // Первый вызов для отрисовки начального экрана

    // Пункт 17.6: Показать обучение
    setTimeout(showFirstLaunchTutorial, 400); // Небольшая задержка для плавности
};

// --- Точка входа в приложение ---
document.addEventListener('DOMContentLoaded', initApp);
