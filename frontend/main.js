// Ожидаем полной загрузки DOM, прежде чем выполнять скрипт
document.addEventListener('DOMContentLoaded', () => {

    // Получаем объект Telegram Web App
    const tg = window.Telegram.WebApp;

    // --- ИНИЦИАЛИЗАЦИЯ ПРИЛОЖЕНИЯ ---
    // Сообщаем Telegram, что приложение готово к отображению
    tg.ready();

    // --- КОНСТАНТЫ И СОСТОЯНИЕ ---
    const STORAGE_KEY = 'tmaGameState';
    const MAX_ENERGY = 100;
    const ENERGY_REGENERATION_RATE = 0.1; // 1 единица за 10 секунд
    const WITHDRAWAL_FEE_PERCENT = 7;

    // Структура состояния по умолчанию для новых пользователей
    const defaultState = {
        balance: 100000, // Начальный баланс в копейках (1000.00)
        energy: MAX_ENERGY,
        maxEnergy: MAX_ENERGY,
        energyPerSecond: ENERGY_REGENERATION_RATE,
        lastUpdate: Date.now(),
        transactions: []
    };

    // --- ПОЛУЧЕНИЕ ЭЛЕМЕНТОВ DOM ---
    const greetingEl = document.getElementById('greeting');
    const balanceDisplayEl = document.getElementById('balance-display');
    const energyBarEl = document.getElementById('energy-bar');
    const energyDisplayEl = document.getElementById('energy-display');
    const withdrawAmountInputEl = document.getElementById('withdraw-amount-input');
    const withdrawButtonEl = document.getElementById('withdraw-button');
    const transactionListEl = document.getElementById('transaction-list');

    // --- ФУНКЦИИ УПРАВЛЕНИЯ СОСТОЯНИЕМ (State Management) ---

    /**
     * Загружает состояние из localStorage и рассчитывает оффлайн-прогресс.
     * @returns {object} Актуальное состояние приложения.
     */
    function loadState() {
        const savedStateJSON = localStorage.getItem(STORAGE_KEY);

        if (!savedStateJSON) {
            return { ...defaultState, lastUpdate: Date.now() };
        }

        const state = JSON.parse(savedStateJSON);

        // Расчет оффлайн-прогресса энергии
        const now = Date.now();
        const elapsedSeconds = (now - state.lastUpdate) / 1000;
        const regeneratedEnergy = elapsedSeconds * state.energyPerSecond;

        state.energy = Math.min(state.energy + regeneratedEnergy, state.maxEnergy);
        state.lastUpdate = now; // Обновляем время последнего апдейта

        return state;
    }

    /**
     * Сохраняет текущее состояние приложения в localStorage.
     * @param {object} state - Объект состояния для сохранения.
     */
    function saveState(state) {
        state.lastUpdate = Date.now();
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    }

    // --- МОДУЛЬ UI (РЕНДЕРИНГ) ---

    /**
     * Обновляет весь DOM на основе текущего состояния.
     * @param {object} state - Текущее состояние приложения.
     */
    function render(state) {
        // Обновляем приветствие, если есть данные пользователя
        if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
            greetingEl.textContent = `Добро пожаловать, ${tg.initDataUnsafe.user.first_name}!`;
        }

        // Форматируем баланс из копеек в читаемый вид (e.g., 12345 -> "123.45")
        balanceDisplayEl.textContent = (state.balance / 100).toFixed(2);

        // Обновляем шкалу и текст энергии
        energyDisplayEl.textContent = `${Math.floor(state.energy)} / ${state.maxEnergy}`;
        const energyPercentage = (state.energy / state.maxEnergy) * 100;
        energyBarEl.style.width = `${energyPercentage}%`;

        // Очищаем список транзакций перед рендерингом
        transactionListEl.innerHTML = '';

        // Рендерим транзакции в обратном порядке (новые сверху)
        state.transactions.slice().reverse().forEach(tx => {
            const li = document.createElement('li');

            const date = new Date(tx.timestamp).toLocaleString('ru-RU');

            // Преобразуем копейки в рубли для отображения
            const amount = (tx.amount / 100).toFixed(2);
            const commission = (tx.commission / 100).toFixed(2);
            const finalAmount = (tx.finalAmount / 100).toFixed(2);

            li.innerHTML = `
                <div class="tx-info">
                    <strong>Вывод средств</strong>
                    <span>-${amount} (Комиссия: ${commission})</span>
                </div>
                <div class="tx-meta">
                    <span>Итог: ${finalAmount}</span>
                    <span>${date}</span>
                </div>
            `;
            transactionListEl.appendChild(li);
        });
    }

    // --- МОДУЛЬ ФИНАНСОВ ---

    /**
     * Обрабатывает операцию вывода средств.
     * @param {object} state - Текущее состояние приложения.
     */
    function handleWithdrawal(state) {
        const amountStr = withdrawAmountInputEl.value;
        const amountFloat = parseFloat(amountStr);

        // Валидация ввода
        if (isNaN(amountFloat) || amountFloat <= 0) {
            tg.showAlert('Пожалуйста, введите корректную положительную сумму.');
            return;
        }

        // Конвертируем в копейки для безопасных расчетов
        const amountInCents = Math.round(amountFloat * 100);

        if (amountInCents > state.balance) {
            tg.showAlert('Недостаточно средств.');
            return;
        }

        // Расчет комиссии в копейках
        const commission = Math.floor((amountInCents * WITHDRAWAL_FEE_PERCENT) / 100);
        const finalAmount = amountInCents - commission;

        // Обновляем баланс
        state.balance -= amountInCents;

        // Создаем запись о транзакции
        const newTransaction = {
            id: `tx-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            type: 'withdraw',
            amount: amountInCents,
            commission: commission,
            finalAmount: finalAmount,
            timestamp: Date.now()
        };
        state.transactions.push(newTransaction);

        // Сохраняем и обновляем UI
        saveState(state);
        render(state);
        tg.HapticFeedback.notificationOccurred('success');

        // Очищаем поле ввода
        withdrawAmountInputEl.value = '';
    }

    // --- МОДУЛЬ ЭНЕРГИИ ---

    /**
     * Запускает систему регенерации энергии в реальном времени.
     * @param {object} state - Текущее состояние приложения.
     */
    function initEnergySystem(state) {
        setInterval(() => {
            if (state.energy < state.maxEnergy) {
                state.energy += state.energyPerSecond;
                // Ограничиваем сверху, чтобы избежать превышения из-за погрешностей
                state.energy = Math.min(state.energy, state.maxEnergy);
                render(state); // Обновляем UI, чтобы показать регенерацию
            }
        }, 1000);
    }

    // --- ПОСЛЕДОВАТЕЛЬНОСТЬ ИНИЦИАЛИЗАЦИИ ---

    // 1. Загружаем состояние, включая расчет оффлайн-прогресса
    let state = loadState();

    // 2. Привязываем обработчики событий
    withdrawButtonEl.addEventListener('click', () => handleWithdrawal(state));

    // 3. Первоначальная отрисовка интерфейса
    render(state);

    // 4. Запускаем регенерацию энергии
    initEnergySystem(state);
});
