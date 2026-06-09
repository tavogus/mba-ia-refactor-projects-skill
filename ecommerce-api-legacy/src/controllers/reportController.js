/**
 * Report controller — financial report via a single JOIN query.
 * Eliminates N+1 queries and manual counter coordination.
 */
const { all } = require('../database/db');

async function financialReport(req, res, next) {
  try {
    // Single JOIN query: courses → enrollments → users + payments
    const rows = await all(`
      SELECT
        c.id AS course_id,
        c.title AS course,
        u.name AS student,
        p.amount AS paid,
        p.status AS payment_status
      FROM courses c
      LEFT JOIN enrollments e ON e.course_id = c.id
      LEFT JOIN users u ON u.id = e.user_id
      LEFT JOIN payments p ON p.enrollment_id = e.id
      ORDER BY c.id
    `, []);

    // Aggregate in memory, grouped by course
    const courseMap = new Map();

    for (const row of rows) {
      if (!courseMap.has(row.course_id)) {
        courseMap.set(row.course_id, { course: row.course, revenue: 0, students: [] });
      }
      const entry = courseMap.get(row.course_id);

      // Only include students who actually enrolled (LEFT JOIN may produce null rows)
      if (row.student !== null) {
        if (row.payment_status === 'PAID') {
          entry.revenue += row.paid;
        }
        entry.students.push({
          student: row.student || 'Unknown',
          paid: row.paid || 0,
        });
      }
    }

    return res.status(200).json(Array.from(courseMap.values()));
  } catch (err) {
    next(err);
  }
}

module.exports = { financialReport };
