/**
 * Generates a random float between min (inclusive) and max (exclusive).
 * @param {number} min - The minimum value.
 * @param {number} max - The maximum value.
 * @returns {number} A random float.
 */
export function randomFloat(min, max) {
    return Math.random() * (max - min) + min;
}

/**
 * Generates a random integer between min (inclusive) and max (inclusive).
 * @param {number} min - The minimum value.
 * @param {number} max - The maximum value.
 * @returns {number} A random integer.
 */
export function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Selects a random item from an array based on weights.
 * Example: weightedRandom({ '🍒': 40, '💎': 1 })
 * @param {object} weights - An object where keys are items and values are their weights.
 * @returns {*} The selected item.
 */
export function weightedRandom(weights) {
    let totalWeight = 0;
    for (const weight of Object.values(weights)) {
        totalWeight += weight;
    }

    let random = Math.random() * totalWeight;
    for (const [item, weight] of Object.entries(weights)) {
        if (random < weight) {
            return item;
        }
        random -= weight;
    }
    // Fallback, should not happen with valid weights
    return Object.keys(weights)[0];
}
