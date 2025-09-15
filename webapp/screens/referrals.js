export const titleKey = 'referrals_title';

let rootElement = null;
const t = window.ManiacGames.t;

function handleCopyLink(event) {
    const button = event.currentTarget;
    const refLink = 'https://t.me/maniac_games_bot?start=ref_123456';

    navigator.clipboard.writeText(refLink).then(() => {
        window.ManiacGames.hapticFeedback('success');

        // --- ✨ НОВОЕ: Используем улучшенный эффект конфетти ---
        const rect = button.getBoundingClientRect();
        window.ManiacGames.effects.launchConfetti({
            x: rect.left + rect.width / 2,
            y: rect.top + rect.height / 2
        });

        // Показываем временное сообщение
        const originalContent = button.innerHTML;
        button.innerHTML = `✅ ${t('copied_success')}`;
        setTimeout(() => {
            if (button) button.innerHTML = originalContent;
        }, 2000);

    }).catch(err => {
        console.error('Failed to copy: ', err);
        window.ManiacGames.showNotification(t('copy_failed'), 'error');
    });
}


function handleShare() {
    const refLink = 'https://t.me/maniac_games_bot?start=ref_123456';
    if (navigator.share) {
        navigator.share({
            title: 'Maniac Games',
            text: 'Присоединяйся ко мне в Maniac Games и получай бонусы!',
            url: refLink,
        })
        .then(() => console.log('Successful share'))
        .catch((error) => console.log('Error sharing', error));
    } else {
        window.ManiacGames.showNotification(t('share_not_supported'), 'warning');
    }
}


export function mount(rootEl) {
    rootElement = rootEl;
    rootElement.innerHTML = `
        <div class="card glassmorphism-card">
            <h2>${t('referrals_header')}</h2>
            <p>${t('referrals_desc')}</p>
            <div class="ref-link-container">
                <span class="ref-link-text">t.me/maniac_games...</span>
                <div class="ref-buttons">
                    <button id="copy-ref-link" class="btn-icon" title="${t('copy_button')}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                    </button>
                    <button id="share-ref-link" class="btn-icon" title="${t('share_button')}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>
                    </button>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>${t('referrals_your_referrals')}</h2>
             <div class="friends-list">
                 <div class="friend-item">
                    <span class="friend-avatar">🧑‍🚀</span>
                    <span class="friend-name">Иван Петров</span>
                    <span class="friend-bonus success">+1000 ⭐</span>
                </div>
                 <div class="friend-item">
                     <span class="friend-avatar">🧑‍💻</span>
                    <span class="friend-name">Алена Сидорова</span>
                    <span class="friend-bonus success">+1000 ⭐</span>
                </div>
                 <div class="friend-item">
                     <span class="friend-avatar">🧐</span>
                    <span class="friend-name">Максим Воронов</span>
                    <span class="friend-bonus pending">${t('referrals_in_progress')}</span>
                </div>
             </div>
        </div>
    `;

    const copyBtn = rootElement.querySelector('#copy-ref-link');
    const shareBtn = rootElement.querySelector('#share-ref-link');
    
    copyBtn.addEventListener('click', handleCopyLink);
    shareBtn.addEventListener('click', handleShare);

    // --- ✨ НОВОЕ: Применяем эффекты к кнопкам ---
    window.ManiacGames.effects.applyRippleEffect(copyBtn);
    window.ManiacGames.effects.applyRippleEffect(shareBtn);
    window.ManiacGames.effects.applyMagneticEffect(copyBtn, { distance: 40 });
    window.ManiacGames.effects.applyMagneticEffect(shareBtn, { distance: 40 });
}

export function unmount() {
    rootElement.innerHTML = '';
    rootElement = null;
}

