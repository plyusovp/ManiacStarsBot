import { t } from '../core/i18n.js';
import { playWin, playLose } from '../core/audio.js';
import { applyPayout } from '../core/houseedge.js'; // Добавляем импорт для расчета комиссии

// --- НАСТРОЙКИ ИГРЫ ---
let currentBet = 10;
let winChance = 50;

// --- HTML-ШАБЛОН (остается твой, но с правильными ключами для перевода) ---
const template = `
    <div class="game-container">
        <h2>${t('dice_game_title')}</h2>
        <div class="dice-controls">
            <div class="control-group">
                <label for="bet-amount">${t('bet_amount')}:</label>
                <input type="number" id="bet-amount" value="${currentBet}" min="1">
            </div>
            <div class="control-group">
                <label>${t('win_chance')} (%): <span id="win-chance-value">${winChance}%</span></label>
                <input type="range" id="win-chance-slider" min="1" max="95" value="${winChance}">
            </div>
            <button id="roll-dice-button">${t('roll_dice')}</button>
        </div>
        <div class="dice-result">
            <p>${t('result')}: <span id="dice-outcome"></span></p>
        </div>
    </div>
`;

// --- ЛОГИКА ИГРЫ ---

/**
 * Эта функция будет обновлять текст с шансом выигрыша при движении ползунка.
 */
const updateWinChanceValue = () => {
    const slider = document.getElementById('win-chance-slider');
    const valueDisplay = document.getElementById('win-chance-value');
    if (slider && valueDisplay) {
        winChance = parseInt(slider.value, 10);
        valueDisplay.textContent = `${winChance}%`;
    }
};

/**
 * Эта функция будет выполняться при нажатии на кнопку "Roll Dice".
 */
const handleRollDice = () => {
    const betAmountInput = document.getElementById('bet-amount');
    currentBet = parseInt(betAmountInput.value, 10);

    const outcomeElement = document.getElementById('dice-outcome');
    if (!outcomeElement) return;

    // Генерируем случайное число от 1 до 100
    const rolledNumber = Math.floor(Math.random() * 100) + 1;
    const isWin = rolledNumber <= winChance;

if (isWin) {
        // Рассчитываем выигрыш. Формула: (100 / шанс) * ставка
        const payoutMultiplier = 99 / winChance;
        const finalPayout = applyPayout(currentBet * payoutMultiplier);

        // Используем стандартный текст из i18n.json
        outcomeElement.textContent = `${t('win_message')}! +${finalPayout.toLocaleString()} ⭐`;
        outcomeElement.style.color = 'var(--green)';
        playWin()
    } else {
        // Используем стандартный текст из i18n.json
        outcomeElement.textContent = `${t('loss_message')}!`;
        outcomeElement.style.color = 'var(--red)';
        playLose()
    }
}
// --- СТАНДАРТНЫЕ ФУНКЦИИ МОДУЛЯ ---

const init = (container) => {
    container.innerHTML = template;
    document.getElementById('win-chance-slider').addEventListener('input', updateWinChanceValue);
    document.getElementById('roll-dice-button').addEventListener('click', handleRollDice);
};

const cleanup = () => {
    const winChanceSlider = document.getElementById('win-chance-slider');
    if (winChanceSlider) {
        winChanceSlider.removeEventListener('input', updateWinChanceValue);
    }

    const rollButton = document.getElementById('roll-dice-button');
    if (rollButton) {
        rollButton.removeEventListener('click', handleRollDice);
    }
};

// Эти две строки у тебя были написаны правильно, я их не менял.
// Ошибка, которую ты видел, была из-за проблем в коде ВЫШЕ.
export const diceGame = {
    id: 'dice',
    init,
    cleanup
};
