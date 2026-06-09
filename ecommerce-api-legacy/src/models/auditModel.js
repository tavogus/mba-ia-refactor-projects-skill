const { run } = require('../database/db');

const auditModel = {
  log(action) {
    return run(
      "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
      [action]
    );
  },
};

module.exports = auditModel;
