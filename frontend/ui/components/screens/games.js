// --- ИЗМЕНЕНО ---
// Весь код обернут в экспортируемую функцию 'init'.
// Теперь main.js сможет ее вызвать, когда нужно будет показать этот экран.

export function init(app) {
    app.innerHTML = `
        <h1>Games</h1>
        <p>Welcome to the games section. Choose a game to play!</p>
    `;
}
