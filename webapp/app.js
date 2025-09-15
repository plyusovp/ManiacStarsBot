// Импортируем экраны
import * as taper from './screens/taper.js';
import * as games from './screens/games.js';
import * as referrals from './screens/referrals.js';
import * as profile from './screens/profile.js';
import * as settings from './screens/settings.js';
import * as uikit from './screens/uikit.js';

// Импортируем утилиты
import { getBalance, fmt } from './lib/balance.js';
import * as audio from './lib/audio.js';
import { hapticFeedback } from './lib/utils.js';
import * as particles from './lib/particles.js';
import { isLowPerfDevice } from './lib/perfomance.js';
import * as i18n from './lib/i18n.js';
// --- ✨ НОВОЕ: Импортируем модуль с эффектами ---
import * as effects from './lib/effects.js';

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

// --- DOM Elements ---
const DOMElements = {
    app: document.getElementById('app'),
    splash: document.getElementById('splash-screen'),
    headerTitle: document.getElementById('header-title'),
    balanceValue: document.getElementById('balance-value'),
    mainContent: document.getElementById('main-content'),
    navContainer: document.getElementById('bottom-nav'),
    particleCanvas: document.getElementById('particle-canvas'),
};

// --- Theme Manager ---
const themeManager = {
    THEME_KEY: 'mg.theme',
    currentTheme: 'dark',

    init() {
        this.currentTheme = localStorage.getItem(this.THEME_KEY) || 'dark'; // Тёмная по умолчанию
        this.applyTheme(this.currentTheme);

        // Слушаем изменения системной темы
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            if (this.currentTheme === 'system') {
                this._applyActualTheme(this.getSystemTheme());
            }
        });
    },

    applyTheme(theme) {
        this.currentTheme = theme;
        localStorage.setItem(this.THEME_KEY, theme);

        let themeToApply = theme;
        if (theme === 'system') {
            themeToApply = this.getSystemTheme();
        }

        this._applyActualTheme(themeToApply);
    },

    _applyActualTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        // Обновляем цвет для Telegram WebApp
        if(window.ManiacGames && window.ManiacGames.tg) {
             window.ManiacGames.tg.setHeaderColor(theme === 'dark' ? '#111823' : '#FFFFFF');
             window.ManiacGames.tg.setBackgroundColor(theme === 'dark' ? '#0B0E12' : '#F0F2F5');
        }
    },

    getSystemTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    },

    getCurrentTheme() {
        return this.currentTheme;
    }
};


const updateBalanceDisplay = () => {
    DOMElements.balanceValue.textContent = fmt(getBalance());
};

const showToast = (message, type = 'info') => {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '❌';
    if (type === 'warning') icon = '⚠️';
    toast.innerHTML = `${icon} ${message}`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'toast-out 0.5s ease-out forwards';
        toast.addEventListener('animationend', () => toast.remove());
    }, 4000);
};

const router = async () => {
    if (currentView && currentView.element) {
        if (currentView.module.unmount) {
            currentView.module.unmount();
        }
        currentView.element.remove();
        currentView = null;
    }

    const path = window.location.hash.slice(1) || '/taper';
    let module;
    let titleKey;

    const gameMatch = path.match(/^\/game\/(.+)/);
    const navLinks = DOMElements.navContainer.querySelectorAll('.nav-item');

    if (gameMatch) {
        const gameId = gameMatch[1];
        try {
            const gameModule = await import(`./games/${gameId}.js`);
            module = gameModule;
            titleKey = module.titleKey || 'games_title';
        } catch (e) {
            console.error(`Failed to load game module: ${gameId}`, e);
            window.location.hash = '/games';
            return;
        }
        navLinks.forEach(link => link.classList.remove('active'));
    } else {
        const routeKey = path.startsWith('/') ? path : `/${path}`;
        module = routes[routeKey] || routes['/taper'];
        titleKey = module.titleKey || 'taper_title';

        navLinks.forEach(link => {
            link.classList.toggle('active', link.getAttribute('href') === `#${routeKey}`);
        });
    }

    const viewContainer = document.createElement('div');
    viewContainer.className = `view ${path.substring(1).replace('/', '-')}-view`;
    DOMElements.mainContent.appendChild(viewContainer);

    if (module.mount) {
        module.mount(viewContainer);
    }

    currentView = { module, element: viewContainer };
    DOMElements.headerTitle.textContent = i18n.t(titleKey);
};

async function changeLanguage(lang) {
    i18n.setLanguage(lang);
    generateNavigation();
    await router();
}


function generateNavigation() {
    const navItems = [
        { href: '#/taper', icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>', key: 'nav_main' },
        { href: '#/games', icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="4.3"/><path d="M8.5 11.5a.5.5 0 1 0-1 0 .5.5 0 0 0 1 0z"/><path d="M16.5 11.5a.5.5 0 1 0-1 0 .5.5 0 0 0 1 0z"/><path d="M15.5 15.5a.5.5 0 1 0-1 0 .5.5 0 0 0 1 0z"/><path d="M9.5 15.5a.5.5 0 1 0-1 0 .5.5 0 0 0 1 0z"/></svg>', key: 'nav_games' },
        { href: '#/referrals', icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.72"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.72-1.72"/></svg>', key: 'nav_friends' },
        { href: '#/profile', icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>', key: 'nav_profile' },
        { href: '#/settings', icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>', key: 'nav_settings' }
    ];

    DOMElements.navContainer.innerHTML = navItems.map(item => `
        <a href="${item.href}" class="nav-item">
            ${item.icon}
            <span>${i18n.t(item.key)}</span>
        </a>
    `).join('');

    bindNavEventListeners();
}

function bindNavEventListeners() {
    const navLinks = DOMElements.navContainer.querySelectorAll('.nav-item');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const path = link.getAttribute('href');
            if (window.location.hash !== path) {
                window.location.hash = path;
                hapticFeedback('light');
                audio.play('tap');
            }
        });
    });
}

const init = async () => {
    console.log("Maniac Games: Initializing...");

    // --- Инициализация менеджера тем (до всего остального) ---
    themeManager.init();

    await i18n.init();

    if (isLowPerfDevice()) {
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
    requestAnimationFrame(particles.loop);

    setTimeout(() => {
        DOMElements.splash.style.opacity = '0';
        DOMElements.app.classList.remove('hidden');
        setTimeout(() => DOMElements.splash.remove(), 500);
    }, 1800);

    window.ManiacGames = {
        updateBalance: updateBalanceDisplay,
        showNotification: showToast,
        playSound: audio.play,
        hapticFeedback,
        particles,
        // --- ✨ НОВОЕ: Добавляем эффекты в глобальный объект ---
        effects,
        t: i18n.t,
        changeLanguage,
        getCurrentLanguage: i18n.getCurrentLanguage,
        changeTheme: (theme) => themeManager.applyTheme(theme),
        getCurrentTheme: () => themeManager.getCurrentTheme(),
        tg,
    };

    generateNavigation();
    window.addEventListener('hashchange', router);

    updateBalanceDisplay();
    router();
};

document.addEventListener('DOMContentLoaded', init);

