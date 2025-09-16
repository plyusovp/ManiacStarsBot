// core/bus.js
// Простая шина событий для связи между модулями (Pub/Sub)
const events = {};

export const bus = {
  /**
   * Подписаться на событие.
   * @param {string} event - Название события.
   * @param {function} callback - Функция-обработчик.
   */
  on(event, callback) {
    if (!events[event]) {
      events[event] = [];
    }
    events[event].push(callback);
  },

  /**
   * Опубликовать событие.
   * @param {string} event - Название события.
   * @param {*} [data] - Данные для передачи в обработчик.
   */
  emit(event, data) {
    if (events[event]) {
      events[event].forEach(callback => callback(data));
    }
  },

  /**
   * Отписаться от события.
   * @param {string} event - Название события.
   * @param {function} callback - Функция-обработчик, которую нужно удалить.
   */
  off(event, callback) {
    if (events[event]) {
      events[event] = events[event].filter(cb => cb !== callback);
    }
  }
};
