// Импортируем нужные сервисы
// TODO: Убедись, что пути к файлам правильные
import { audio } from '../../../core/audio.js';
import { createConfetti } from '../../../core/effects.js';

// --- Фейковые данные для примера. Потом их нужно будет получать с бэкенда ---
const FAKE_REFERRAL_DATA = {
    link: "https://t.me/ManiacStarsBot?start=ref123456",
    invitedCount: 12,
    activeCount: 4,
    earned: 1570,
    lastReferrals: [
        { name: "User1***" },
        { name: "User2***" },
        { name: "User3***" },
    ]
};

export function mount(root) {
    // --- 1. Создаём HTML-структуру ---
    root.innerHTML = `
        <div class="screen-container referrals-screen">
            <h2>Ваши рефералы</h2>
            
            <div class="card glass-card">
                <p>Ваша реферальная ссылка:</p>
                <div class="ref-link-wrapper">
                    <input type="text" id="refLinkInput" value="${FAKE_REFERRAL_DATA.link}" readonly>
                </div>
                <div class="ref-buttons">
                    <button id="copyBtn">Скопировать</button>
                    <button id="shareBtn">Поделиться</button>
                </div>
            </div>

            <div class="ref-stats">
                <div class="card">
                    <span class="stat-value">${FAKE_REFERRAL_DATA.invitedCount}</span>
                    <span class="stat-label">Приглашено</span>
                </div>
                <div class="card">
                    <span class="stat-value">${FAKE_REFERRAL_DATA.activeCount}</span>
                    <span class="stat-label">Активно</span>
                </div>
                <div class="card">
                    <span class="stat-value">${FAKE_REFERRAL_DATA.earned} ⭐</span>
                    <span class="stat-label">Заработано</span>
                </div>
            </div>

            <h3>Последние приглашённые</h3>
            <div class="ref-list">
                ${FAKE_REFERRAL_DATA.lastReferrals.map(ref => `
                    <div class="card">${ref.name}</div>
                `).join('')}
            </div>
        </div>
    `;

    // --- 2. Находим наши HTML-элементы ---
    const copyBtn = document.getElementById('copyBtn');
    const shareBtn = document.getElementById('shareBtn');
    const refLinkInput = document.getElementById('refLinkInput');

    // --- 3. Обработчики событий ---
    
    // Кнопка "Скопировать"
    copyBtn.addEventListener('click', () => {
        refLinkInput.select();
        document.execCommand('copy');
        audio.play('tap');
        
        // Показываем анимацию конфетти и уведомление
        createConfetti(copyBtn); 
        // TODO: Добавить вызов твоего компонента Toast (уведомление)
        alert('Ссылка скопирована!'); 
    });

    // Кнопка "Поделиться"
    shareBtn.addEventListener('click', () => {
        audio.play('tap');
        if (navigator.share) {
            navigator.share({
                title: 'Присоединяйся к Maniac Stars!',
                text: 'Играй со мной и зарабатывай звёзды!',
                url: FAKE_REFERRAL_DATA.link,
            });
        } else {
            // Если navigator.share не поддерживается, просто копируем
            copyBtn.click();
        }
    });

    const unmount = () => {
        console.log('Referrals screen unmounted');
    };

    return unmount;
}
