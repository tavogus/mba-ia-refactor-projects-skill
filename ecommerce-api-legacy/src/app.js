/**
 * Entry point / composition root.
 * Loads config, initializes DB, wires routes and error handler, starts server.
 */
const express = require('express');
const settings = require('./config/settings');
const { initDb } = require('./database/db');
const router = require('./routes/index');
const errorHandler = require('./middlewares/errorHandler');

const app = express();
app.use(express.json());

// Register routes
app.use(router);

// Centralized error handler (must be last middleware)
app.use(errorHandler);

// Initialize DB then start server
initDb()
  .then(() => {
    app.listen(settings.port, () => {
      process.stdout.write(`Frankenstein LMS rodando na porta ${settings.port}...\n`);
    });
  })
  .catch((err) => {
    process.stderr.write(`Failed to initialize DB: ${err.message}\n`);
    process.exit(1);
  });

module.exports = app;
