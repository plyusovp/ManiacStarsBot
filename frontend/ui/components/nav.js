const navLinks = [
    { id: 'taper', icon: '👆', text: 'Taper' },
    { id: 'referrals', icon: '🤝', text: 'Referrals' },
    { id: 'games', icon: '🎮', text: 'Games' },
    { id: 'profile', icon: '🧑‍🚀', text: 'Profile' },
];

export const renderNav = (container, currentRoute) => {
    const navHTML = navLinks.map(link => `
        <a href="#${link.id}" class="nav-link ${currentRoute === link.id ? 'active' : ''}">
            <span class="icon">${link.icon}</span>
            <span class="text">${link.text}</span>
        </a>
    `).join('');

    container.innerHTML = `<nav class="main-nav">${navHTML}</nav>`;
};
