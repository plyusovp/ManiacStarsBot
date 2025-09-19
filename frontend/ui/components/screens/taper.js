import { state } from '../../../core/state.js';
import { bus } from '../../../core/bus.js';

// HTML-шаблон для экрана
const template = `
<div id="taper-screen" class="screen">
    <div class="taper-container">
        <div class="taper-header">
            <h1 class="balance-label">Your Balance</h1>
            <div class="balance-container">
                <span id="taper-balance">0</span>
            </div>
        </div>
        <div class="taper-circle-container">
            <div id="taper-circle" class="taper-circle">
                <img src="./assets/logo.png" alt="Maniac Stars Logo">
            </div>
        </div>
        <div class="taper-stats">
            <div class="stat">
                <p>Energy</p>
                <div>
                    <span id="taper-energy">1000</span>/<span id="taper-max-energy">1000</span>
                </div>
            </div>
        </div>
        <div id="floating-numbers-container"></div>
    </div>
</div>
`;

let energyInterval = null;

// Функция для обновления отображения баланса
const updateBalance = () => {
    const balanceElement = document.getElementById('taper-balance');
    if (balanceElement) {
        balanceElement.textContent = Math.floor(state.balance);
    }
};

// Функция для обновления отображения энергии
const updateEnergy = () => {
    const energyElement = document.getElementById('taper-energy');
    const maxEnergyElement = document.getElementById('taper-max-energy');
    if (energyElement && maxEnergyElement) {
        energyElement.textContent = state.energy;
        maxEnergyElement.textContent = state.maxEnergy;
    }
};

// Показывает всплывающее число при клике
const showFloatingNumber = (x, y) => {
    const container = document.getElementById('floating-numbers-container');
    if (!container) return;

    const numberElement = document.createElement('div');
    numberElement.className = 'floating-number';
    numberElement.textContent = `+${state.perTap}`;

    // Позиционируем элемент относительно окна
    numberElement.style.left = `${x}px`;
    numberElement.style.top = `${y}px`;

    container.appendChild(numberElement);

    // Анимация и удаление элемента
    requestAnimationFrame(() => {
        numberElement.style.transform = 'translateY(-100px)';
        numberElement.style.opacity = '0';
    });

    setTimeout(() => {
        if (container.contains(numberElement)) {
            container.removeChild(numberElement);
        }
    }, 1000);
};

// Обработчик нажатия на круг
const handleTap = (event) => {
    event.preventDefault(); // Предотвращаем стандартное поведение (например, зум)
    if (state.energy >= state.perTap) {
        state.balance += state.perTap;
        state.energy -= state.perTap;
        updateBalance();
        updateEnergy();

        const clientX = event.touches ? event.touches[0].clientX : event.clientX;
        const clientY = event.touches ? event.touches[0].clientY : event.clientY;

        showFloatingNumber(clientX, clientY);

        // Визуальная обратная связь
        const circle = event.currentTarget;
        circle.style.transform = 'scale(0.95)';
        setTimeout(() => {
            circle.style.transform = 'scale(1)';
        }, 100);
    }
};

// Запускает регенерацию энергии
const startEnergyRegeneration = () => {
    if (energyInterval) {
        clearInterval(energyInterval);
    }
    energyInterval = setInterval(() => {
        if (state.energy < state.maxEnergy) {
            state.energy = Math.min(state.maxEnergy, state.energy + state.energyRegenRate);
            updateEnergy();
        }
    }, 1000);
};

// Инициализация экрана
const init = (container) => {
    container.innerHTML = template;
    const taperCircle = document.getElementById('taper-circle');
    if (taperCircle) {
        taperCircle.addEventListener('click', handleTap);
        taperCircle.addEventListener('touchstart', handleTap, { passive: false });
    }

    updateBalance();
    updateEnergy();

    startEnergyRegeneration();

    bus.on('state:updateBalance', updateBalance);
};

// Очистка при переключении экрана
const cleanup = () => {
    const taperCircle = document.getElementById('taper-circle');
    if (taperCircle) {
        taperCircle.removeEventListener('click', handleTap);
        taperCircle.removeEventListener('touchstart', handleTap);
    }
    if (energyInterval) {
        clearInterval(energyInterval);
        energyInterval = null;
    }
    bus.off('state:updateBalance', updateBalance);
};

// Экспортируем объект экрана, чтобы его можно было импортировать в других файлах
export const taperScreen = {
    id: 'taper',
    init,
    cleanup
};
