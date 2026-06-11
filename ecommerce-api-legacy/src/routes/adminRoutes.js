const express = require('express');
const authMiddleware = require('../middlewares/authMiddleware');
const reportController = require('../controllers/reportController');

const router = express.Router();

router.use(authMiddleware);

router.get('/financial-report', async (req, res, next) => {
    try {
        const report = await reportController.financialReport();
        res.json(report);
    } catch (err) {
        next(err);
    }
});

module.exports = router;
