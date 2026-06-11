const express = require('express');
const authMiddleware = require('../middlewares/authMiddleware');
const userModel = require('../models/userModel');

const router = express.Router();

router.delete('/:id', authMiddleware, async (req, res, next) => {
    try {
        await userModel.deleteById(req.params.id);
        res.json({ msg: 'Usuário deletado' });
    } catch (err) {
        next(err);
    }
});

module.exports = router;
