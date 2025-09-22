// plyusovp/maniacstarsbot/ManiacStarsBot-4df23ef8bd5b8766acddffe6bca30a128458c7a5/frontend/games/crash.js

import { t } from '../core/i18n.js';
import { playWin, playLose } from '../core/audio.js';
import { applyPayout } from '../core/houseedge.js'; // Импортируем для расчета комиссии

// --- НАСТРОЙКИ ИГРЫ ---
let currentBet = 10;
let multiplier = 1.0;
let gameState = 'waiting'; // 'waiting', 'running', 'crashed'
let gameLoopInterval = null;

// --- HTML-ШАБЛОН ---
const template = `
    <div class="game-container crash-game">
        <h2 class="game-title">${t('crash_game_title')}</h2>
        <div class="crash-graph">
            <p id="multiplier-display">x1.00</p>
        </div>
        <div class="crash-controls">
            <div class="control-group">
                <label for="crash-bet-amount">${t('bet_amount')}:</label>
                <input type="number" id="crash-bet-amount" value="${currentBet}" min="1">
            </div>
            <button id="crash-button">${t('crash_place_bet')}</button>
        </div>
        <div class="crash-result">
            <p id="crash-outcome"></p>
        </div>
    </div>
`;

// --- ЛОГИКА ИГРЫ ---

/**
 * Рассчитывает точку краша по более честной формуле.
 * @returns {number} Множитель, на котором произойдет краш.
 */
const calculateCrashPoint = () => {
    // Эта формула дает более справедливое распределение результатов,
    // где высокие множители выпадают реже, что делает игру интереснее.
    const e = 2 ** 32;
    const h = Math.floor(Math.random() * e);
    // Устанавливаем house edge для краша в 3% (соответствует applyPayout)
    const houseEdge = 0.97;
    
    // Если выпадает 0, это мгновенный краш на x1.00
    if (h % (1 / (1 - houseEdge)) === 0) {
        return 1.00;
    }

    const crashPoint = Math.floor((100 * e - h) / (e - h)) / 100;
    return Math.max(1.01, crashPoint);
};


const resetGame = () => {
    multiplier = 1.0;
    gameState = 'waiting';
    if(gameLoopInterval) clearInterval(gameLoopInterval);
    
    const multiplierDisplay = document.getElementById('multiplier-display');
    const crashButton = document.getElementById('crash-button');
    const outcomeElement = document.getElementById('crash-outcome');

    if (multiplierDisplay) {
        multiplierDisplay.textContent = `x${multiplier.toFixed(2)}`;
        multiplierDisplay.style.color = 'white';
    }
    if (crashButton) {
        crashButton.textContent = t('crash_place_bet');
        crashButton.disabled = false;
    }
    if(outcomeElement) outcomeElement.textContent = '';
};

const startGameLoop = () => {
    gameState = 'running';
    document.getElementById('crash-button').textContent = t('crash_take');
    
    const crashPoint = calculateCrashPoint();

    gameLoopInterval = setInterval(() => {
        // Замедление роста множителя со временем для драматичности
        const increment = 0.01 + (multiplier / 500);
        multiplier += increment;
        
        const multiplierDisplay = document.getElementById('multiplier-display');
        if (multiplierDisplay) {
            multiplierDisplay.textContent = `x${multiplier.toFixed(2)}`;
        }

        if (multiplier >= crashPoint) {
            clearInterval(gameLoopInterval);
            gameState = 'crashed';
            
            const crashButton = document.getElementById('crash-button');
            const outcomeElement = document.getElementById('crash-outcome');
            
            if (multiplierDisplay) multiplierDisplay.style.color = 'var(--red)';
            if (crashButton) {
                crashButton.textContent = t('crash_crashed');
                crashButton.disabled = true;
            }
            if (outcomeElement) outcomeElement.textContent = `${t('crash_crashed')} x${crashPoint.toFixed(2)}`;
            
            playLose();
            setTimeout(resetGame, 3000);
        }
    }, 100); // Интервал обновления
};

const handleCrashButton = () => {
    if (gameState === 'waiting') {
        const betAmountInput = document.getElementById('crash-bet-amount');
        // ИСПРАВЛЕНО: Убрана опечатка 'betAmount-input'
        currentBet = parseInt(betAmountInput.value, 10);
        startGameLoop();
    } else if (gameState === 'running') {
        clearInterval(gameLoopInterval);
        gameState = 'cashed_out';

        // ИСПРАВЛЕНО: Выигрыш рассчитывается с учетом комиссии
        const winAmount = applyPayout(currentBet * multiplier);
        
        const outcomeElement = document.getElementById('crash-outcome');
        if(outcomeElement) {
             outcomeElement.textContent = `${t('crash_take')} x${multiplier.toFixed(2)}! ${t('win_message')} +${winAmount.toLocaleString()}`;
        }
       
        const crashButton = document.getElementById('crash-button');
        if (crashButton) crashButton.disabled = true;
        
        playWin();
        setTimeout(resetGame, 3000);
    }
};

// --- СТАНДАРТНЫЕ ФУНКЦИИ МОДУЛЯ ---
const init = (container) => {
    container.innerHTML = template;
    resetGame(); // Сбрасываем состояние при инициализации
    document.getElementById('crash-button').addEventListener('click', handleCrashButton);
};

const cleanup = () => {
    if (gameLoopInterval) {
        clearInterval(gameLoopInterval);
    }
    const crashButton = document.getElementById('crash-button');
    if (crashButton) {
        crashButton.removeEventListener('click', handleCrashButton);
    }
};

export const crashGame = {
    id: 'crash',
    init,
    cleanup
};
