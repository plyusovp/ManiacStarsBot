import { addBalance } from '../lib/balance.js';

export const title = 'Тапалка';

// --- Game Parameters ---
const MAX_ENERGY = 1000;
const REGEN_RATE_PER_SECOND = 2; // How many energy points regenerate per second
const STARS_PER_TAP = 1;
const ENERGY_KEY = 'mg.tapper.energy';
const LAST_VISIT_KEY = 'mg.tapper.lastvisit';

// --- State ---
let root, elements, state;
let regenInterval = null;

function calculateOfflineRegen() {
    const lastVisit = parseInt(localStorage.getItem(LAST_VISIT_KEY), 10);
    const now = Date.now();
    if (!lastVisit) {
        localStorage.setItem(LAST_VISIT_KEY, now.toString());
        return 0;
    }

    const secondsPassed = Math.floor((now - lastVisit) / 1000);
    localStorage.setItem(LAST_VISIT_KEY, now.toString());

    return secondsPassed * REGEN_RATE_PER_SECOND;
}


function resetState() {
    const savedEnergy = parseInt(localStorage.getItem(ENERGY_KEY), 10);
    const offlineRegen = calculateOfflineRegen();

    let currentEnergy = isNaN(savedEnergy) ? MAX_ENERGY : savedEnergy;
    currentEnergy = Math.min(MAX_ENERGY, currentEnergy + offlineRegen);

    state = {
        energy: currentEnergy,
    };
}

function updateUI() {
    if (!elements) return;
    const energyPercentage = (state.energy / MAX_ENERGY) * 100;
    elements.energyValue.textContent = `${Math.floor(state.energy)} / ${MAX_ENERGY}`;
    elements.energyBarInner.style.width = `${energyPercentage}%`;
}

function handleTap(event) {
    if (state.energy < STARS_PER_TAP) {
        window.ManiacGames.showNotification('Недостаточно энергии!', 'error', 1000);
        return;
    }

    state.energy -= STARS_PER_TAP;
    addBalance(STARS_PER_TAP);

    // Haptic feedback
    window.ManiacGames.hapticFeedback('light');

    // Show floating number animation
    const tapX = event.clientX || event.touches[0].clientX;
    const tapY = event.clientY || event.touches[0].clientY;
    showFloatingText(`+${STARS_PER_TAP}`, tapX, tapY);

    // Animate the star
    elements.tapper.style.transform = 'scale(0.95)';
    setTimeout(() => {
        if(elements && elements.tapper) {
            elements.tapper.style.transform = 'scale(1)';
        }
    }, 100);

    // Update UI immediately for responsiveness
    updateUI();
    window.ManiacGames.updateBalance();
}

function showFloatingText(text, x, y) {
    const floatingText = document.createElement('div');
    floatingText.className = 'floating-text';
    floatingText.textContent = text;
    root.appendChild(floatingText);

    floatingText.style.left = `${x}px`;
    floatingText.style.top = `${y}px`;

    setTimeout(() => {
        floatingText.remove();
    }, 1500);
}


function startEnergyRegen() {
    if (regenInterval) clearInterval(regenInterval);
    regenInterval = setInterval(() => {
        if (state.energy < MAX_ENERGY) {
            state.energy = Math.min(MAX_ENERGY, state.energy + REGEN_RATE_PER_SECOND);
            updateUI();
        }
    }, 1000);
}

function bindEvents() {
    elements.tapper.addEventListener('click', handleTap);
}

export function mount(rootEl) {
    root = rootEl;
    resetState();

    root.innerHTML = `
        <style>
            .tapper-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100%;
                text-align: center;
                user-select: none;
            }
            #tapper-star {
                font-size: 150px;
                cursor: pointer;
                text-shadow: 0 0 15px var(--warning), 0 0 30px var(--warning);
                transition: transform 0.1s ease-out;
                padding: 20px;
            }
            .energy-info {
                margin-top: 20px;
                width: 80%;
            }
            .energy-bar-outer {
                width: 100%;
                height: 20px;
                background: rgba(0,0,0,0.3);
                border-radius: 10px;
                border: 1px solid var(--neon1);
                padding: 2px;
                box-sizing: border-box;
            }
            .energy-bar-inner {
                height: 100%;
                background: linear-gradient(90deg, var(--neon2), var(--neon1));
                border-radius: 8px;
                transition: width 0.2s linear;
            }
            #energy-value {
                margin-bottom: 8px;
                font-weight: 600;
                color: var(--text);
            }
            .floating-text {
                position: fixed;
                font-size: 1.5rem;
                font-weight: bold;
                color: var(--success);
                text-shadow: 0 0 5px #000;
                pointer-events: none;
                animation: float-up 1.5s ease-out forwards;
                transform: translateX(-50%);
            }
            @keyframes float-up {
                from {
                    opacity: 1;
                    transform: translate(-50%, 0);
                }
                to {
                    opacity: 0;
                    transform: translate(-50%, -80px);
                }
            }
        </style>
        <div class="tapper-container">
            <h2>Тапай по звезде!</h2>
            <div id="tapper-star">⭐</div>
            <div class="energy-info">
                <p id="energy-value"></p>
                <div class="energy-bar-outer">
                    <div id="energy-bar-inner"></div>
                </div>
            </div>
        </div>
    `;

    elements = {
        tapper: root.querySelector('#tapper-star'),
        energyValue: root.querySelector('#energy-value'),
        energyBarInner: root.querySelector('#energy-bar-inner'),
    };

    bindEvents();
    updateUI();
    startEnergyRegen();
}

export function unmount() {
    if (regenInterval) clearInterval(regenInterval);
    // Save current energy
    localStorage.setItem(ENERGY_KEY, state.energy.toString());
    localStorage.setItem(LAST_VISIT_KEY, Date.now().toString());

    root = null;
    elements = null;
    state = null;
    regenInterval = null;
}
