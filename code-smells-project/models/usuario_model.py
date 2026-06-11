from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash


def _serialize(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def get_todos():
    cursor = get_db().cursor()
    cursor.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios")
    return [_serialize(row) for row in cursor.fetchall()]


def get_por_id(usuario_id):
    cursor = get_db().cursor()
    cursor.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?", (usuario_id,))
    row = cursor.fetchone()
    return _serialize(row) if row else None


def criar(nome, email, senha):
    db = get_db()
    cursor = db.cursor()
    senha_hash = generate_password_hash(senha)
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, 'cliente')",
        (nome, email, senha_hash),
    )
    db.commit()
    return cursor.lastrowid


def verificar_login(email, senha):
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    row = cursor.fetchone()
    if row and check_password_hash(row["senha"], senha):
        return _serialize(row)
    return None
