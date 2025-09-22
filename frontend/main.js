document.addEventListener('DOMContentLoaded', () => {
    // Инициализация Telegram Web App
    const tg = window.Telegram.WebApp;
    try {
        tg.ready();
        tg.expand();
    } catch (e) {
        console.error("Telegram Web App API not available.", e);
    }

    // --- ОБЩИЕ ЭЛЕМЕНТЫ И СОСТОЯНИЕ ---
    const config = {
        maxEnergy: 200,
        energyPerClick: 1,
        starPerClick: 1,
        energyRegenRate: 1,
        energyRegenInterval: 10000
    };

    let gameState = {
        balance: 0,
        energy: config.maxEnergy,
        lastUpdate: Date.now()
    };

    // --- ЭЛЕМЕНТЫ DOM ---
    const gameScreen = document.getElementById('game-screen');
    const withdrawScreen = document.getElementById('withdraw-screen');
    const goToWithdrawBtn = document.getElementById('go-to-withdraw');
    const backButton = document.querySelector('#withdraw-screen .back-button');
    const notification = document.getElementById('notification');
    const successModal = document.getElementById('success-modal');

    // --- ФУНКЦИИ УПРАВЛЕНИЯ ЭКРАНАМИ ---
    function showScreen(screen) {
        gameScreen.classList.add('hidden');
        withdrawScreen.classList.add('hidden');
        screen.classList.remove('hidden');
    }

    goToWithdrawBtn.addEventListener('click', () => {
        initWithdrawPage(); // Обновляем данные на странице вывода каждый раз при переходе
        showScreen(withdrawScreen);
    });

    backButton.addEventListener('click', () => {
        updateBalanceUI(); // Обновляем баланс на главном экране
        showScreen(gameScreen);
    });

    // --- СОХРАНЕНИЕ / ЗАГРУЗКА ---
    function saveState() {
        localStorage.setItem('maniacClicState', JSON.stringify(gameState));
    }

    function loadState() {
        const savedState = localStorage.getItem('maniacClicState');
        if (savedState) {
            const parsedState = JSON.parse(savedState);
            gameState = { ...gameState, ...parsedState };

            const now = Date.now();
            const elapsedSeconds = Math.floor((now - gameState.lastUpdate) / 1000);
            const intervalsPassed = Math.floor(elapsedSeconds / (config.energyRegenInterval / 1000));

            if (intervalsPassed > 0) {
                const energyToRegen = intervalsPassed * config.energyRegenRate;
                gameState.energy = Math.min(config.maxEnergy, gameState.energy + energyToRegen);
            }
        }
        gameState.lastUpdate = Date.now();
        saveState();
    }

    // --- ИНИЦИАЛИЗАЦИЯ СТРАНИЦ ---

    // Инициализация игрового экрана
    function initGamePage() {
        const balanceCounter = document.getElementById('balance-counter');
        const clickableStar = document.getElementById('clickable-star');
        const energyBar = document.getElementById('energy-bar');
        const energyCounter = document.getElementById('energy-counter');

        loadState();
        updateBalanceUI();
        updateEnergyUI();
        checkEnergy();

        clickableStar.addEventListener('click', (event) => {
            if (gameState.energy >= config.energyPerClick) {
                gameState.energy -= config.energyPerClick;
                gameState.balance += config.starPerClick;

                updateBalanceUI();
                updateEnergyUI();
                playClickAnimations(event.clientX, event.clientY);

                saveState();
            } else {
                showNotification();
            }
            checkEnergy();
        });

        setInterval(() => {
            if (gameState.energy < config.maxEnergy) {
                gameState.energy = Math.min(config.maxEnergy, gameState.energy + config.energyRegenRate);
                gameState.lastUpdate = Date.now();
                updateEnergyUI();
                checkEnergy();
                saveState();
            }
        }, config.energyRegenInterval);

        window.updateBalanceUI = function() {
            balanceCounter.innerText = Math.floor(gameState.balance).toLocaleString('ru-RU');
        }

        function updateEnergyUI() {
            const percentage = (gameState.energy / config.maxEnergy) * 100;
            energyBar.style.width = `${percentage}%`;
            energyCounter.innerText = `${Math.floor(gameState.energy)}/${config.maxEnergy}`;
        }

        function checkEnergy() {
            clickableStar.classList.toggle('disabled', gameState.energy < config.energyPerClick);
        }

        function playClickAnimations(x, y) {
            clickableStar.classList.add('clicked');
            setTimeout(() => clickableStar.classList.remove('clicked'), 100);

            const textAnim = document.createElement('div');
            textAnim.className = 'click-animation-text';
            textAnim.innerText = `+${config.starPerClick}`;
            document.body.appendChild(textAnim);
            textAnim.style.left = `${x - 15}px`;
            textAnim.style.top = `${y - 30}px`;
            setTimeout(() => textAnim.remove(), 1000);

            for (let i = 0; i < 5; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                document.body.appendChild(particle);
                const size = Math.random() * 5 + 2;
                particle.style.width = `${size}px`;
                particle.style.height = `${size}px`;
                particle.style.left = `${x}px`;
                particle.style.top = `${y}px`;
                const angle = Math.random() * 360;
                const distance = Math.random() * 80 + 50;
                const endX = Math.cos(angle * Math.PI / 180) * distance;
                const endY = Math.sin(angle * Math.PI / 180) * distance;
                particle.style.setProperty('--x', `${endX}px`);
                particle.style.setProperty('--y', `${endY}px`);
                setTimeout(() => particle.remove(), 800);
            }
        }
    }

    // Инициализация страницы вывода (вызывается при переходе)
    function initWithdrawPage() {
        const withdrawBalance = document.getElementById('withdraw-balance');
        const slider = document.getElementById('withdraw-slider');
        const calcAmount = document.getElementById('calc-amount');
        const calcCommission = document.getElementById('calc-commission');
        const calcTotal = document.getElementById('calc-total');
        const calcBotStars = document.getElementById('calc-bot-stars');
        const withdrawButton = document.getElementById('withdraw-button');

        const userBalance = Math.floor(gameState.balance);
        withdrawBalance.innerText = userBalance.toLocaleString('ru-RU');

        const maxWithdraw = Math.floor(userBalance / 200) * 200;
        slider.max = maxWithdraw > 0 ? maxWithdraw : 200;
        slider.disabled = userBalance < 200;
        slider.value = 200;

        slider.oninput = updateCalculator;

        function updateCalculator() {
            const amount = parseInt(slider.value);
            const commission = Math.round(amount * 0.07);
            const totalDeducted = amount + commission;
            const botStars = amount / 200;

            calcAmount.innerText = `✨ ${amount.toLocaleString('ru-RU')}`;
            calcCommission.innerText = `✨ ${commission.toLocaleString('ru-RU')}`;
            calcTotal.innerText = `✨ ${totalDeducted.toLocaleString('ru-RU')}`;
            calcBotStars.innerText = `⭐ ${botStars.toLocaleString('ru-RU')}`;
            withdrawButton.disabled = totalDeducted > userBalance;
        }

        withdrawButton.onclick = () => {
            const amount = parseInt(slider.value);
            const commission = Math.round(amount * 0.07);
            const totalDeducted = amount + commission;
            const botStars = amount / 200;

            if (totalDeducted <= userBalance) {
                const jsonData = { action: "withdraw", withdraw_amount: amount, commission_amount: commission, total_deducted: totalDeducted, bot_stars_received: botStars };
                try {
                    tg.sendData(JSON.stringify(jsonData));
                } catch(e) {
                    console.error("Couldn't send data to Telegram", e);
                }

                gameState.balance -= totalDeducted;
                saveState();

                document.getElementById('success-message').innerText = `⭐ ${botStars.toLocaleString('ru-RU')} звёзд зачислены в бота.`;
                successModal.classList.remove('hidden');

                setTimeout(() => {
                    successModal.classList.add('hidden');
                    updateBalanceUI();
                    showScreen(gameScreen);
                }, 3000);
            }
        };
        updateCalculator();
    }

    // --- ОБЩИЕ ФУНКЦИИ И ЗАПУСК ---
    function showNotification() {
        notification.classList.remove('hidden');
        setTimeout(() => notification.classList.add('hidden'), 3000);
    }

    function createBackgroundStars() {
        const container = document.getElementById('background-stars');
        if (!container) return;
        const starCount = 30;
        for (let i = 0; i < starCount; i++) {
            const star = document.createElement('div');
            star.className = 'star';
            const size = Math.random() * 2 + 1;
            star.style.width = `${size}px`;
            star.style.height = `${size}px`;
            const duration = Math.random() * 5 + 5;
            const delay = Math.random() * 5;
            star.style.animationDuration = `${duration}s`;
            star.style.animationDelay = `${delay}s`;
            star.style.setProperty('--start-x', `${Math.random() * 100}vw`);
            star.style.setProperty('--start-y', `${Math.random() * 100}vh`);
            star.style.setProperty('--end-x', `${Math.random() * 100}vw`);
            star.style.setProperty('--end-y', `${Math.random() * 100}vh`);
            container.appendChild(star);
        }
    }

    // Первоначальный запуск
    createBackgroundStars();
    initGamePage();
    showScreen(gameScreen);
});
