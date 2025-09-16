export const titleKey = 'games_title'; // <-- Ключ для заголовка

let rootElement = null;
let selectedGame = null;

// Игры теперь используют ключи для названий
const games = [
    { id: 'dice', titleKey: 'dice_game_title', rtp: '98.5%', volatility: 'Низкая' },
    { id: 'crash', titleKey: 'crash_game_title', rtp: '96.0%', volatility: 'Высокая' },
    { id: 'slots', titleKey: 'slots_game_title', rtp: '94.2%', volatility: 'Средняя' },
    { id: 'coin', titleKey: 'coin_game_title', rtp: '99.0%', volatility: 'Низкая' }
];

function render() {
    if (!rootElement) return; // Добавим проверку
    const t = window.ManiacGames.t; // <-- ИСПРАВЛЕНО: Доступ к t внутри функции
    rootElement.innerHTML = `
        <div class="games-grid">
            ${games.map((game, index) => `
                <div class="game-card" data-game-id="${game.id}" style="--stagger-index: ${index};">
                    <div class="game-card-icon">${getGameIcon(game.id)}</div>
                    <div class="game-card-title">${t(game.titleKey)}</div>
                    <div class="game-card-info">${t('game_rtp')}: ${game.rtp}</div>
                </div>
            `).join('')}
        </div>
        <div id="play-bar" class="play-bar">
            <button id="play-button" class="btn btn-primary">${t('play_button')}</button>
        </div>
    `;

    addEventListeners();
}

function renderGameListSkeleton() {
    const skeletonCount = 4;
    if (!rootElement) return;
    const t = window.ManiacGames.t; // <-- ИСПРАВЛЕНО: Доступ к t внутри функции
    rootElement.innerHTML = `
        <div class="games-grid">
            ${Array(skeletonCount).fill(0).map((_, index) => `
                <div class="game-card skeleton" style="--stagger-index: ${index}; aspect-ratio: 1 / 1.1;">
                </div>
            `).join('')}
        </div>
         <div id="play-bar" class="play-bar">
            <button id="play-button" class="btn btn-primary">${t('play_button')}</button>
        </div>
    `;
}


