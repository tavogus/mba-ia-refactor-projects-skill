const { get, all } = require('../database/db');

const courseModel = {
  findActiveById(id) {
    return get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
  },

  findAll() {
    return all('SELECT * FROM courses', []);
  },
};

module.exports = courseModel;
