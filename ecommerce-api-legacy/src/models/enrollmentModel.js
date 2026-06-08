const { run, all } = require('../database/db');

const enrollmentModel = {
  create(userId, courseId) {
    return run(
      'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
      [userId, courseId]
    );
  },

  findByCourseId(courseId) {
    return all('SELECT * FROM enrollments WHERE course_id = ?', [courseId]);
  },

  deleteByCourseOrUser(userId) {
    return run('DELETE FROM enrollments WHERE user_id = ?', [userId]);
  },
};

module.exports = enrollmentModel;
