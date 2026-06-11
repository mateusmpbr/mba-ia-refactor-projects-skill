const reportModel = require('../models/reportModel');

async function financialReport() {
    const rows = await reportModel.getFinancialData();

    const courseMap = {};
    for (const row of rows) {
        if (!courseMap[row.course]) {
            courseMap[row.course] = { course: row.course, revenue: 0, students: [] };
        }
        if (row.student) {
            courseMap[row.course].students.push({ student: row.student, paid: row.paid || 0 });
            if (row.payment_status === 'PAID') {
                courseMap[row.course].revenue += row.paid;
            }
        }
    }

    return Object.values(courseMap);
}

module.exports = { financialReport };
