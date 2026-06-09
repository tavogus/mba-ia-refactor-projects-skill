/**
 * User controller — handles user deletion with cascade cleanup.
 * Deletes dependent payments and enrollments in a single transaction
 * before deleting the user — no orphaned records left behind.
 */
const userModel = require('../models/userModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const { run, all } = require('../database/db');

async function deleteUser(req, res, next) {
  try {
    const userId = parseInt(req.params.id, 10);

    // Find all enrollments belonging to the user (needed to cascade payments)
    const enrollments = await all(
      'SELECT id FROM enrollments WHERE user_id = ?',
      [userId]
    );
    const enrollmentIds = enrollments.map((e) => e.id);

    await run('BEGIN');
    try {
      // Delete payments linked to those enrollments
      await paymentModel.deleteByEnrollmentIds(enrollmentIds);
      // Delete enrollments
      await enrollmentModel.deleteByCourseOrUser(userId);
      // Delete the user
      await userModel.deleteById(userId);
      await run('COMMIT');
    } catch (txErr) {
      await run('ROLLBACK');
      throw txErr;
    }

    return res.status(200).json({ msg: 'Usuário e registros dependentes deletados com sucesso.' });
  } catch (err) {
    next(err);
  }
}

module.exports = { deleteUser };
