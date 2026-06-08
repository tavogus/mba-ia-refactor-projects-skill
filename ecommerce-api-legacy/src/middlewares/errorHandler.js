/**
 * Centralized error handler middleware.
 * Catches errors thrown or passed via next(err) from any route/controller.
 * Eliminates repetitive try/catch in every handler.
 */
function errorHandler(err, req, res, next) { // eslint-disable-line no-unused-vars
  const status = err.status || err.statusCode || 500;
  const message = err.message || 'Internal Server Error';
  // Log to stderr without leaking sensitive data
  process.stderr.write(`[ERROR] ${req.method} ${req.path} — ${message}\n`);
  res.status(status).json({ error: message });
}

module.exports = errorHandler;
