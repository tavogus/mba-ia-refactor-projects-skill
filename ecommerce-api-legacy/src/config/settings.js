/**
 * Centralized configuration — all secrets read from environment variables.
 * Never hardcode credentials here. See .env.example for required variables.
 */
const settings = {
  port: parseInt(process.env.PORT, 10) || 3000,
  dbPath: process.env.DB_PATH || ':memory:',
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
  smtpUser: process.env.SMTP_USER || '',
  dbUser: process.env.DB_USER || '',
  dbPass: process.env.DB_PASS || '',
};

module.exports = settings;
