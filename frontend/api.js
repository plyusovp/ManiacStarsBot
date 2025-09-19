// Этот модуль будет отвечать за всю коммуникацию с внешним миром

// Инициализируем Telegram Web App
const tg = window.Telegram.WebApp;

// Функция для получения начальных данных пользователя
export async function fetchInitialData() {
    return new Promise((resolve, reject) => {
        try {
            tg.ready();
            console.log('Telegram WebApp is ready');

            // Здесь можно будет делать запрос к вашему серверу за данными пользователя
            // А пока вернем моковые (тестовые) данные
            const userData = {
                ...tg.initDataUnsafe.user,
                balance: 1000,
                energy: 500,
            };

            resolve(userData);
        } catch (error) {
            console.error("Failed to initialize Telegram WebApp", error);
            reject(error);
        }
    });
}
