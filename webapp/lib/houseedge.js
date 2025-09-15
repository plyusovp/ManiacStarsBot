/**
 * The global house edge multiplier.
 * 1.00 = 0% edge (payouts are exactly as calculated)
 * 0.99 = 1% edge (payouts are 99% of calculated value)
 * 0.95 = 5% edge (payouts are 95% of calculated value)
 * This is the primary parameter for adjusting the casino's overall profitability.
 */
export const HOUSE_EDGE = 1.00;

/**
 * Applies the house edge to a calculated payout.
 * Always rounds down to the nearest integer to favor the house.
 * @param {number} payout - The theoretical payout before applying the edge.
 * @returns {number} The final payout amount after applying the house edge.
 */
export function applyPayout(payout) {
    if (payout <= 0) return 0;
    return Math.floor(payout * HOUSE_EDGE);
}
