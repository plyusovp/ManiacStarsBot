(function () {
    'use strict';

    // Глобальный объект приложения для хранения всех "модулей"
    const Maniac = {};

    // --- [НАЧАЛО] core/state.js ---
    Maniac.state = (function() {
        const BALANCE_KEY = 'mg.balance';
        const STATS_KEY = 'mg.stats';
        const VISITED_KEY = 'mg.visited';
        const STARTING_BALANCE = 1000;

        function initStorage() {
            if (localStorage.getItem(BALANCE_KEY) === null) localStorage.setItem(BALANCE_KEY, STARTING_BALANCE.toString());
            if (localStorage.getItem(STATS_KEY) === null) localStorage.setItem(STATS_KEY, JSON.stringify({ wins: 0, losses: 0, topWin: 0, maxCrashMultiplier: 0 }));
            if (localStorage.getItem(VISITED_KEY) === null) localStorage.setItem(VISITED_KEY, 'false');
        }
        function fmt(n) { return n != null ? n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ") : '0'; }
        function getBalance() { initStorage(); return parseInt(localStorage.getItem(BALANCE_KEY), 10); }
        function setBalance(n) { localStorage.setItem(BALANCE_KEY, Math.floor(n).toString()); }
        function addBalance(n) { setBalance(getBalance() + n); }
        function subBalance(n) { setBalance(getBalance() - n); }
        function isFirstLaunch() { initStorage(); return localStorage.getItem(VISITED_KEY) === 'false'; }
        function setVisited() { localStorage.setItem(VISITED_KEY, 'true'); }
        function getStats() { initStorage(); return JSON.parse(localStorage.getItem(STATS_KEY));}
        function updateStats(newStats) {
            const currentStats = getStats();
            let updated = { ...currentStats };
            if (newStats.wins) updated.wins = (currentStats.wins || 0) + newStats.wins;
            if (newStats.losses) updated.losses = (currentStats.losses || 0) + newStats.losses;
            if (newStats.topWin && newStats.topWin > (currentStats.topWin || 0)) updated.topWin = newStats.topWin;
            if (newStats.maxCrashMultiplier && newStats.maxCrashMultiplier > (currentStats.maxCrashMultiplier || 0)) updated.maxCrashMultiplier = newStats.maxCrashMultiplier;
            localStorage.setItem(STATS_KEY, JSON.stringify(updated));
        }
        initStorage();
        return { getBalance, addBalance, subBalance, fmt, getStats, updateStats, isFirstLaunch, setVisited };
    })();
    // --- [КОНЕЦ] core/state.js ---

    // --- [НАЧАЛО] core/i18n.js ---
    Maniac.i18n = (function() {
        const LANG_KEY = 'mg.lang';
        let currentLang = localStorage.getItem(LANG_KEY) || 'ru';
        const translations = {
          "ru": {"play_button":"Играть","copy_button":"Скопировать","copied_success":"Скопировано!","share_button":"Поделиться","nav_main":"Главная","nav_games":"Игры","nav_friends":"Друзья","nav_profile":"Профиль","nav_settings":"Настройки","taper_title":"Главная","games_title":"Игры","referrals_title":"Друзья","profile_title":"Профиль","settings_title":"Настройки","dice_game_title":"Кости","crash_game_title":"Crash","slots_game_title":"Слоты","coin_game_title":"Орёл/Решка","game_rtp":"RTP","referrals_header":"Ваша реферальная ссылка","referrals_desc":"Пригласите друга и получите <strong>1000 ⭐</strong>, как только он заработает свои первые 5000 ⭐. Ваш друг также получит бонус <strong>500 ⭐</strong> при старте!","referrals_in_progress":"... в процессе","referrals_your_referrals":"Ваши рефералы","copy_failed":"Не удалось скопировать ссылку","share_not_supported":"Функция 'Поделиться' не поддерживается","profile_level":"Уровень","profile_balance":"Баланс","profile_achievements":"Достижения","profile_history":"История операций","history_crash_win":"Выигрыш в Crash","history_slots_bet":"Ставка в Slots","history_ref_bonus":"Реферальный бонус","settings_general":"Основные","settings_sound":"Звуковые эффекты","settings_haptics":"Вибрация (Тактильный отклик)","settings_appearance":"Внешний вид","settings_language":"Язык","not_enough_funds":"Недостаточно средств","win_message":"Выигрыш","loss_message":"Проигрыш","dice_make_bet":"Сделайте ставку","dice_even":"Чёт","dice_odd":"Нечет","dice_exact_bet":"Ставка на точное число","slots_spin":"Крутить","crash_history":"История","crash_bet":"Ставка","crash_place_bet":"Сделать ставку","crash_accepted":"Ставка принята","crash_take":"Забрать","crash_betting_closed":"Приём ставок завершён","crash_crashed":"Краш!"},
        };
        function init() { setLanguage(currentLang); }
        function setLanguage(lang) { if (translations[lang]) { currentLang = lang; localStorage.setItem(LANG_KEY, lang); document.documentElement.lang = lang;} }
        function t(key) { return translations[currentLang]?.[key] || key; }
        return { init, setLanguage, t, getCurrentLanguage: () => currentLang };
    })();
    // --- [КОНЕЦ] core/i18n.js ---

    // --- [НАЧАЛО] core/utils.js ---
    Maniac.utils = { hapticFeedback: (type) => { try { if(window.Telegram?.WebApp?.HapticFeedback) window.Telegram.WebApp.HapticFeedback.impactOccurred(type); } catch(e){} } };
    // --- [КОНЕЦ] core/utils.js ---

    // --- [НАЧАЛО] api.js ---
    Maniac.api = (function() {
        function getUser() {
            const tg = window.Telegram?.WebApp;
            if (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) {
                const user = tg.initDataUnsafe.user;
                return { id: user.id, name: user.first_name || user.username || 'User', photo_url: user.photo_url || null };
            }
            return { id: 123456, name: 'Test User', photo_url: null };
        }
        return { getUser };
    })();
    // --- [КОНЕЦ] api.js ---

    // --- [НАЧАЛО] taper.js ---
    Maniac.taper = (function() {
        const { addBalance } = Maniac.state;
        const titleKey = 'taper_title';
        function handleTap() {
            addBalance(1);
            window.ManiacGames.updateBalance();
            Maniac.utils.hapticFeedback('light');
            const star = document.querySelector('#tapper-star');
            if (star) {
                star.classList.add('tapped');
                setTimeout(() => star.classList.remove('tapped'), 150);
            }
        }
        function mount(rootEl) {
            rootEl.innerHTML = `<div class="tapper-wrapper"><div class="tapper-star-container" id="star-container"><div id="tapper-star" class="star-2d"></div></div></div>`;
            document.getElementById('star-container').addEventListener('pointerdown', handleTap);
        }
        return { titleKey, mount, unmount: () => {} };
    })();
    // --- [КОНЕЦ] taper.js ---

    // --- [НАЧАЛО] games.js ---
    Maniac.games = (function() {
        const titleKey = 'games_title';
        let rootElement, selectedGame;
        const games = [ { id: 'dice', titleKey: 'dice_game_title', rtp: '98.5%' }, { id: 'crash', titleKey: 'crash_game_title', rtp: '96.0%' }, { id: 'slots', titleKey: 'slots_game_title', rtp: '94.2%' }, { id: 'coin', titleKey: 'coin_game_title', rtp: '99.0%' }];
        function render() {
            const t = Maniac.i18n.t;
            rootElement.innerHTML = `
                <div class="games-grid">
                    ${games.map((game, i) => `<div class="game-card" data-game-id="${game.id}" style="--stagger-index: ${i};"><div class="game-card-title">${t(game.titleKey)}</div><div class="game-card-info">${t('game_rtp')}: ${game.rtp}</div></div>`).join('')}
                </div>
                <div id="play-bar" class="play-bar"><button id="play-button" class="btn btn-primary">${t('play_button')}</button></div>`;
            addEventListeners();
        }
        function addEventListeners() {
            const gameCards = rootElement.querySelectorAll('.game-card');
            const playBar = rootElement.querySelector('#play-bar');
            gameCards.forEach(card => card.addEventListener('click', () => {
                gameCards.forEach(c => c.classList.remove('selected'));
                card.classList.add('selected');
                selectedGame = card.dataset.gameId;
                playBar.classList.add('visible');
            }));
            rootElement.querySelector('#play-button').addEventListener('click', () => { if (selectedGame) window.ManiacGames.navigateTo(`/game/${selectedGame}`); });
        }
        return { titleKey, mount: (el) => { rootElement = el; render(); }, unmount: () => { rootElement = null; selectedGame = null; } };
    })();
    // --- [КОНЕЦ] games.js ---

    // --- [НАЧАЛО] referrals.js ---
    Maniac.referrals = (function(){
        const titleKey = 'referrals_title';
        function mount(el) {
            const t = Maniac.i18n.t;
            el.innerHTML = `<div class="card glassmorphism-card"><h2>${t('referrals_header')}</h2><p>${t('referrals_desc')}</p></div>
            <div class="card"><h2>${t('referrals_your_referrals')}</h2><div class="friends-list">
                <div class="friend-item"><span class="friend-avatar">🧑‍🚀</span><span class="friend-name">Иван Петров</span><span class="friend-bonus success">+1000 ⭐</span></div>
                <div class="friend-item"><span class="friend-avatar">🧐</span><span class="friend-name">Максим Воронов</span><span class="friend-bonus pending">${t('referrals_in_progress')}</span></div>
            </div></div>`;
        }
        return { titleKey, mount, unmount: () => {} };
    })();
    // --- [КОНЕЦ] referrals.js ---

    // --- [НАЧАЛО] profile.js ---
    Maniac.profile = (function(){
        const titleKey = 'profile_title';
        function mount(el) {
            const t = Maniac.i18n.t;
            const user = Maniac.api.getUser();
            const { getBalance, fmt } = Maniac.state;
            el.innerHTML = `<div class="profile-header">
                <div class="profile-avatar-wrapper"><img src="${user.photo_url || 'https://placehold.co/100x100/111823/EAF2FF?text=' + user.name.charAt(0)}" alt="Аватар" class="profile-avatar"></div>
                <h2 class="profile-name">${user.name}</h2>
                <div class="profile-level">${t('profile_level')} 1</div>
            </div>
            <div class="card"><h2>${t('profile_balance')}</h2><div class="balance-container"><span class="balance-value-large">${fmt(getBalance())}</span> <span class="balance-currency">⭐</span></div></div>`;
        }
        return { titleKey, mount, unmount: () => {} };
    })();
    // --- [КОНЕЦ] profile.js ---

    // --- [НАЧАЛО] settings.js ---
    Maniac.settings = (function(){
        const titleKey = 'settings_title';
        function mount(el) {
            const t = Maniac.i18n.t;
            el.innerHTML = `<div class="card"><h2>${t('settings_general')}</h2>
            <div class="settings-list"><div class="setting-item"><label>${t('settings_sound')}</label><label class="switch"><input type="checkbox" checked><span class="switch-track"><span class="switch-thumb"></span></span></label></div></div></div>`;
        }
        return { titleKey, mount, unmount: () => {} };
    })();
    // --- [КОНЕЦ] settings.js ---

    // --- ЗАГЛУШКИ ДЛЯ ИГР (пока не перенесены) ---
    Maniac.diceGame = { titleKey: 'dice_game_title', mount: (el) => el.innerHTML = `<div class="card"><h2>${Maniac.i18n.t('dice_game_title')}</h2><p>В разработке</p></div>`, unmount: () => {} };
    Maniac.crashGame = { titleKey: 'crash_game_title', mount: (el) => el.innerHTML = `<div class="card"><h2>${Maniac.i18n.t('crash_game_title')}</h2><p>В разработке</p></div>`, unmount: () => {} };
    Maniac.slotsGame = { titleKey: 'slots_game_title', mount: (el) => el.innerHTML = `<div class="card"><h2>${Maniac.i18n.t('slots_game_title')}</h2><p>В разработке</p></div>`, unmount: () => {} };
    Maniac.coinGame = { titleKey: 'coin_game_title', mount: (el) => el.innerHTML = `<div class="card"><h2>${Maniac.i18n.t('coin_game_title')}</h2><p>В разработке</p></div>`, unmount: () => {} };

    // --- Основная логика приложения (app.js) ---
    (function() {
        const DOMElements = { app: document.getElementById('app'), splash: document.getElementById('splash-screen'), headerTitle: document.getElementById('header-title'), balanceValue: document.getElementById('balance-value'), mainContent: document.getElementById('main-content'), navContainer: document.getElementById('bottom-nav') };
        const routes = { '/taper': Maniac.taper, '/games': Maniac.games, '/referrals': Maniac.referrals, '/profile': Maniac.profile, '/settings': Maniac.settings };
        const gameModules = { 'dice': Maniac.diceGame, 'crash': Maniac.crashGame, 'slots': Maniac.slotsGame, 'coin': Maniac.coinGame };
        let currentView = null;

        function updateBalanceDisplay() { DOMElements.balanceValue.textContent = Maniac.state.fmt(Maniac.state.getBalance()); }

        function navigateTo(path) {
            let gameId = null;
            if (path.startsWith('/game/')) { gameId = path.split('/')[2]; path = '/game'; }
            if (currentView && currentView.unmount) currentView.unmount();
            const viewModule = gameId ? gameModules[gameId] : routes[path];
            if (!viewModule) { return navigateTo('/taper'); }
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
            const navItems = [ { path: '/taper', icon: 'star', labelKey: 'nav_main' }, { path: '/games', icon: 'gamepad-2', labelKey: 'nav_games' }, { path: '/referrals', icon: 'users', labelKey: 'nav_friends' }, { path: '/profile', icon: 'user', labelKey: 'nav_profile' }, { path: '/settings', icon: 'sliders-horizontal', labelKey: 'nav_settings' }];
            const icons = { 'star': '⭐', 'gamepad-2': '🎮', 'users': '👥', 'user': '👤', 'sliders-horizontal': '⚙️' };
            DOMElements.navContainer.innerHTML = navItems.map(item => `<a href="#" data-path="${item.path}" class="nav-item"><div style="font-size: 24px;">${icons[item.icon]}</div><span>${Maniac.i18n.t(item.labelKey)}</span></a>`).join('');
            DOMElements.navContainer.querySelectorAll('.nav-item').forEach(item => item.addEventListener('click', (e) => { e.preventDefault(); navigateTo(item.dataset.path); Maniac.utils.hapticFeedback('light'); }));
        }

        async function initApp() {
            Maniac.i18n.init();
            try { const tg = window.Telegram.WebApp; tg.ready(); tg.expand(); window.ManiacGames = { tg }; } catch (e) { console.warn("TG API not found."); }
            window.ManiacGames = { ...(window.ManiacGames || {}), updateBalance: updateBalanceDisplay, hapticFeedback: Maniac.utils.hapticFeedback, navigateTo: navigateTo };
            generateNavigation();
            updateBalanceDisplay();
            navigateTo('/taper');
            setTimeout(() => {
                DOMElements.splash.style.opacity = '0';
                DOMElements.app.classList.remove('hidden');
                DOMElements.splash.addEventListener('transitionend', () => DOMElements.splash.remove());
            }, 100);
        }

        document.addEventListener('DOMContentLoaded', initApp);
    })();

})();
