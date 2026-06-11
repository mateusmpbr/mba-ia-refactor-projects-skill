const { dbGet, dbRun } = require('../database');

async function findByEmail(email) {
    return dbGet("SELECT id, name, email FROM users WHERE email = ?", [email]);
}

async function create(name, email, passwordHash) {
    const result = await dbRun(
        "INSERT INTO users (name, email, pass) VALUES (?, ?, ?)",
        [name, email, passwordHash]
    );
    return result.lastID;
}

async function deleteById(id) {
    return dbRun("DELETE FROM users WHERE id = ?", [id]);
}

module.exports = { findByEmail, create, deleteById };
