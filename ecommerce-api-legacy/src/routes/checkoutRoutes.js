const express = require('express');
const checkoutController = require('../controllers/checkoutController');

const router = express.Router();

router.post('/checkout', async (req, res, next) => {
    const { usr: name, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;

    if (!name || !email || !courseId || !cardNumber) {
        return res.status(400).json({ error: 'Bad Request: campos obrigatórios ausentes' });
    }

    try {
        const result = await checkoutController.checkout({ name, email, password, courseId, cardNumber });
        res.status(200).json({ msg: 'Sucesso', enrollment_id: result.enrollmentId });
    } catch (err) {
        next(err);
    }
});

module.exports = router;
