const settings = require('../config/settings');

function authMiddleware(req, res, next) {
    const apiKey = req.headers['x-admin-key'];
    if (!apiKey || apiKey !== settings.adminApiKey) {
        return res.status(401).json({ error: 'Unauthorized' });
    }
    next();
}

module.exports = authMiddleware;
