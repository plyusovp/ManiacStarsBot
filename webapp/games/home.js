import { getStats, fmt, resetLocalData } from '../lib/balance.js';

export const title = 'Дом';

const games = [
    { name: 'Crash', href: '#/crash', icon: '🚀' },
    { name: 'Слоты', href: '#/slots', icon: '🎰' },
    { name: 'Кости 3D', href: '#/dice3d', icon: '🧊' },
    { name: 'Кости 2D', href: '#/dice', icon: '🎲' },
    { name: 'Монетка', href: '#/coin', icon: '🪙' },
    { name: 'Дартс', href: '#/darts', icon: '🎯' },
    { name: 'Баскетбол', href: '#/basketball', icon: '🏀' },
    { name: 'Боулинг', href: '#/bowling', icon: '🎳' },
    { name: 'Футбол', href: '#/football', icon: '⚽' },
    { name: 'Дуэли', href: '#/duels', icon: '⚔️' },
    { name: 'Таймер', href: '#/timer', icon: '⏱️' },
];

let rootElement = null;

function render() {
    const stats = getStats();
    const gameTilesHTML = games.map(game => `
        <a href="${game.href}" class="game-tile">
            <div class="icon">${game.icon}</div>
            <div class="name">${game.name}</div>
        </a>
    `).join('');

    rootElement.innerHTML = `
        <div class="card stats-card">
            <h2>Ваша Статистика</h2>
            <p><strong>Победы/Поражения:</strong> ${fmt(stats.wins)} / ${fmt(stats.losses)}</p>
            <p><strong>Макс. множитель (Crash):</strong> ${stats.maxCrashMultiplier.toFixed(2)}x</p>
            <p><strong>Топ выигрыш:</strong> ${fmt(stats.topWin)} ⭐</p>
            <button id="reset-stats-btn" class="btn btn-danger" style="margin-top: 15px; padding: 8px 10px; font-size: 0.8rem;">Сбросить локальные данные</button>
        </div>

        <div class="card">
            <h2>Игры</h2>
            <div class="games-grid">
                ${gameTilesHTML}
            </div>
        </div>
    `;

    rootElement.querySelector('#reset-stats-btn').addEventListener('click', () => {
        if (confirm('Вы уверены, что хотите сбросить весь прогресс и баланс? Это действие необратимо.')) {
            resetLocalData();
            window.ManiacGames.updateBalance();
            render(); // Re-render to show updated stats
            window.ManiacGames.showNotification('Данные сброшены!', 'success');
        }
    });
}

export function mount(rootEl) {
    rootElement = rootEl;
    render();
}

export function unmount() {
    rootElement = null;
}
