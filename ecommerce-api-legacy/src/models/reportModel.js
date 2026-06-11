const { dbAll } = require('../database');

async function getFinancialData() {
    return dbAll(`
        SELECT
            c.title  AS course,
            u.name   AS student,
            p.amount AS paid,
            p.status AS payment_status
        FROM courses c
        LEFT JOIN enrollments e ON e.course_id = c.id
        LEFT JOIN users u       ON u.id = e.user_id
        LEFT JOIN payments p    ON p.enrollment_id = e.id
        ORDER BY c.id
    `);
}

module.exports = { getFinancialData };
