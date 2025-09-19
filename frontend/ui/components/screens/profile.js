import { state } from '../../../core/state.js';
import { bus } from '../../../core/bus.js';

const template = `
<div id="profile-screen" class="screen">
    <div class="profile-container">
        <div class="profile-header">
            <img src="./assets/logo.png" alt="User Avatar" class="avatar">
            <h1 id="username"></h1>
        </div>
        <div class="profile-stats">
            <div class="stat">
                <p>Balance</p>
                <span id="profile-balance">0</span>
            </div>
            <div class="stat">
                <p>Total Earned</p>
                <span id="total-earned">0</span>
            </div>
        </div>
        <div class="profile-actions">
            <button id="logout-button">Logout</button>
        </div>
    </div>
</div>
`;

const updateProfile = () => {
    const usernameElement = document.getElementById('username');
    const balanceElement = document.getElementById('profile-balance');
    const totalEarnedElement = document.getElementById('total-earned');

    if (usernameElement) {
        // Assuming the username is part of the state or user object
        usernameElement.textContent = state.user ? state.user.username : 'Guest';
    }
    if (balanceElement) {
        balanceElement.textContent = Math.floor(state.balance);
    }
    if (totalEarnedElement) {
        // You need to track total earned in the state
        totalEarnedElement.textContent = Math.floor(state.totalEarned || 0);
    }
};

const handleLogout = () => {
    // Implement logout logic
    console.log('User logged out');
    // For example, clear state and redirect to a login screen
    // This part depends on your authentication flow
};

const init = (container) => {
    container.innerHTML = template;
    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', handleLogout);
    }
    updateProfile();
    bus.on('state:updateBalance', updateProfile);
    // You might want another event for total earned updates
};

const cleanup = () => {
    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
        logoutButton.removeEventListener('click', handleLogout);
    }
    bus.off('state:updateBalance', updateProfile);
};

export const profileScreen = {
    id: 'profile',
    init,
    cleanup
};
