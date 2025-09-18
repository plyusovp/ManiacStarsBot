(function () {
    'use strict';

    // Глобальный объект приложения для хранения всех "модулей"
    const Maniac = {};

    // --- Core: state.js ---
    Maniac.state = (function() {
        const BALANCE_KEY = 'mg.balance';
        const STATS_KEY = 'mg.stats';
        const VISITED_KEY = 'mg.visited';
        const STARTING_BALANCE = 1000;

        function initStorage() {
            if (localStorage.getItem(BALANCE_KEY) === null) localStorage.setItem(BALANCE_KEY, STARTING_BALANCE.toString());
            if (localStorage.getItem(STATS_KEY) === null) localStorage.setItem(STATS_KEY, JSON.stringify({ wins: 0, losses: 0, topWin: 0 }));
            if (localStorage.getItem(VISITED_KEY) === null) localStorage.setItem(VISITED_KEY, 'false');
        }
        function fmt(n) { return n ? n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ") : '0'; }
        function getBalance() { initStorage(); return parseInt(localStorage.getItem(BALANCE_KEY), 10); }
        function setBalance(n) { localStorage.setItem(BALANCE_KEY, Math.floor(n).toString()); }
        function addBalance(n) { setBalance(getBalance() + n); }
        function subBalance(n) { setBalance(getBalance() - n); }
        function isFirstLaunch() { initStorage(); return localStorage.getItem(VISITED_KEY) === 'false'; }
        function setVisited() { localStorage.setItem(VISITED_KEY, 'true'); }
        function updateStats(newStats) { /* ...логика обновления статистики... */ }

        initStorage();
        return { getBalance, setBalance, addBalance, subBalance, fmt, isFirstLaunch, setVisited, updateStats };
    })();

    // --- Core: i18n.js ---
    Maniac.i18n = (function() {
        const LANG_KEY = 'mg.lang';
        let currentLang = localStorage.getItem(LANG_KEY) || 'ru';
        const translations = {
          "ru": {"play_button":"Играть","copy_button":"Скопировать","copied_success":"Скопировано!","share_button":"Поделиться","nav_main":"Главная","nav_games":"Игры","nav_friends":"Друзья","nav_profile":"Профиль","nav_settings":"Настройки","taper_title":"Главная","games_title":"Игры","referrals_title":"Друзья","profile_title":"Профиль","settings_title":"Настройки","dice_game_title":"Кости","crash_game_title":"Crash","slots_game_title":"Слоты","coin_game_title":"Орёл/Решка","game_rtp":"RTP","referrals_header":"Ваша реферальная ссылка","referrals_desc":"Пригласите друга и получите <strong>1000 ⭐</strong>...","profile_level":"Уровень","profile_balance":"Баланс","settings_general":"Основные","settings_sound":"Звуковые эффекты","not_enough_funds":"Недостаточно средств","win_message":"Выигрыш","loss_message":"Проигрыш"},
          "es": {"play_button":"Jugar","copy_button":"Copiar","copied_success":"¡Copiado!","share_button":"Compartir","nav_main":"Principal","nav_games":"Juegos","nav_friends":"Amigos","nav_profile":"Perfil","nav_settings":"Ajustes","taper_title":"Principal","games_title":"Juegos","referrals_title":"Amigos","profile_title":"Perfil","settings_title":"Ajustes","dice_game_title":"Dados","crash_game_title":"Crash","slots_game_title":"Tragamonedas","coin_game_title":"Cara/Cruz","game_rtp":"RTP","referrals_header":"Tu enlace de referido","referrals_desc":"Invita a un amigo y recibe <strong>1000 ⭐</strong>...","profile_level":"Nivel","profile_balance":"Saldo","settings_general":"General","settings_sound":"Efectos de sonido","not_enough_funds":"Fondos insuficientes","win_message":"Ganancia","loss_message":"Pérdida"}
        };
        function init() { setLanguage(currentLang); }
        function setLanguage(lang) { if (translations[lang]) { currentLang = lang; localStorage.setItem(LANG_KEY, lang); } }
        function t(key) { return translations[currentLang]?.[key] || key; }
        function getCurrentLanguage() { return currentLang; }
        return { init, setLanguage, t, getCurrentLanguage };
    })();

    // --- Core: audio.js, effects.js, etc. (здесь будет код из других core-файлов) ---
    Maniac.audio = { play: (sound) => { try { if (Tone) new Tone.Synth().toDestination().triggerAttackRelease("C4", "8n"); } catch(e) {} } };
    Maniac.effects = { applyRippleEffect: () => {}, launchConfetti: () => {} };
    Maniac.particles = { init: () => {}, loop: () => {}, emit: () => {} };
    Maniac.performance = { isLowPerfDevice: () => false };
    Maniac.utils = { hapticFeedback: (type) => { try { window.Telegram.WebApp.HapticFeedback.impactOccurred(type); } catch(e){} } };

    // --- Screens ---
    Maniac.taper = (function() {
        const { addBalance } = Maniac.state;
        const titleKey = 'taper_title';
        function handleTap() {
            addBalance(1);
            window.ManiacGames.updateBalance();
            Maniac.utils.hapticFeedback('light');
            document.querySelector('#tapper-star')?.classList.add('tapped');
            setTimeout(() => document.querySelector('#tapper-star')?.classList.remove('tapped'), 150);
        }
        function mount(rootEl) {
            rootEl.innerHTML = `<div class="tapper-wrapper"><div class="tapper-star-container" id="star-container"><div id="tapper-star" class="star-2d"></div></div></div>`;
            document.getElementById('star-container').addEventListener('pointerdown', handleTap);
        }
        return { titleKey, mount, unmount: () => {} };
    })();

    Maniac.games = (function() {
        const titleKey = 'games_title';
        function mount(rootEl) {
             rootEl.innerHTML = `<div class="card"><h2>${Maniac.i18n.t(titleKey)}</h2><p>Нажмите на игру, чтобы начать.</p> <button id="play-dice" class="btn btn-secondary">Играть в кости</button></div>`;
             document.getElementById('play-dice').addEventListener('click', () => window.ManiacGames.navigateTo('/game/dice'));
        }
        return { titleKey, mount, unmount: () => {} };
    })();

    Maniac.referrals = { titleKey: 'referrals_title', mount: (el) => el.innerHTML = `<div class="card"><h2>${Maniac.i18n.t('referrals_title')}</h2></div>`, unmount: () => {} };
    Maniac.profile = { titleKey: 'profile_title', mount: (el) => el.innerHTML = `<div class="card"><h2>${Maniac.i18n.t('profile_title')}</h2></div>`, unmount: () => {} };
    Maniac.settings = { titleKey: 'settings_title', mount: (el) => el.innerHTML = `<div class="card"><h2>${Maniac.i18n.t('settings_title')}</h2></div>`, unmount: () => {} };

    // --- Games ---
    Maniac.diceGame = { titleKey: 'dice_game_title', mount: (el) => el.innerHTML = `<div class="card"><h2>${Maniac.i18n.t('dice_game_title')}</h2><p>Игровой процесс...</p></div>`, unmount: () => {} };


    // --- Основная логика приложения (app.js) ---
    (function() {
        const DOMElements = {
            app: document.getElementById('app'),
            splash: document.getElementById('splash-screen'),
            headerTitle: document.getElementById('header-title'),
            balanceValue: document.getElementById('balance-value'),
            mainContent: document.getElementById('main-content'),
            navContainer: document.getElementById('bottom-nav'),
            particleCanvas: document.getElementById('particle-canvas'),
        };

        const routes = {
            '/taper': Maniac.taper,
            '/games': Maniac.games,
            '/referrals': Maniac.referrals,
            '/profile': Maniac.profile,
            '/settings': Maniac.settings,
        };
        const gameModules = {
            'dice': Maniac.diceGame,
        };

        let currentView = null;

        function updateBalanceDisplay() {
            DOMElements.balanceValue.textContent = Maniac.state.fmt(Maniac.state.getBalance());
        }

        function navigateTo(path) {
            let gameId = null;
            if (path.startsWith('/game/')) {
                gameId = path.split('/')[2];
                path = '/game';
            }

            if (currentView && currentView.unmount) currentView.unmount();

            const viewModule = gameId ? gameModules[gameId] : routes[path];

            if (!viewModule) {
                console.error("View not found for path:", path);
                navigateTo('/taper');
                return;
            }

            currentView = viewModule;
            DOMElements.headerTitle.textContent = Maniac.i18n.t(viewModule.titleKey);
            DOMElements.mainContent.innerHTML = '';
            viewModule.mount(DOMElements.mainContent);

            document.querySelectorAll('.nav-item').forEach(item => {
                const itemPath = item.dataset.path;
                item.classList.toggle('active', itemPath === path || (path === '/game' && itemPath === '/games'));
            });
        }

        function generateNavigation() {
            const navItems = [
                { path: '/taper', icon: 'star', labelKey: 'nav_main' },
                { path: '/games', icon: 'gamepad-2', labelKey: 'nav_games' },
                { path: '/referrals', icon: 'users', labelKey: 'nav_friends' },
                { path: '/profile', icon: 'user', labelKey: 'nav_profile' },
                { path: '/settings', icon: 'sliders-horizontal', labelKey: 'nav_settings' },
            ];
             const icons = { 'star': '⭐', 'gamepad-2': '🎮', 'users': '👥', 'user': '👤', 'sliders-horizontal': '⚙️' };
            DOMElements.navContainer.innerHTML = navItems.map(item => `
                <a href="#" data-path="${item.path}" class="nav-item">
                    <div style="font-size: 24px;">${icons[item.icon]}</div>
                    <span>${Maniac.i18n.t(item.labelKey)}</span>
                </a>`).join('');

            DOMElements.navContainer.querySelectorAll('.nav-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    navigateTo(item.dataset.path);
                });
            });
        }

        async function initApp() {
            Maniac.i18n.init();

            try {
                const tg = window.Telegram.WebApp;
                tg.ready();
                tg.expand();
                window.ManiacGames = { tg };
            } catch (e) { console.warn("TG API not found."); }

            window.ManiacGames = {
                ...(window.ManiacGames || {}),
                updateBalance: updateBalanceDisplay,
                hapticFeedback: Maniac.utils.hapticFeedback,
                navigateTo: navigateTo
            };

            generateNavigation();
            updateBalanceDisplay();
            navigateTo('/taper');

            setTimeout(() => {
                DOMElements.splash.style.opacity = '0';
                DOMElements.app.classList.remove('hidden');
                DOMElements.splash.addEventListener('transitionend', () => DOMElements.splash.remove());
            }, 100); // Небольшая задержка для плавной анимации
        }

        document.addEventListener('DOMContentLoaded', initApp);
    })();

})();
