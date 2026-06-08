/**
 * Routes — thin layer: declare paths, delegate to controllers.
 * No business logic, no SQL, no direct DB access here.
 */
const { Router } = require('express');
const { checkout } = require('../controllers/checkoutController');
const { financialReport } = require('../controllers/reportController');
const { deleteUser } = require('../controllers/userController');

const router = Router();

router.post('/api/checkout', checkout);
router.get('/api/admin/financial-report', financialReport);
router.delete('/api/users/:id', deleteUser);

module.exports = router;
