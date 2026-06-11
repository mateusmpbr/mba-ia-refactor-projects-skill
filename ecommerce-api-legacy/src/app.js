const express = require('express');
const { initDb } = require('./database');
const settings = require('./config/settings');
const checkoutRoutes = require('./routes/checkoutRoutes');
const adminRoutes = require('./routes/adminRoutes');
const userRoutes = require('./routes/userRoutes');
const errorHandler = require('./middlewares/errorHandler');

const app = express();
app.use(express.json());

app.use('/api', checkoutRoutes);
app.use('/api/admin', adminRoutes);
app.use('/api/users', userRoutes);
app.use(errorHandler);

initDb().then(() => {
    app.listen(settings.port, () => {
        console.log(`Frankenstein LMS rodando na porta ${settings.port}...`);
    });
}).catch(err => {
    console.error('Falha ao inicializar banco:', err);
    process.exit(1);
});
