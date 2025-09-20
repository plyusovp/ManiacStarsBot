// Импортируем нужные сервисы
// TODO: Убедись, что пути к файлам правильные
import { bus } from '../../../core/bus.js';
// import { balance } from '../../../core/balance.js'; // Предполагаем, что такой файл у тебя будет

// --- Фейковые данные для примера. Потом их нужно будет получать с бэкенда ---
const FAKE_PROFILE_DATA = {
    username: "Maniac",
    level: 12,
    xp: 75, // в процентах
    balance: 12530,
    history: [
        { type: 'Taper Win', delta: '+150', date: 'Сегодня в 14:30' },
        { type: 'Duel Lose', delta: '-50', date: 'Сегодня в 14:28' },
        { type: 'Daily Bonus', delta: '+10', date: 'Вчера в 11:05' },
    ],
    achievements: [
        { id: 'first_tap', name: 'Первый тап', unlocked: true },
        { id: 'sniper', name: 'Снайпер', unlocked: true },
        { id: 'ice_cold', name: 'Хладнокровный', unlocked: false },
        { id: 'jackpot', name: 'Джекпот', unlocked: false },
        { id: 'influencer', name: 'Инфлюенсер', unlocked: true },
        { id: 'tap_king', name: 'Король тапов', unlocked: false },
    ]
};

// Фейковый объект баланса, пока у тебя не готов balance.js
const balance = {
    _value: FAKE_PROFILE_DATA.balance,
    get() { return this._value; },
};

export function mount(root) {
    // --- 1. Создаём HTML-структуру ---
    root.innerHTML = `
        <div class="screen-container profile-screen">
            <div class="profile-header card glass-card">
                <div class="avatar"></div>
                <div class="user-info">
                    <span class="username">${FAKE_PROFILE_DATA.username}</span>
                    <div class="level-bar">
                        <div class="level-progress" style="width: ${FAKE_PROFILE_DATA.xp}%;"></div>
                        <span class="level-text">Уровень ${FAKE_PROFILE_DATA.level}</span>
                    </div>
                </div>
            </div>

            <div class="balance-card card">
                <span class="balance-label">Ваш баланс</span>
                <span class="balance-value">${balance.get().toLocaleString()} ⭐</span>
            </div>

            <div class="profile-actions">
                 <button class="button secondary" id="historyBtn">История</button>
                 <button class="button secondary" id="achievementsBtn">Ачивки</button>
            </div>
            
            <div id="dynamicContent" class="dynamic-content"></div>
        </div>
    `;

    // --- 2. Находим наши HTML-элементы ---
    const historyBtn = document.getElementById('historyBtn');
    const achievementsBtn = document.getElementById('achievementsBtn');
    const dynamicContent = document.getElementById('dynamicContent');

    // --- 3. Функции для отрисовки ---
    
    function renderHistory() {
        dynamicContent.innerHTML = `
            <h3>История операций</h3>
            <div class="history-list">
                ${FAKE_PROFILE_DATA.history.map(item => `
                    <div class="history-item card">
                        <span class="history-type">${item.type}</span>
                        <span class="history-date">${item.date}</span>
                        <span class="history-delta ${item.delta.startsWith('+') ? 'win' : 'lose'}">${item.delta} ⭐</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    function renderAchievements() {
        dynamicContent.innerHTML = `
            <h3>Достижения</h3>
            <div class="achievements-grid">
                ${FAKE_PROFILE_DATA.achievements.map(ach => `
                    <div class="achievement-card card ${ach.unlocked ? 'unlocked' : ''}">
                        <div class="achievement-icon">🏆</div>
                        <span class="achievement-name">${ach.name}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // --- 4. Обработчики событий ---
    historyBtn.addEventListener('click', renderHistory);
    achievementsBtn.addEventListener('click', renderAchievements);

    // По умолчанию показываем историю
    renderHistory(); 

    const unmount = () => {
        console.log('Profile screen unmounted');
    };
    return unmount;
}