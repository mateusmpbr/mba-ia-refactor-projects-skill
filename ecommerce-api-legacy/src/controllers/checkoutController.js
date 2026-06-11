const bcrypt = require('bcryptjs');
const courseModel = require('../models/courseModel');
const userModel = require('../models/userModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditModel = require('../models/auditModel');

async function checkout({ name, email, password, courseId, cardNumber }) {
    const course = await courseModel.findActiveById(courseId);
    if (!course) throw Object.assign(new Error('Curso não encontrado'), { status: 404 });

    let user = await userModel.findByEmail(email);
    if (!user) {
        const passwordHash = await bcrypt.hash(password || 'change-me', 12);
        const userId = await userModel.create(name, email, passwordHash);
        user = { id: userId };
    }

    const paymentStatus = cardNumber.startsWith('4') ? 'PAID' : 'DENIED';
    if (paymentStatus === 'DENIED') {
        throw Object.assign(new Error('Pagamento recusado'), { status: 400 });
    }

    const enrollmentId = await enrollmentModel.create(user.id, courseId);
    await paymentModel.create(enrollmentId, course.price, paymentStatus);
    await auditModel.log(`Checkout curso ${courseId} por ${user.id}`);

    return { enrollmentId };
}

module.exports = { checkout };
