// Импортируем нужные сервисы из твоих модулей
// TODO: Убедись, что пути к файлам правильные
import { bus } from '../../core/bus.js';
import { balance } from '../../core/balance.js';
import { audio } from '../../core/audio.js';
import { getEdge } from '../../core/houseedge.js';
import { rand } from '../../core/rng.js';

// --- Настройки игры ---
const STEPS_COUNT = 10; // Количество ступеней
const CHANCE_TO_WIN_STEP = 0.75; // Шанс пройти ступень (75%)

export function mount(root) {
    // --- 1. Создаём HTML-структуру игры ---
    root.innerHTML = `
        <style>
            /* Стили для игры. Потом можешь перенести их в свой основной CSS */
            .taper-game { display: flex; flex-direction: column; align-items: center; gap: 16px; width: 100%; }
            .taper-controls { display: flex; gap: 12px; }
            .taper-ladder { display: flex; flex-direction: column-reverse; width: 100%; gap: 8px; }
            .taper-step { 
                /* TODO: Используй здесь стили своего компонента Card */
                padding: 12px; border-radius: 12px; background: var(--card); 
                display: flex; justify-content: space-between; font-size: 14px;
                transition: all var(--dur-md) var(--ease-out);
            }
            .taper-step.active { background: var(--accent); color: white; transform: scale(1.05); }
            .taper-step.win { background: var(--success); }
            .taper-step.lose { background: var(--danger); animation: shake 0.5s; }
            @keyframes shake { 0%, 100% { transform: translateX(0); } 25% { transform: translateX(-5px); } 75% { transform: translateX(5px); } }
        </style>

        <div class="taper-game">
            <h2>Лестница (Taper)</h2>
            <div class="taper-ladder" id="taperLadder">
                </div>
            
            <div class="taper-controls">
                <button id="betBtn">Ставка 10</button>
                <button id="nextBtn" disabled>Дальше</button>
                <button id="cashoutBtn" disabled>Забрать</button>
            </div>
            <div id="taperInfo">Сделай ставку, чтобы начать!</div>
        </div>
    `;

    // --- 2. Находим наши HTML-элементы ---
    const ladderEl = document.getElementById('taperLadder');
    const betBtn = document.getElementById('betBtn');
    const nextBtn = document.getElementById('nextBtn');
    const cashoutBtn = document.getElementById('cashoutBtn');
    const infoEl = document.getElementById('taperInfo');
    
    // --- 3. Игровая логика ---
    let isActive = false;
    let currentStep = 0;
    const betAmount = 10; // Для примера, потом можно добавить поле для ввода
    const multipliers = [];

    // Предварительно считаем все множители для лестницы
    function calculateMultipliers() {
        const edge = getEdge('taper'); // Берём преимущество из твоего модуля
        for (let i = 1; i <= STEPS_COUNT; i++) {
            const multiplier = (1 / CHANCE_TO_WIN_STEP) ** i * (1 - edge);
            multipliers.push(multiplier);
        }
    }

    // Рисуем лестницу
    function renderLadder() {
        ladderEl.innerHTML = '';
        multipliers.forEach((mul, index) => {
            ladderEl.innerHTML += `
                <div class="taper-step" id="step-${index + 1}">
                    <span>Шаг ${index + 1}</span>
                    <strong>x${mul.toFixed(2)}</strong>
                </div>
            `;
        });
    }

    // Обновляем UI в зависимости от состояния игры
    function updateUI() {
        // Снимаем все активные классы
        ladderEl.querySelectorAll('.taper-step').forEach(el => {
            el.classList.remove('active', 'win', 'lose');
        });

        if (isActive) {
            betBtn.disabled = true;
            nextBtn.disabled = false;
            cashoutBtn.disabled = currentStep > 0; // Можно забрать после первого шага
            
            const currentMultiplier = multipliers[currentStep - 1].toFixed(2);
            infoEl.textContent = `Текущий выигрыш: ${(betAmount * currentMultiplier).toFixed(0)} ⭐`;

            // Подсвечиваем текущую ступень
            if (currentStep > 0) {
                document.getElementById(`step-${currentStep}`).classList.add('active');
            }
        } else {
            betBtn.disabled = false;
            nextBtn.disabled = true;
            cashoutBtn.disabled = true;
            infoEl.textContent = 'Сделай ставку, чтобы начать!';
        }
    }

    // --- 4. Обработчики событий ---
    betBtn.addEventListener('click', async () => {
        if (!balance.canBet(betAmount)) {
            infoEl.textContent = 'Недостаточно средств!';
            return;
        }
        await balance.commitBet(betAmount);
        bus.publish('balance-changed'); // Уведомляем другие части UI об изменении баланса
        audio.play('tap');

        isActive = true;
        currentStep = 0;
        updateUI();
        infoEl.textContent = 'Ставка сделана! Нажми "Дальше".';
    });

    nextBtn.addEventListener('click', () => {
        audio.play('tap');
        const isWin = rand() < CHANCE_TO_WIN_STEP;

        if (isWin) {
            currentStep++;
            audio.play('win'); // Короткий звук успеха
            updateUI();
            if (currentStep >= STEPS_COUNT) {
                // Автоматически забираем выигрыш на последней ступени
                cashoutBtn.click();
            }
        } else {
            // Проигрыш
            isActive = false;
            audio.play('lose');
            infoEl.textContent = `Проигрыш! Ты упал на ${currentStep + 1} ступени.`;
            document.getElementById(`step-${currentStep + 1}`).classList.add('lose');
            updateUI();
        }
    });
    
    cashoutBtn.addEventListener('click', async () => {
        const payout = betAmount * multipliers[currentStep - 1];
        await balance.applyPayout(payout);
        bus.publish('balance-changed');
        audio.play('bigwin'); // Звук большого выигрыша

        isActive = false;
        document.getElementById(`step-${currentStep}`).classList.add('win');
        infoEl.textContent = `Выигрыш ${payout.toFixed(0)} ⭐ забран!`;
        updateUI();
    });

    // --- 5. Инициализация игры ---
    calculateMultipliers();
    renderLadder();

    // Функция для очистки при уходе с экрана
    const unmount = () => {
        // Здесь можно удалить слушатели событий, если нужно
        console.log('Taper game unmounted');
    };

    return unmount;
}
