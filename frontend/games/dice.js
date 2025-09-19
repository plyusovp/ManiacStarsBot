import { t } from '../core/i18n.js';
import { playWin, playLose } from '../core/audio.js';

let currentBet = 10;
let winChance = 50;

const template = `
    <div class="game-container">
        <h2>${t('dice_game_title')}</h2>
        <div class="dice-controls">
            <div class="control-group">
                <label for="bet-amount">${t('bet_amount')}:</label>
                <input type="number" id="bet-amount" value="${currentBet}" min="1">
            </div>
            <div class="control-group">
                <label for="win-chance">${t('win_chance')} (%):</label>
                <input type="range" id="win-chance" min="1" max="99" value="${winChance}">
                <span id="win-chance-value">${winChance}%</span>
            </div>
            <button id="roll-dice-button">${t('roll_dice')}</button>
        </div>
        <div class="dice-result">
            <p>${t('result')}: <span id="dice-outcome"></span></p>
        </div>
    </div>
`;

const updateWinChanceValue = () => {
    const slider = document.getElementById('win-chance');
    const valueDisplay = document.getElementById('win-chance-value');
    if(slider && valueDisplay) {
        valueDisplay.textContent = `${slider.value}%`;
        winChance = parseInt(slider.value, 10);
    }
};

const handleRollDice = () => {
    const betAmountInput = document.getElementById('bet-amount');
    currentBet = parseInt(betAmountInput.value, 10);

    const outcomeElement = document.getElementById('dice-outcome');
    if (!outcomeElement) return;

    const winningNumber = Math.floor(Math.random() * 100) + 1;
    const isWin = winningNumber <= winChance;

    if (isWin) {
        outcomeElement.textContent = `${t('win')}! You rolled ${winningNumber}.`;
        outcomeElement.style.color = 'green';
        playWin();
        // Here you would update the user's balance
        // bus.emit('game:win', { game: 'dice', bet: currentBet, payout: calculatedPayout });
    } else {
        outcomeElement.textContent = `${t('loss')}! You rolled ${winningNumber}.`;
        outcomeElement.style.color = 'red';
        playLose();
        // Here you would update the user's balance
        // bus.emit('game:lose', { game: 'dice', bet: currentBet });
    }
};


const init = (container) => {
    container.innerHTML = template;
    document.getElementById('win-chance').addEventListener('input', updateWinChanceValue);
    document.getElementById('roll-dice-button').addEventListener('click', handleRollDice);
};

const cleanup = () => {
    const winChanceSlider = document.getElementById('win-chance');
    if (winChanceSlider) {
        winChanceSlider.removeEventListener('input', updateWinChanceValue);
    }

    const rollButton = document.getElementById('roll-dice-button');
    if (rollButton) {
        rollButton.removeEventListener('click', handleRollDice);
    }
};

export const diceGame = {
    id: 'dice',
    init,
    cleanup
};
