/**
 * Database initialization, schema creation, seeding, and promisified helpers.
 * All DB access goes through the run/get/all helpers — no raw callbacks elsewhere.
 */
const sqlite3 = require('sqlite3');
const settings = require('../config/settings');

const db = new sqlite3.Database(settings.dbPath);

/**
 * Promisified db.run — resolves with { lastID, changes }.
 */
function run(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.run(sql, params, function (err) {
      if (err) return reject(err);
      resolve({ lastID: this.lastID, changes: this.changes });
    });
  });
}

/**
 * Promisified db.get — resolves with the first row or undefined.
 */
function get(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.get(sql, params, (err, row) => {
      if (err) return reject(err);
      resolve(row);
    });
  });
}

/**
 * Promisified db.all — resolves with an array of rows.
 */
function all(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.all(sql, params, (err, rows) => {
      if (err) return reject(err);
      resolve(rows);
    });
  });
}

/**
 * Create schema and seed initial data.
 * Uses db.serialize to guarantee sequential execution at startup.
 */
function initDb() {
  return new Promise((resolve, reject) => {
    db.serialize(() => {
      db.run('PRAGMA foreign_keys = ON');
      db.run('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
      db.run('CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
      db.run('CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
      db.run('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)');
      db.run('CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');

      // Seed data — matches the original boilerplate exactly
      db.run("INSERT INTO users (name, email, pass) VALUES ('Leonan', 'leonan@fullcycle.com.br', '123')");
      db.run("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)");
      db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
      db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')", [], (err) => {
        if (err) return reject(err);
        resolve();
      });
    });
  });
}

module.exports = { run, get, all, initDb };
