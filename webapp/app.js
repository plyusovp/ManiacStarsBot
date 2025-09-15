import * as home from './games/home.js';
import * as crash from './games/crash.js';
import * as slots from './games/slots.js';
import * as dice3d from './games/dice3d.js';
import * as dice from './games/dice.js';
import * as coin from './games/coin.js';
import * as darts from './games/darts.js';
import * as basketball from './games/basketball.js';
import * as bowling from './games/bowling.js';
import * as football from './games/football.js';
import * as duels from './games/duels.js';
import * as timer from './games/timer.js';

import { getBalance, fmt } from './lib/balance.js';
import { playSound, hapticFeedback } from './lib/utils.js';

const routes = {
    '/home': home,
    '/crash': crash,
    '/slots': slots,
    '/dice3d': dice3d,
    '/dice': dice,
    '/coin': coin,
    '/darts': darts,
    '/basketball': basketball,
    '/bowling': bowling,
    '/football': football,
    '/duels': duels,
    '/timer': timer,
};

let currentView = null;
let tg;

// --- DOM Elements ---
const DOMElements = {
    app: document.getElementById('app'),
    splash: document.getElementById('splash-screen'),
    headerTitle: document.getElementById('header-title'),
    balanceValue: document.getElementById('balance-value'),
    mainContent: document.getElementById('main-content'),
    navLinks: document.querySelectorAll('.nav-item'),
    notificationBox: document.getElementById('notification-box'),
};

/**
 * Updates the balance display in the header.
 */
const updateBalanceDisplay = () => {
    DOMElements.balanceValue.textContent = fmt(getBalance());
};

/**
 * Shows a temporary notification message.
 * @param {string} message - The message to display.
 * @param {string} type - 'success', 'error', or 'info'.
 * @param {number} duration - How long to show the message in ms.
 */
const showNotification = (message, type = 'info', duration = 3000) => {
    const box = DOMElements.notificationBox;
    box.textContent = message;
    box.className = 'notification-box'; // Reset classes
    box.classList.add('show', type);

    setTimeout(() => {
        box.classList.remove('show');
    }, duration);
};

/**
 * Main router function. Handles view transitions.
 */
const router = async () => {
    const path = window.location.hash.slice(1) || '/home';
    const module = routes[path] || routes['/home'];

    // Unmount the old view
    if (currentView && currentView.module.unmount) {
        // Animate out
        const oldViewEl = currentView.element;
        oldViewEl.classList.add('view-leave');
        setTimeout(() => oldViewEl.remove(), 300);
    }

    // Create and mount the new view
    const viewContainer = document.createElement('div');
    viewContainer.className = `view ${path.substring(1)}-view`; // e.g., view crash-view

    // Add a slight delay to allow the old view to start animating out
    setTimeout(() => {
        DOMElements.mainContent.appendChild(viewContainer);
        module.mount(viewContainer);
    }, 50);

    currentView = { module, element: viewContainer };

    // Update UI elements
    DOMElements.headerTitle.textContent = module.title || 'Maniac Games';
    DOMElements.navLinks.forEach(link => {
        link.classList.toggle('active', link.dataset.route === path);
    });
};

/**
 * Binds all initial event listeners.
 */
const bindEventListeners = () => {
    window.addEventListener('hashchange', router);
    window.addEventListener('popstate', router); // For browser back/forward

    // Handle navigation clicks to prevent full page reloads
    DOMElements.navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const path = link.getAttribute('href');
            if (window.location.hash !== path) {
                window.location.hash = path;
                playSound('click');
                hapticFeedback('light');
            }
        });
    });

     // Dev button: long press on logo to simulate rounds
    const logo = document.querySelector('.splash-logo');
    let pressTimer;
    if(logo) {
        logo.addEventListener('mousedown', () => {
            pressTimer = window.setTimeout(() => {
                console.log("--- DEV: Simulating 10,000 rounds ---");
                if (crash.simulateRTP) {
                    const rtp = crash.simulateRTP(10000);
                    console.log(`Crash RTP: ${rtp}%`);
                    showNotification(`Crash RTP (10k rounds): ${rtp}%`, 'info', 5000);
                }
                if (slots.simulateRTP) {
                    const rtp = slots.simulateRTP(10000);
                    console.log(`Slots RTP: ${rtp}%`);
                    showNotification(`Slots RTP (10k rounds): ${rtp}%`, 'info', 5000);
                }
            }, 2000); // 2-second press
        });
        logo.addEventListener('mouseup', () => clearTimeout(pressTimer));
        logo.addEventListener('mouseleave', () => clearTimeout(pressTimer));
    }
};

/**
 * Initializes the entire application.
 */
const init = () => {
    console.log("Maniac Games: Initializing...");

    // 1. Initialize Telegram WebApp
    try {
        tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();
        tg.setHeaderColor('secondary_bg_color');
        tg.setBackgroundColor('#0a0a0f');
        console.log("Telegram WebApp API initialized.");
    } catch (e) {
        console.warn("Telegram WebApp API not found. Running in dev mode.");
    }

    // 2. Hide splash screen after animation
    setTimeout(() => {
        DOMElements.splash.style.opacity = '0';
        DOMElements.app.classList.remove('hidden');
        setTimeout(() => DOMElements.splash.remove(), 500);
    }, 1800);

    // 3. Set up the global object for modules to use
    window.ManiacGames = {
        updateBalance: updateBalanceDisplay,
        showNotification,
        playSound,
        hapticFeedback,
        tg: tg // Expose TG object
    };

    // 4. Initial setup
    updateBalanceDisplay();
    bindEventListeners();
    router(); // Initial route
};

// --- App Start ---
document.addEventListener('DOMContentLoaded', init);
