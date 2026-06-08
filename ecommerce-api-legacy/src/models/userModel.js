const { run, get } = require('../database/db');
const crypto = require('crypto');

/**
 * Hash a password using scrypt with a random salt.
 * Returns a string in the format "salt:hash" (hex-encoded).
 */
function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(password, salt, 64).toString('hex');
  return `${salt}:${hash}`;
}

const userModel = {
  findByEmail(email) {
    return get('SELECT id, name, email FROM users WHERE email = ?', [email]);
  },

  findById(id) {
    return get('SELECT id, name, email FROM users WHERE id = ?', [id]);
  },

  create(name, email, password) {
    const hashedPassword = hashPassword(password || '123456');
    return run(
      'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
      [name, email, hashedPassword]
    );
  },

  deleteById(id) {
    return run('DELETE FROM users WHERE id = ?', [id]);
  },
};

module.exports = userModel;
