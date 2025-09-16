import { getBalance, fmt } from '../../core/state.js';
import { getUser } from '../../api.js';

export const titleKey = 'profile_title';

let rootElement = null;
let balanceAnimator = null;
const t = window.ManiacGames.t;

// Моковые данные
const user = getUser();
const userLevel = 12;
const userExp = 65; // в процентах
const achievements = [
    { id: 'first_win', name: 'Первая победа', unlocked: true },
    { id: 'big_win', name: 'Крупный выигрыш', unlocked: true },
    { id: 'crasher', name: 'Мастер Crash', unlocked: true },
    { id: 'millionaire', name: 'Миллионер', unlocked: false },
    { id: 'inviter', name: 'Душа компании', unlocked: false },
    { id: 'veteran', name: 'Ветеран', unlocked: false },
];

const history = [
    { typeKey: 'history_crash_win', amount: 5230, date: 'Сегодня, 14:28' },
    { typeKey: 'history_slots_bet', amount: -100, date: 'Сегодня, 14:25' },
    { typeKey: 'history_ref_bonus', amount: 1000, date: 'Вчера, 20:10' },
];


function animateBalance(element, start, end) {
    if (balanceAnimator) cancelAnimationFrame(balanceAnimator);

    let current = start;
    const range = end - start;
    if (range === 0) return;
    const duration = 800;
    let startTime = null;

    function step(timestamp) {
        if (!startTime) startTime = timestamp;
        const progress = Math.min((timestamp - startTime) / duration, 1);
        const easedProgress = 1 - Math.pow(1 - progress, 4); // easeOutQuart

        current = Math.floor(easedProgress * range + start);
        element.textContent = fmt(current);

        if (progress < 1) {
            balanceAnimator = requestAnimationFrame(step);
        } else {
            element.textContent = fmt(end);
        }
    }
    balanceAnimator = requestAnimationFrame(step);
}


function render() {
    rootElement.innerHTML = `
        <div class="profile-header">
            <div class="profile-avatar-wrapper">
                <img src="${user.photo_url || 'https://placehold.co/100x100/111823/EAF2FF?text=' + user.name.charAt(0)}" alt="Аватар" class="profile-avatar">
            </div>
            <h2 class="profile-name">${user.name}</h2>
            <div class="profile-level">
                <span>${t('profile_level')} ${userLevel}</span>
                <div class="progress-bar-sm">
                    <div class="progress-bar-inner-sm" style="width: ${userExp}%;"></div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>${t('profile_balance')}</h2>
            <div class="balance-container">
                <span id="profile-balance" class="balance-value-large">${fmt(getBalance())}</span> <span class="balance-currency">⭐</span>
            </div>
        </div>

        <div class="card">
            <h2>${t('profile_achievements')}</h2>
            <div class="achievements-grid">
                ${achievements.map(ach => `
                    <div class="achievement ${ach.unlocked ? 'unlocked' : ''}" title="${ach.name}">
                        <div class="achievement-icon">${getAchievementIcon(ach.id)}</div>
                    </div>
                `).join('')}
            </div>
        </div>

        <div class="card">
            <h2>${t('profile_history')}</h2>
            <div class="history-list">
                ${history.map(item => `
                    <div class="history-item">
                        <span class="history-type">${t(item.typeKey)}</span>
                        <div class="history-details">
                            <span class="history-amount ${item.amount > 0 ? 'success' : 'danger'}">${item.amount > 0 ? '+' : ''}${fmt(item.amount)} ⭐</span>
                            <span class="history-date">${item.date}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;

    // Демонстрация анимации баланса (убрана для чистоты)
}

function getAchievementIcon(id) {
    switch (id) {
        case 'first_win': return '🏆';
        case 'big_win': return '💰';
        case 'crasher': return '🚀';
        case 'millionaire': return '🤑';
        case 'inviter': return '🤝';
        case 'veteran': return '🛡️';
        default: return '❓';
    }
}


export function mount(rootEl) {
    rootElement = rootEl;
    render();
}

export function unmount() {
    if (balanceAnimator) cancelAnimationFrame(balanceAnimator);
    rootElement = null;
}
