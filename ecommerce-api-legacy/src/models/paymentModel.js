const { run } = require('../database/db');

const paymentModel = {
  create(enrollmentId, amount, status) {
    return run(
      'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
      [enrollmentId, amount, status]
    );
  },

  deleteByEnrollmentIds(enrollmentIds) {
    if (!enrollmentIds || enrollmentIds.length === 0) return Promise.resolve();
    const placeholders = enrollmentIds.map(() => '?').join(', ');
    return run(
      `DELETE FROM payments WHERE enrollment_id IN (${placeholders})`,
      enrollmentIds
    );
  },
};

module.exports = paymentModel;
