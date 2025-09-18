// --- BUNDLED APPLICATION ---
// This file is a combination of all project's JavaScript files.

(function () {
    'use strict';

    // Global object to hold all modules
    const Maniac = {};

    // --- core/utils.js ---
    Maniac.utils = (function () {
        function hapticFeedback(type) {
            try {
                const tg = window.Telegram?.WebApp;
                if (tg && tg.HapticFeedback) {
                    if (['light', 'medium', 'heavy'].includes(type)) {
                        tg.HapticFeedback.impactOccurred(type);
                    } else if (['success', 'warning', 'error'].includes(type)) {
                        tg.HapticFeedback.notificationOccurred(type);
                    }
                }
            } catch (e) {
                console.warn('Haptic feedback failed:', e);
            }
        }
        return { hapticFeedback };
    })();

    // --- core/rng.js ---
    Maniac.rng = (function() {
        function randomInt(min, max) {
            return Math.floor(Math.random() * (max - min + 1)) + min;
        }
        function weightedRandom(weights) {
            let totalWeight = 0;
            for (const weight of Object.values(weights)) {
                totalWeight += weight;
            }
            let random = Math.random() * totalWeight;
            for (const [item, weight] of Object.entries(weights)) {
                if (random < weight) return item;
                random -= weight;
            }
            return Object.keys(weights)[0];
        }
        return { randomInt, weightedRandom };
    })();

    // --- core/houseedge.js ---
    Maniac.houseedge = (function() {
        const HOUSE_EDGE = 1.00; // 1.00 = 0% edge
        function applyPayout(payout) {
            if (payout <= 0) return 0;
            return Math.floor(payout * HOUSE_EDGE);
        }
        return { applyPayout };
    })();

    // --- core/state.js ---
    Maniac.state = (function () {
        const BALANCE_KEY = 'mg.balance';
        const STATS_KEY = 'mg.stats';
        const VISITED_KEY = 'mg.visited';
        const STARTING_BALANCE = 1000;

        function initStorage() {
            if (localStorage.getItem(BALANCE_KEY) === null) localStorage.setItem(BALANCE_KEY, STARTING_BALANCE.toString());
            if (localStorage.getItem(STATS_KEY) === null) localStorage.setItem(STATS_KEY, JSON.stringify({ wins: 0, losses: 0, maxCrashMultiplier: 0, topWin: 0 }));
            if (localStorage.getItem(VISITED_KEY) === null) localStorage.setItem(VISITED_KEY, 'false');
        }

        function fmt(n) {
            if (n === null || n === undefined) return '0';
            return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
        }

        function getBalance() {
            initStorage();
            return parseInt(localStorage.getItem(BALANCE_KEY), 10);
        }
        function setBalance(n) {
            localStorage.setItem(BALANCE_KEY, Math.floor(n).toString());
        }
        function addBalance(n) { setBalance(getBalance() + n); }
        function subBalance(n) { setBalance(getBalance() - n); }

        function getStats() {
            initStorage();
            return JSON.parse(localStorage.getItem(STATS_KEY));
        }

        function updateStats(newStats) {
            const currentStats = getStats();
            const updated = { ...currentStats, ...newStats };
            if (newStats.maxCrashMultiplier && newStats.maxCrashMultiplier > currentStats.maxCrashMultiplier) updated.maxCrashMultiplier = newStats.maxCrashMultiplier;
            if (newStats.topWin && newStats.topWin > currentStats.topWin) updated.topWin = newStats.topWin;
            if (newStats.wins) updated.wins = currentStats.wins + newStats.wins;
            if (newStats.losses) updated.losses = currentStats.losses + newStats.losses;
            localStorage.setItem(STATS_KEY, JSON.stringify(updated));
        }

        function isFirstLaunch() {
            initStorage();
            return localStorage.getItem(VISITED_KEY) === 'false';
        }
        function setVisited() {
            localStorage.setItem(VISITED_KEY, 'true');
        }

        return { getBalance, addBalance, subBalance, fmt, isFirstLaunch, setVisited, getStats, updateStats };
    })();

    // --- core/audio.js ---
    Maniac.audio = (function () {
        let isMuted = localStorage.getItem('mg.soundMuted') === 'true';
        let sfx = {};
        let audioContextStarted = false;

        function init() {
            if (typeof Tone === 'undefined') {
                console.error("Tone.js is not loaded.");
                return;
            }
            sfx = {
                tap: new Tone.MembraneSynth({ pitchDecay: 0.01, octaves: 6, envelope: { attack: 0.001, decay: 0.1, sustain: 0 } }).toDestination(),
                win: new Tone.PolySynth(Tone.Synth, { envelope: { attack: 0.01, decay: 0.2, sustain: 0.1, release: 0.1 }, volume: -12 }).toDestination(),
                lose: new Tone.MembraneSynth({ pitchDecay: 0.1, octaves: 2, envelope: { attack: 0.01, decay: 0.2, sustain: 0 }, volume: -10 }).toDestination(),
                spinStart: new Tone.NoiseSynth({ noise: { type: 'white' }, envelope: { attack: 0.01, decay: 0.2, sustain: 0 }, volume: -20 }).toDestination(),
                spinStop: new Tone.MembraneSynth({ pitchDecay: 0.01, octaves: 6, envelope: { attack: 0.001, decay: 0.1, sustain: 0 }, volume: -15 }).toDestination(),
                crash: new Tone.Synth({ oscillator: { type: 'sawtooth' }, envelope: { attack: 0.01, decay: 0.2, sustain: 0, release: 0.1 }, volume: -8 }).toDestination(),
                crystalClick: new Tone.MetalSynth({ frequency: 300, envelope: { attack: 0.001, decay: 0.1, release: 0.1 }, harmonicity: 8.5, modulationIndex: 20, resonance: 4000, octaves: 1.5, volume: -15 }).toDestination(),
            };
        }

        async function initAudioContext() {
            if (audioContextStarted || (Tone && Tone.context.state === 'running')) {
                audioContextStarted = true;
                return;
            }
            if (Tone) {
                await Tone.start();
                console.log('AudioContext started.');
                audioContextStarted = true;
            }
        }

        function play(id, options = {}) {
            if (isMuted || Object.keys(sfx).length === 0) return;
            initAudioContext();
            const now = Tone.now() + (options.delay || 0);
            switch (id) {
                case 'tap': sfx.tap.triggerAttackRelease('C4', '32n', now); break;
                case 'win': sfx.win.triggerAttackRelease(['C4', 'E4', 'G4'], '16n', now, 0.35); break;
                case 'lose': sfx.lose.triggerAttackRelease('C2', '8n', now, 0.2); break;
                case 'spinStart': sfx.spinStart.triggerAttackRelease('0.2', now); break;
                case 'spinStop': sfx.spinStop.triggerAttackRelease('C5', '32n', now); break;
                case 'crystalClick': sfx.crystalClick.triggerAttackRelease("C6", "32n", now); break;
                case 'crash': sfx.crash.triggerAttackRelease('C4', '8n', now); sfx.crash.frequency.rampTo('C3', 0.25, now); break;
            }
        }
        function setMuted(muted) {
            isMuted = muted;
            localStorage.setItem('mg.soundMuted', isMuted.toString());
            if (!isMuted) {
                initAudioContext();
                play('tap');
            }
        }
        function getMutedState() { return isMuted; }

        return { init, play, setMuted, getMutedState };
    })();

    // --- core/i18n.js ---
    Maniac.i18n = (function() {
        let currentLang = localStorage.getItem('mg.lang') || 'ru';
        const translations = {
          "ru": { "play_button": "Играть", "copy_button": "Скопировать", "copied_success": "Скопировано!", "share_button": "Поделиться", "nav_main": "Главная", "nav_games": "Игры", "nav_friends": "Друзья", "nav_profile": "Профиль", "nav_settings": "Настройки", "taper_title": "Главная", "games_title": "Игры", "referrals_title": "Друзья", "profile_title": "Профиль", "settings_title": "Настройки", "dice_game_title": "Кости", "crash_game_title": "Crash", "slots_game_title": "Слоты", "coin_game_title": "Орёл/Решка", "game_rtp": "RTP", "referrals_header": "Ваша реферальная ссылка", "referrals_desc": "Пригласите друга и получите <strong>1000 ⭐</strong>, как только он заработает свои первые 5000 ⭐. Ваш друг также получит бонус <strong>500 ⭐</strong> при старте!", "referrals_in_progress": "... в процессе", "referrals_your_referrals": "Ваши рефералы", "copy_failed": "Не удалось скопировать", "share_not_supported": "Поделиться не поддерживается", "profile_level": "Уровень", "profile_balance": "Баланс", "profile_achievements": "Достижения", "profile_history": "История операций", "history_crash_win": "Выигрыш в Crash", "history_slots_bet": "Ставка в Slots", "history_ref_bonus": "Реферальный бонус", "settings_general": "Основные", "settings_sound": "Звук", "settings_haptics": "Вибрация", "settings_appearance": "Внешний вид", "settings_language": "Язык", "settings_theme": "Тема", "settings_theme_dark": "Тёмная", "settings_theme_light": "Светлая", "settings_theme_system": "Системная", "settings_info": "Информация", "settings_rules": "Правила", "settings_support": "Поддержка", "settings_privacy": "Политика", "not_enough_funds": "Недостаточно средств", "win_message": "Выигрыш", "loss_message": "Проигрыш", "dice_make_bet": "Сделайте ставку", "dice_even": "Чёт", "dice_odd": "Нечет", "dice_exact_bet": "Ставка на точное число", "slots_spin": "Крутить", "crash_history": "История", "crash_bet": "Ставка", "crash_place_bet": "Сделать ставку", "crash_accepted": "Ставка принята", "crash_take": "Забрать", "crash_betting_closed": "Приём ставок завершён", "crash_crashed": "Краш!" },
          "es": { "play_button": "Jugar", "nav_main": "Principal", "nav_games": "Juegos", "nav_friends": "Amigos", "nav_profile": "Perfil", "nav_settings": "Ajustes" }
        };

        function setLanguage(lang) {
            if (translations[lang]) {
                currentLang = lang;
                localStorage.setItem('mg.lang', lang);
                document.documentElement.lang = lang;
            }
        }
        function t(key) { return translations[currentLang]?.[key] || key; }
        function getCurrentLanguage() { return currentLang; }
        setLanguage(currentLang);
        return { setLanguage, t, getCurrentLanguage };
    })();

    // --- ui/components/screens/taper.js ---
    Maniac.taper = (function () {
        const { addBalance, getBalance } = Maniac.state;
        const titleKey = 'taper_title';
        let root, elements;

        function updateFlipCounter(start, end) {
            if (!elements?.balanceCounter) return;
            const container = elements.balanceCounter;
            const endStr = end.toString();
            const startStr = start.toString().padStart(endStr.length, ' ');
            container.innerHTML = '';
            for (let i = 0; i < endStr.length; i++) {
                const charContainer = document.createElement('div');
                charContainer.className = 'flip-char';
                charContainer.innerHTML = `<div class="flip-char-inner"><div class="flip-char-front">${startStr[i] || ' '}</div><div class="flip-char-back">${endStr[i]}</div></div>`;
                container.appendChild(charContainer);
                if (startStr[i] !== endStr[i]) {
                    setTimeout(() => charContainer.classList.add('animate'), i * 50);
                }
            }
        }

        function handleTap() {
            const oldBalance = getBalance();
            addBalance(1);
            updateFlipCounter(oldBalance, getBalance());
            if (elements.star) {
                elements.star.classList.add('tapped');
                elements.star.addEventListener('animationend', () => elements.star.classList.remove('tapped'), { once: true });
            }
            Maniac.utils.hapticFeedback('light');
            Maniac.audio.play('crystalClick');
        }

        function mount(rootEl) {
            root = rootEl;
            root.innerHTML = `
                <style>
                    .tapper-star-container { width: 100%; flex-grow: 1; display: flex; align-items: center; justify-content: center; cursor: pointer; user-select: none; -webkit-tap-highlight-color: transparent; }
                    .tapper-star-2d { font-size: 250px; line-height: 1; color: #f92b75; filter: drop-shadow(0 0 25px rgba(249, 43, 117, 0.7)); transition: transform 0.1s ease-out; }
                    .tapper-star-2d.tapped { animation: star-tap-effect 0.2s ease-out; }
                    @keyframes star-tap-effect { 50% { transform: scale(0.9); } }
                </style>
                <div class="tapper-wrapper">
                    <div class="tapper-balance-container">
                        <span class="tapper-balance-icon">⭐</span>
                        <div id="tapper-balance-counter" class="tapper-balance-counter"></div>
                    </div>
                    <div class="tapper-star-container">
                        <div id="tapper-star-2d" class="tapper-star-2d">★</div>
                    </div>
                    <div class="tapper-energy-info"></div>
                </div>`;
            elements = {
                balanceCounter: root.querySelector('#tapper-balance-counter'),
                starContainer: root.querySelector('.tapper-star-container'),
                star: root.querySelector('#tapper-star-2d'),
            };
            updateFlipCounter(0, getBalance());
            elements.starContainer.addEventListener('pointerdown', handleTap);
        }
        function unmount() { root = null; elements = null; }
        return { mount, unmount, titleKey };
    })();

    // --- ui/components/screens/games.js ---
    Maniac.games = (function() {
        const titleKey = 'games_title';
        let rootElement = null;
        let selectedGame = null;
        const games = [
            { id: 'dice', titleKey: 'dice_game_title', rtp: '98.5%' },
            { id: 'crash', titleKey: 'crash_game_title', rtp: '96.0%' },
            { id: 'slots', titleKey: 'slots_game_title', rtp: '94.2%' },
            { id: 'coin', titleKey: 'coin_game_title', rtp: '99.0%' }
        ];

        function getGameIcon(gameId) {
             switch (gameId) {
                case 'dice': return `<svg width="48" height="48" viewBox="0 0 100 100"><g filter="url(#filter0_d_8_2)"><rect x="10" y="10" width="80" height="80" rx="15" fill="url(#paint0_linear_8_2)"/><rect x="11.5" y="11.5" width="77" height="77" rx="13.5" stroke="white" stroke-opacity="0.2" stroke-width="3"/></g><circle cx="30" cy="30" r="8" fill="white"/><circle cx="70" cy="30" r="8" fill="white"/><circle cx="50" cy="50" r="8" fill="white"/><circle cx="30" cy="70" r="8" fill="white"/><circle cx="70" cy="70" r="8" fill="white"/><defs><filter id="filter0_d_8_2" x="0" y="0" width="100" height="100" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0" result="hardAlpha"/><feOffset dy="0"/><feGaussianBlur stdDeviation="5"/><feComposite in2="hardAlpha" operator="out"/><feColorMatrix type="matrix" values="0 0 0 0 0.541667 0 0 0 0 0.4875 0 0 0 0 1 0 0 0 0.3 0"/><feBlend mode="normal" in2="BackgroundImageFix" result="effect1_dropShadow_8_2"/><feBlend mode="normal" in="SourceGraphic" in2="effect1_dropShadow_8_2" result="shape"/></filter><linearGradient id="paint0_linear_8_2" x1="50" y1="10" x2="50" y2="90" gradientUnits="userSpaceOnUse"><stop stop-color="#3A435E"/><stop offset="1" stop-color="#21283C"/></linearGradient></defs></svg>`;
                case 'crash': return `<svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 40C8 40 16 40 24 24S40 8 40 8" stroke="url(#paint0_linear_2_28)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/><path d="M28 8H40V20" stroke="url(#paint1_linear_2_28)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/><defs><linearGradient id="paint0_linear_2_28" x1="8" y1="24" x2="40" y2="24" gradientUnits="userSpaceOnUse"><stop stop-color="#8A7CFF"/><stop offset="1" stop-color="#F92B75"/></linearGradient><linearGradient id="paint1_linear_2_28" x1="28" y1="14" x2="40" y2="14" gradientUnits="userSpaceOnUse"><stop stop-color="#8A7CFF"/><stop offset="1" stop-color="#F92B75"/></linearGradient></defs></svg>`;
                case 'slots': return `<svg width="48" height="48" viewBox="0 0 48 48"><rect x="4" y="8" width="10" height="32" rx="2" stroke="#8A7CFF" stroke-width="2.5"/><rect x="19" y="8" width="10" height="32" rx="2" stroke="#F92B75" stroke-width="2.5"/><rect x="34" y="8" width="10" height="32" rx="2" stroke="#33D6A6" stroke-width="2.5"/></svg>`;
                case 'coin': return `<svg width="48" height="48" viewBox="0 0 100 100"><g filter="url(#filter0_d_12_2)"><circle cx="50" cy="46" r="40" fill="url(#paint0_linear_12_2)"/><circle cx="50" cy="46" r="38" stroke="url(#paint1_linear_12_2)" stroke-width="4"/></g><path d="M50 33L58.6603 48.5H41.3397L50 33Z" fill="#FFC85C"/><path d="M50 63L58.6603 47.5H41.3397L50 63Z" fill="#FFC85C" fill-opacity="0.6"/><defs><filter id="filter0_d_12_2" x="0" y="0" width="100" height="100" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feColorMatrix in="SourceAlpha" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"/><feOffset dy="4"/><feGaussianBlur stdDeviation="5"/><feComposite in2="hardAlpha" operator="out"/><feColorMatrix values="0 0 0 0 0.93 0 0 0 0 0.76 0 0 0 0 0.35 0 0 0 0.4 0"/><feBlend in2="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="effect1_dropShadow_12_2"/></filter><linearGradient id="paint0_linear_12_2" x1="50" y1="6" x2="50" y2="86" gradientUnits="userSpaceOnUse"><stop stop-color="#FFD77A"/><stop offset="1" stop-color="#E8A91E"/></linearGradient><linearGradient id="paint1_linear_12_2" x1="50" y1="6" x2="50" y2="86" gradientUnits="userSpaceOnUse"><stop stop-color="white" stop-opacity="0.8"/><stop offset="1" stop-color="white" stop-opacity="0"/></linearGradient></defs></svg>`;
                default: return `?`;
            }
        }

        function mount(rootEl) {
            rootElement = rootEl;
            const t = Maniac.i18n.t;
            rootElement.innerHTML = `
                <div class="games-grid">
                    ${games.map((game, index) => `
                        <div class="game-card" data-game-id="${game.id}" style="--stagger-index: ${index};">
                            <div class="game-card-icon">${getGameIcon(game.id)}</div>
                            <div class="game-card-title">${t(game.titleKey)}</div>
                            <div class="game-card-info">${t('game_rtp')}: ${game.rtp}</div>
                        </div>`).join('')}
                </div>
                <div id="play-bar" class="play-bar">
                    <button id="play-button" class="btn btn-primary">${t('play_button')}</button>
                </div>`;

            const gameCards = rootElement.querySelectorAll('.game-card');
            const playBar = rootElement.querySelector('#play-bar');
            const playButton = rootElement.querySelector('#play-button');

            gameCards.forEach(card => {
                card.addEventListener('click', () => {
                    gameCards.forEach(c => c.classList.remove('selected'));
                    card.classList.add('selected');
                    selectedGame = card.dataset.gameId;
                    playBar.classList.add('visible');
                    Maniac.utils.hapticFeedback('light');
                });
            });

            playButton.addEventListener('click', () => {
                if (selectedGame && window.ManiacGames) {
                    Maniac.audio.play('tap');
                    Maniac.utils.hapticFeedback('medium');
                    window.ManiacGames.navigateTo(`/game/${selectedGame}`);
                }
            });
        }
        function unmount() { rootElement = null; selectedGame = null; }
        return { mount, unmount, titleKey };
    })();

    Maniac.referrals = (function() {
        const titleKey = 'referrals_title';
        function mount(r){
            const t = Maniac.i18n.t;
            r.innerHTML = `
            <div class="card glassmorphism-card">
                <h2>${t('referrals_header')}</h2>
                <p>${t('referrals_desc')}</p>
            </div>
            <div class="card">
                <h2>${t('referrals_your_referrals')}</h2>
                 <div class="friends-list">
                     <div class="friend-item"><span class="friend-avatar">🧑‍🚀</span><span class="friend-name">Иван</span><span class="friend-bonus success">+1000 ⭐</span></div>
                     <div class="friend-item"><span class="friend-avatar">🧑‍💻</span><span class="friend-name">Алена</span><span class="friend-bonus pending">${t('referrals_in_progress')}</span></div>
                 </div>
            </div>`;
        }
        function unmount(){}
        return { mount, unmount, titleKey };
    })();

    Maniac.profile = (function() {
        const titleKey = 'profile_title';
        function mount(r){
            const t = Maniac.i18n.t;
            const user = { name: "Test User", photo_url: null };
            r.innerHTML = `
            <div class="profile-header">
                <div class="profile-avatar-wrapper"><img src="${user.photo_url || 'https://placehold.co/100x100/111823/EAF2FF?text=' + user.name.charAt(0)}" alt="Аватар" class="profile-avatar"></div>
                <h2 class="profile-name">${user.name}</h2>
                <div class="profile-level"><span>${t('profile_level')} 12</span><div class="progress-bar-sm"><div class="progress-bar-inner-sm" style="width: 65%;"></div></div></div>
            </div>
            <div class="card">
                <h2>${t('profile_balance')}</h2>
                <div class="balance-container"><span class="balance-value-large">${Maniac.state.fmt(Maniac.state.getBalance())}</span> <span class="balance-currency">⭐</span></div>
            </div>
             <div class="card">
                <h2>${t('profile_achievements')}</h2>
                <div class="achievements-grid"><div class="achievement unlocked">🏆</div><div class="achievement">💰</div></div>
            </div>`;
        }
        function unmount(){}
        return { mount, unmount, titleKey };
    })();

    Maniac.settings = (function() {
        const titleKey = 'settings_title';
        function mount(r){
            const t = Maniac.i18n.t;
            r.innerHTML = `
            <div class="card">
                <h2>${t('settings_general')}</h2>
                <div class="settings-list">
                    <div class="setting-item">
                        <label>${t('settings_sound')}</label>
                        <label class="switch"><input type="checkbox" id="sound-toggle" ${!Maniac.audio.getMutedState() ? 'checked' : ''}><span class="switch-track"><span class="switch-thumb"></span></span></label>
                    </div>
                </div>
            </div>
            <div class="card">
                <h2>${t('settings_info')}</h2>
                <div class="settings-links">
                    <a href="#">${t('settings_rules')}</a>
                    <a href="#">${t('settings_support')}</a>
                </div>
            </div>`;
            r.querySelector('#sound-toggle').addEventListener('change', (e) => {
                Maniac.audio.setMuted(!e.target.checked);
            });
        }
        function unmount(){}
        return { mount, unmount, titleKey };
    })();

    // --- GAMES ---
    Maniac.diceGame = (function(){
        const { getBalance, subBalance, addBalance, updateStats } = Maniac.state;
        const { applyPayout } = Maniac.houseedge;
        const { randomInt } = Maniac.rng;
        const titleKey = 'dice_game_title';
        let root, elements, state = {};

        function getDiceFace(v) {
            const dots = { 1:['d-center'], 2:['d-top-left','d-bottom-right'], 3:['d-top-left','d-center','d-bottom-right'], 4:['d-top-left','d-top-right','d-bottom-left','d-bottom-right'], 5:['d-top-left','d-top-right','d-center','d-bottom-left','d-bottom-right'], 6:['d-top-left','d-top-right','d-mid-left','d-mid-right','d-bottom-left','d-bottom-right'] };
            return (dots[v] || []).map(d => `<div class="dot ${d}"></div>`).join('');
        }

        async function playGame(betType) {
            if (state.isRolling) return;
            const t = Maniac.i18n.t;
            if (getBalance() < state.betAmount) return alert(t('not_enough_funds'));
            state.isRolling = true;
            subBalance(state.betAmount);
            window.ManiacGames.updateBalance();
            const result = randomInt(1, 6);
            elements.resultText.textContent = '...';

            elements.dice.classList.add('rolling');
            await new Promise(res => setTimeout(res, 1500));
            elements.dice.innerHTML = getDiceFace(result);
            elements.dice.classList.remove('rolling');

            let isWin = false;
            if (betType === 'even' && result % 2 === 0) isWin = true;
            if (betType === 'odd' && result % 2 !== 0) isWin = true;

            if(isWin) {
                const payout = applyPayout(state.betAmount * 1.9);
                addBalance(payout);
                updateStats({ wins: 1, topWin: payout });
                elements.resultText.textContent = `${t('win_message')} +${payout} ⭐`;
            } else {
                updateStats({ losses: 1 });
                elements.resultText.textContent = `${t('loss_message')}`;
            }
            window.ManiacGames.updateBalance();
            state.isRolling = false;
        }

        function mount(rootEl) {
            root = rootEl;
            state = { isRolling: false, betAmount: 10 };
            const t = Maniac.i18n.t;
            root.innerHTML = `
            <style>.dice-2d-container{display:flex;justify-content:center;align-items:center;min-height:150px}.dice-face{width:100px;height:100px;background:#fff;border-radius:12px;display:grid;padding:10px;box-shadow:0 5px 15px rgba(0,0,0,0.2);transition:transform .3s ease}.dice-face.rolling{transform:rotate(360deg) scale(.8)}.dot{width:20px;height:20px;background:#111;border-radius:50%}.d-center{justify-self:center;align-self:center}.d-top-left{justify-self:start;align-self:start}.d-top-right{justify-self:end;align-self:start}.d-bottom-left{justify-self:start;align-self:end}.d-bottom-right{justify-self:end;align-self:end}.d-mid-left{justify-self:start;align-self:center}.d-mid-right{justify-self:end;align-self:center}</style>
            <div class="card dice-2d-container"><div id="dice-2d-face" class="dice-face">${getDiceFace(6)}</div></div>
            <div class="card">
                <div id="dice-result" style="text-align:center;font-weight:bold;min-height:1.2em;margin-bottom:15px">${t('dice_make_bet')}</div>
                <input type="number" id="dice-bet-input" class="input-field" value="${state.betAmount}">
                <div id="dice-bet-controls" class="chip-controls" style="grid-template-columns:1fr 1fr;margin-top:15px">
                    <button class="btn" data-bet="even">${t('dice_even')}</button>
                    <button class="btn" data-bet="odd">${t('dice_odd')}</button>
                </div>
            </div>`;
            elements = {
                dice: root.querySelector('#dice-2d-face'),
                betInput: root.querySelector('#dice-bet-input'),
                betControls: root.querySelector('#dice-bet-controls'),
                resultText: root.querySelector('#dice-result'),
            };
            elements.betInput.addEventListener('change', e => state.betAmount = Math.max(1, parseInt(e.target.value) || 1));
            elements.betControls.addEventListener('click', e => {
                if (e.target.dataset.bet) playGame(e.target.dataset.bet);
            });
        }
        function unmount() { root = null; elements = null; }
        return { mount, unmount, titleKey };
    })();
    Maniac.crashGame = (function(){ const titleKey = 'crash_game_title'; function mount(r){r.innerHTML = `<h2>Crash (в разработке)</h2>`;} function unmount(){} return {mount,unmount,titleKey};})();
    Maniac.slotsGame = (function(){ const titleKey = 'slots_game_title'; function mount(r){r.innerHTML = `<h2>Слоты (в разработке)</h2>`;} function unmount(){} return {mount,unmount,titleKey};})();
    Maniac.coinGame = (function(){ const titleKey = 'coin_game_title'; function mount(r){r.innerHTML = `<h2>Орёл/Решка (в разработке)</h2>`;} function unmount(){} return {mount,unmount,titleKey};})();


    // --- APP INITIALIZATION ---
    document.addEventListener('DOMContentLoaded', () => {
        const DOMElements = {
            app: document.getElementById('app'),
            splash: document.getElementById('splash-screen'),
            headerTitle: document.getElementById('header-title'),
            balanceValue: document.getElementById('balance-value'),
            mainContent: document.getElementById('main-content'),
            navContainer: document.getElementById('bottom-nav'),
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
            'crash': Maniac.crashGame,
            'slots': Maniac.slotsGame,
            'coin': Maniac.coinGame,
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
                console.error("View not found for path:", path, "or gameId:", gameId);
                return navigateTo('/taper');
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
            const icons = { 'star': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>', 'gamepad-2': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="6" y1="12" x2="10" y2="12"></line><line x1="8" y1="10" x2="8" y2="14"></line><line x1="15" y1="13" x2="15.01" y2="13"></line><line x1="18" y1="11" x2="18.01" y2="11"></line><path d="M10 21a9 9 0 0 0-4.42-16.9"></path><path d="M14 3a9 9 0 0 1 4.42 16.9"></path></svg>', 'users': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>', 'user': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>', 'sliders-horizontal': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="21" y1="10" x2="3" y2="10"></line><line x1="21" y1="6" x2="3" y2="6"></line><line x1="21" y1="14" x2="3" y2="14"></line><line x1="21" y1="18" x2="3" y2="18"></line></svg>'};

            DOMElements.navContainer.innerHTML = navItems.map(item => `
                <a href="#" data-path="${item.path}" class="nav-item">
                    ${icons[item.icon]}
                    <span>${Maniac.i18n.t(item.labelKey)}</span>
                </a>
            `).join('');

            DOMElements.navContainer.querySelectorAll('.nav-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    navigateTo(item.dataset.path);
                    Maniac.utils.hapticFeedback('light');
                    Maniac.audio.play('tap');
                });
            });
        }

        try {
            const tg = window.Telegram.WebApp;
            tg.ready();
            tg.expand();
        } catch (e) {
            console.warn("Telegram API not found.");
        }

        Maniac.audio.init();

        window.ManiacGames = {
            updateBalance: updateBalanceDisplay,
            hapticFeedback: Maniac.utils.hapticFeedback,
            playSound: Maniac.audio.play,
            navigateTo: navigateTo,
        };

        generateNavigation();
        updateBalanceDisplay();
        navigateTo('/taper');

        DOMElements.splash.style.opacity = '0';
        DOMElements.app.classList.remove('hidden');
        DOMElements.splash.addEventListener('transitionend', () => DOMElements.splash.remove());

    });
})();