function getGameIcon(gameId) {
    // ... (код иконок остаётся без изменений)
    switch (gameId) {
        case 'dice':
            return `<svg width="48" height="48" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg"><g filter="url(#filter0_d_8_2)"><rect x="10" y="10" width="80" height="80" rx="15" fill="url(#paint0_linear_8_2)"/><rect x="11.5" y="11.5" width="77" height="77" rx="13.5" stroke="white" stroke-opacity="0.2" stroke-width="3"/></g><circle cx="30" cy="30" r="8" fill="white"/><circle cx="70" cy="30" r="8" fill="white"/><circle cx="50" cy="50" r="8" fill="white"/><circle cx="30" cy="70" r="8" fill="white"/><circle cx="70" cy="70" r="8" fill="white"/><defs><filter id="filter0_d_8_2" x="0" y="0" width="100" height="100" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0" result="hardAlpha"/><feOffset dy="0"/><feGaussianBlur stdDeviation="5"/><feComposite in2="hardAlpha" operator="out"/><feColorMatrix type="matrix" values="0 0 0 0 0.541667 0 0 0 0 0.4875 0 0 0 0 1 0 0 0 0.3 0"/><feBlend mode="normal" in2="BackgroundImageFix" result="effect1_dropShadow_8_2"/><feBlend mode="normal" in="SourceGraphic" in2="effect1_dropShadow_8_2" result="shape"/></filter><linearGradient id="paint0_linear_8_2" x1="50" y1="10" x2="50" y2="90" gradientUnits="userSpaceOnUse"><stop stop-color="#3A435E"/><stop offset="1" stop-color="#21283C"/></linearGradient></defs></svg>`;
        case 'crash':
            return `<svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 40C8 40 16 40 24 24S40 8 40 8" stroke="url(#paint0_linear_2_28)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/><path d="M28 8H40V20" stroke="url(#paint1_linear_2_28)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/><defs><linearGradient id="paint0_linear_2_28" x1="8" y1="24" x2="40" y2="24" gradientUnits="userSpaceOnUse"><stop stop-color="#8A7CFF"/><stop offset="1" stop-color="#F92B75"/></linearGradient><linearGradient id="paint1_linear_2_28" x1="28" y1="14" x2="40" y2="14" gradientUnits="userSpaceOnUse"><stop stop-color="#8A7CFF"/><stop offset="1" stop-color="#F92B75"/></linearGradient></defs></svg>`;
        case 'slots':
            return `<svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="4" y="8" width="10" height="32" rx="2" stroke="#8A7CFF" stroke-width="2.5"/><rect x="19" y="8" width="10" height="32" rx="2" stroke="#F92B75" stroke-width="2.5"/><rect x="34" y="8" width="10" height="32" rx="2" stroke="#33D6A6" stroke-width="2.5"/></svg>`;
        case 'coin':
            return `<svg width="48" height="48" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg"><g filter="url(#filter0_d_12_2)"><circle cx="50" cy="46" r="40" fill="url(#paint0_linear_12_2)"/><circle cx="50" cy="46" r="38" stroke="url(#paint1_linear_12_2)" stroke-width="4"/></g><path d="M50 33L58.6603 48.5H41.3397L50 33Z" fill="#FFC85C"/><path d="M50 63L58.6603 47.5H41.3397L50 63Z" fill="#FFC85C" fill-opacity="0.6"/><defs><filter id="filter0_d_12_2" x="0" y="0" width="100" height="100" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0" result="hardAlpha"/><feOffset dy="4"/><feGaussianBlur stdDeviation="5"/><feComposite in2="hardAlpha" operator="out"/><feColorMatrix type="matrix" values="0 0 0 0 0.933333 0 0 0 0 0.764706 0 0 0 0 0.352941 0 0 0 0.4 0"/><feBlend mode="normal" in2="BackgroundImageFix" result="effect1_dropShadow_12_2"/><feBlend mode="normal" in="SourceGraphic" in2="effect1_dropShadow_12_2" result="shape"/></filter><linearGradient id="paint0_linear_12_2" x1="50" y1="6" x2="50" y2="86" gradientUnits="userSpaceOnUse"><stop stop-color="#FFD77A"/><stop offset="1" stop-color="#E8A91E"/></linearGradient><linearGradient id="paint1_linear_12_2" x1="50" y1="6" x2="50" y2="86" gradientUnits="userSpaceOnUse"><stop stop-color="white" stop-opacity="0.8"/><stop offset="1" stop-color="white" stop-opacity="0"/></linearGradient></defs></svg>`;
        default:
            return `<svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="10" stroke="#6E7B8A" stroke-width="2" stroke-dasharray="4 4"/><path d="M9.09 9C9.3251 8.33333 10.2911 7.2 12 9C13.7089 10.8 15.2422 10.5 15.5 10" stroke="#6E7B8A" stroke-width="2" stroke-linecap="round"/></svg>`;
    }
}

function addEventListeners() {
    const gameCards = rootElement.querySelectorAll('.game-card');
    const playBar = rootElement.querySelector('#play-bar');
    const playButton = rootElement.querySelector('#play-button');

    gameCards.forEach(card => {
        card.addEventListener('click', () => {
            gameCards.forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedGame = card.dataset.gameId;
            playBar.classList.add('visible');
            window.ManiacGames.hapticFeedback('light');
        });
    });

    playButton.addEventListener('click', () => {
        if (selectedGame) {
            window.ManiacGames.playSound('tap');
            window.ManiacGames.hapticFeedback('medium');
            window.location.hash = `#/game/${selectedGame}`;
        }
    });
}

export function mount(rootEl) {
    rootElement = rootEl;
    // 1. Показываем скелет
    renderGameListSkeleton();

    // 2. Имитируем загрузку данных
    setTimeout(() => {
        // 3. После "загрузки" рендерим настоящий контент
        if (rootElement) {
            render();
        }
    }, 800); // Задержка в 800ms для демонстрации
}

export function unmount() {
    rootElement = null;
    selectedGame = null;
}
