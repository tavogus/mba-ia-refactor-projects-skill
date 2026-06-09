/**
 * Payment service — encapsulates payment decision logic.
 * Card numbers starting with "4" are approved (PAID), all others are denied.
 * Never logs card numbers or gateway keys.
 */
const paymentService = {
  /**
   * Determine payment status for a given card number.
   * @param {string} cardNumber
   * @returns {'PAID'|'DENIED'}
   */
  authorize(cardNumber) {
    if (typeof cardNumber === 'string' && cardNumber.startsWith('4')) {
      return 'PAID';
    }
    return 'DENIED';
  },
};

module.exports = paymentService;
