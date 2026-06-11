module.exports = {
    port: process.env.PORT || 3000,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    dbUser: process.env.DB_USER,
    dbPass: process.env.DB_PASS,
    smtpUser: process.env.SMTP_USER,
    adminApiKey: process.env.ADMIN_API_KEY || 'change-me-in-production',
};
