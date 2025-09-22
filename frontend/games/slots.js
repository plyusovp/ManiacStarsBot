// plyusovp/maniacstarsbot/ManiacStarsBot-4df23ef8bd5b8766acddffe6bca30a128458c7a5/frontend/games/slots.js

import { t } from '../core/i18n.js';
import { playWin, playLose } from '../core/audio.js';
import { applyPayout } from '../core/houseedge.js';
import { weightedRandom } from '../core/rng.js';

// --- НАСТРОЙКИ ИГРЫ ---
let currentBet = 10;
let isSpinning = false;

// Настраиваем символы и их "вес" (как часто они выпадают) и выплаты
const SYMBOLS = {
    '🍒': { weight: 25, payout: 5 },  // Вишня
    '🍋': { weight: 20, payout: 8 },  // Лимон
    '🍊': { weight: 15, payout: 12 }, // Апельсин
    '🍉': { weight: 10, payout: 20 }, // Арбуз
    '⭐': { weight: 7, payout: 50 },  // Звезда
    '💎': { weight: 4, payout: 100 }  // Бриллиант
};

// Определяем 5 выигрышных линий (индексы ячеек в сетке 3x3)
const WIN_LINES = [
    [0, 1, 2], // Верхняя горизонталь
    [3, 4, 5], // Средняя горизонталь
    [6, 7, 8], // Нижняя горизонталь
    [0, 4, 8], // Диагональ \
    [2, 4, 6]  // Диагональ /
];

// --- HTML-ШАБЛОН ---
const template = `
    <div class="game-container slots-game">
        <h2 class="game-title">${t('slots_game_title')}</h2>
        <div class="slots-reels-container">
            <div class="slots-line-overlay"></div>
            <div class="reel"></div>
            <div class="reel"></div>
            <div class="reel"></div>
        </div>
        <div class="slots-controls">
            <div class="control-group">
                <label for="slots-bet-amount">${t('bet_amount')}:</label>
                <input type="number" id="slots-bet-amount" value="${currentBet}" min="1">
            </div>
            <button id="spin-button">${t('slots_spin')}</button>
        </div>
        <div class="slots-result">
            <p id="slots-outcome"></p>
        </div>
    </div>
`;

// --- ЛОГИКА ИГРЫ ---

/**
 * Запускает анимацию вращения и определяет конечные символы.
 */
const handleSpin = () => {
    if (isSpinning) return;
    isSpinning = true;

    const betAmountInput = document.getElementById('slots-bet-amount');
    currentBet = parseInt(betAmountInput.value, 10);

    const reels = document.querySelectorAll('.reel');
    const outcomeElement = document.getElementById('slots-outcome');
    const spinButton = document.getElementById('spin-button');

    if (spinButton) spinButton.disabled = true;
    if (outcomeElement) outcomeElement.textContent = '';

    let finalResults = [];

    reels.forEach((reel, index) => {
        // Запускаем бесконечную анимацию прокрутки
        reel.style.backgroundPositionY = '0';
        reel.classList.add('spinning');
        
        // Через некоторое время останавливаем каждый барабан
        setTimeout(() => {
            reel.classList.remove('spinning');
            
            const finalReelSymbols = Array.from({ length: 3 }, () => weightedRandom(SYMBOLS));
            finalResults.push(...finalReelSymbols);
            
            // Устанавливаем финальные символы на барабан
            reel.innerHTML = `<div>${finalReelSymbols.join('</div><div>')}</div>`;

            // Если это последний остановившийся барабан
            if (index === reels.length - 1) {
                checkWin(finalResults);
            }
        }, 1000 + index * 300); // Барабаны останавливаются с небольшой задержкой
    });
};

/**
 * Проверяет выигрышные комбинации после остановки барабанов.
 * @param {string[]} results - Массив из 9 символов на поле.
 */
const checkWin = (results) => {
    let totalWin = 0;

    for (const line of WIN_LINES) {
        const [a, b, c] = line;
        if (results[a] === results[b] && results[b] === results[c]) {
            const symbol = results[a];
            totalWin += SYMBOLS[symbol].payout * currentBet;
        }
    }

    const outcomeElement = document.getElementById('slots-outcome');
    const spinButton = document.getElementById('spin-button');

    if (totalWin > 0) {
        const finalPayout = applyPayout(totalWin);
        outcomeElement.textContent = `${t('win_message')}! +${finalPayout.toLocaleString()} ⭐`;
        outcomeElement.style.color = 'var(--green)';
        playWin()
    } else {
        outcomeElement.textContent = `${t('loss_message')}!`;
        outcomeElement.style.color = 'var(--red)';
        playLose()
    }

    if (spinButton) spinButton.disabled = false;
    isSpinning = false;
};

// --- СТАНДАРТНЫЕ ФУНКЦИИ МОДУЛЯ ---

const init = (container) => {
    container.innerHTML = template;
    document.getElementById('spin-button').addEventListener('click', handleSpin);
};

const cleanup = () => {
    const spinButton = document.getElementById('spin-button');
    if (spinButton) {
        spinButton.removeEventListener('click', handleSpin);
    }
};

export const slotsGame = {
    id: 'slots',
    init,
    cleanup
};
