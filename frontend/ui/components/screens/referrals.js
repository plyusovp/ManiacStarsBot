import { state } from '../../../core/state.js';
import { showMessageModal } from '../modal.js'; // ИСПРАВЛЕНО: импорт из нового компонента modal.js

const template = (referralLink) => `
    <div class="screen">
        <div class="referral-card">
            <h2>Your Referral Link</h2>
            <p>Share this link with your friends. You'll get a bonus for each friend who joins!</p>
            <div class="referral-link-container">
                <input type="text" value="${referralLink}" readonly id="referral-link-input">
                <button id="copy-referral-link">Copy</button>
            </div>
        </div>
    </div>
`;

const copyLinkToClipboard = () => {
    const input = document.getElementById('referral-link-input');
    if (input && input.value) {
        // execCommand is more reliable in complex environments like iframes
        input.select();
        input.setSelectionRange(0, 99999);
        try {
            document.execCommand('copy');
            showMessageModal('Referral link copied!');
        } catch (err) {
            console.error('Fallback copy failed: ', err);
            showMessageModal('Could not copy link.');
        }
    }
};

const init = (container) => {
    const userId = state.user ? state.user.id : 'your_unique_id';
    const referralLink = `${window.location.origin}${window.location.pathname}?ref=${userId}`;

    container.innerHTML = template(referralLink);

    const copyButton = document.getElementById('copy-referral-link');
    if (copyButton) {
        copyButton.addEventListener('click', copyLinkToClipboard);
    }
};

const cleanup = () => {
    // No complex event listeners to clean up in this version
};

export const referralsScreen = {
    id: 'referrals',
    init,
    cleanup
};
