/**
 * Checkout controller — orchestrates the enrollment use case.
 *
 * Flow:
 *  1. Validate required fields
 *  2. Verify course exists and is active
 *  3. Find or create user
 *  4. Authorize payment (no card number logged)
 *  5. Atomically: create enrollment → payment → audit log (BEGIN/COMMIT/ROLLBACK)
 */
const courseModel = require('../models/courseModel');
const userModel = require('../models/userModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditModel = require('../models/auditModel');
const paymentService = require('../services/paymentService');
const cacheService = require('../services/cacheService');
const { run } = require('../database/db');

async function checkout(req, res, next) {
  try {
    const { usr: name, eml: email, pwd: password, c_id: courseId, card } = req.body;

    // 1. Validate required fields
    if (!name || !email || !courseId || !card) {
      return res.status(400).json({ error: 'Bad Request' });
    }

    // 2. Verify course
    const course = await courseModel.findActiveById(courseId);
    if (!course) {
      return res.status(404).json({ error: 'Curso não encontrado' });
    }

    // 3. Find or create user
    let user = await userModel.findByEmail(email);
    if (!user) {
      const result = await userModel.create(name, email, password);
      user = { id: result.lastID };
    }

    // 4. Authorize payment — card number is NEVER logged
    const status = paymentService.authorize(card);
    if (status === 'DENIED') {
      return res.status(400).json({ error: 'Pagamento recusado' });
    }

    // 5. Atomic transaction: enrollment → payment → audit
    await run('BEGIN');
    try {
      const enrResult = await enrollmentModel.create(user.id, courseId);
      const enrollmentId = enrResult.lastID;

      await paymentModel.create(enrollmentId, course.price, status);
      await auditModel.log(`Checkout curso ${courseId} por ${user.id}`);
      await run('COMMIT');

      cacheService.set(`last_checkout_${user.id}`, course.title);

      return res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    } catch (txErr) {
      await run('ROLLBACK');
      throw txErr;
    }
  } catch (err) {
    next(err);
  }
}

module.exports = { checkout };
