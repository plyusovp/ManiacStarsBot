import { t } from '../core/i18n.js';
import { playWin, playLose } from '../core/audio.js';

let currentBet = 10;

const template = `
    <div class="game-container">
        <h2>${t('coin_flip_game_title')}</h2>
        <div class="coin-flipper">
            <div id="coin" class="">
                <div class="heads">H</div>
                <div class="tails">T</div>
            </div>
        </div>
        <div class="coin-controls">
             <div class="control-group">
                <label for="coin-bet-amount">${t('bet_amount')}:</label>
                <input type="number" id="coin-bet-amount" value="${currentBet}" min="1">
            </div>
            <div class="control-group">
                <button class="choice-button" data-choice="heads">${t('heads')}</button>
                <button class="choice-button" data-choice="tails">${t('tails')}</button>
            </div>
        </div>
        <div class="coin-result">
            <p id="coin-outcome"></p>
        </div>
    </div>
`;

const handleFlip = (playerChoice) => {
    const coin = document.getElementById('coin');
    const outcomeElement = document.getElementById('coin-outcome');
    const betAmountInput = document.getElementById('coin-bet-amount');

    currentBet = parseInt(betAmountInput.value, 10);

    // Disable buttons during flip
    document.querySelectorAll('.choice-button').forEach(b => b.disabled = true);
    outcomeElement.textContent = '';

    coin.className = ''; // Reset animation classes

    const result = Math.random() < 0.5 ? 'heads' : 'tails';

    // Start animation
    requestAnimationFrame(() => {
        coin.classList.add('flipping');

        setTimeout(() => {
            coin.classList.remove('flipping');
            coin.classList.add(result === 'heads' ? 'is-heads' : 'is-tails');

            if (playerChoice === result) {
                outcomeElement.textContent = `${t('win')}! It was ${t(result)}.`;
                outcomeElement.style.color = 'green';
                playWin();
                // bus.emit('game:win', { game: 'coin', bet: currentBet, payout: currentBet * 2 });
            } else {
                outcomeElement.textContent = `${t('loss')}! It was ${t(result)}.`;
                outcomeElement.style.color = 'red';
                playLose();
                // bus.emit('game:lose', { game: 'coin', bet: currentBet });
            }

            // Re-enable buttons
            document.querySelectorAll('.choice-button').forEach(b => b.disabled = false);

        }, 1000); // Match animation duration
    });
};

const init = (container) => {
    container.innerHTML = template;
    document.querySelectorAll('.choice-button').forEach(button => {
        button.addEventListener('click', (e) => handleFlip(e.target.dataset.choice));
    });
};

const cleanup = () => {
     document.querySelectorAll('.choice-button').forEach(button => {
        button.removeEventListener('click', (e) => handleFlip(e.target.dataset.choice));
    });
};


export const coinGame = {
    id: 'coin',
    init,
    cleanup
};
