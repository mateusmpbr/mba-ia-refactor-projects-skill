# Playbook de Refatoração

Use este documento na **Fase 3** como guia concreto de transformação para cada anti-pattern identificado. Cada padrão mostra o código ANTES (problemático) e DEPOIS (corrigido).

---

## PT-01 — Extrair Configuração Hardcoded para Variáveis de Ambiente

**Anti-pattern alvo:** AP-01 (Hardcoded Credentials)

**ANTES:**
```python
# app.py
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
```

```javascript
// utils.js
const config = {
    dbPass: "senha_super_secreta_prod_123",
    paymentGatewayKey: "pk_live_1234567890abcdef",
    port: 3000
};
```

**DEPOIS:**
```python
# config/settings.py
import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-key")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///app.db")
```

```javascript
// config/settings.js
module.exports = {
    dbPass: process.env.DB_PASS,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    port: process.env.PORT || 3000,
};
```

**Criar `.env.example`:**
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///app.db
PAYMENT_GATEWAY_KEY=pk_test_...
```

---

## PT-02 — Corrigir SQL Injection com Queries Parametrizadas

**Anti-pattern alvo:** AP-02 (SQL Injection)

**ANTES:**
```python
# models.py — concatenação de strings
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute(
    "INSERT INTO usuarios (nome, email, senha) VALUES ('" +
    nome + "', '" + email + "', '" + senha + "')"
)
cursor.execute(
    "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
)
```

**DEPOIS:**
```python
# models/usuario_model.py — parâmetros posicionais com ?
def get_por_id(usuario_id):
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
    return cursor.fetchone()

def criar(nome, email, senha_hash):
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
        (nome, email, senha_hash)
    )

def login(email, senha_hash):
    cursor.execute(
        "SELECT * FROM usuarios WHERE email = ? AND senha = ?",
        (email, senha_hash)
    )
```

**Node.js — ANTES:**
```javascript
db.get("SELECT * FROM users WHERE email = '" + email + "'", callback)
```

**Node.js — DEPOIS:**
```javascript
db.get("SELECT * FROM users WHERE email = ?", [email], callback)
// ou com Promises:
await db.get("SELECT * FROM users WHERE email = ?", [email])
```

---

## PT-03 — Hash de Senhas com Bcrypt

**Anti-pattern alvo:** AP-05 (Weak Cryptography / Plaintext Passwords)

**ANTES:**
```python
# Senha em plaintext
def criar_usuario(nome, email, senha):
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
        (nome, email, senha)  # plaintext!
    )

def login_usuario(email, senha):
    cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
```

**DEPOIS (Python — werkzeug):**
```python
from werkzeug.security import generate_password_hash, check_password_hash

def criar_usuario(nome, email, senha):
    senha_hash = generate_password_hash(senha)
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
        (nome, email, senha_hash)
    )

def login_usuario(email, senha):
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    row = cursor.fetchone()
    if row and check_password_hash(row["senha"], senha):
        return {"id": row["id"], "nome": row["nome"], "email": row["email"]}
    return None
```

**DEPOIS (Node.js — bcryptjs):**
```javascript
const bcrypt = require('bcryptjs');

async function createUser(name, email, password) {
    const hash = await bcrypt.hash(password, 12);
    await db.run("INSERT INTO users (name, email, pass) VALUES (?, ?, ?)", [name, email, hash]);
}

async function verifyPassword(password, hash) {
    return bcrypt.compare(password, hash);
}
```

---

## PT-04 — Extrair Lógica de Negócio para Controller

**Anti-pattern alvo:** AP-06 (Business Logic in Model/Route)

**ANTES:**
```python
# models.py — regra de negócio misturada com acesso a dados
def criar_pedido(usuario_id, itens):
    total = 0
    for item in itens:
        cursor.execute("SELECT * FROM produtos WHERE id = ?", (item["produto_id"],))
        produto = cursor.fetchone()
        if produto is None:
            return {"erro": f"Produto {item['produto_id']} não encontrado"}
        if produto["estoque"] < item["quantidade"]:
            return {"erro": f"Estoque insuficiente para {produto['nome']}"}
        total += produto["preco"] * item["quantidade"]
    # ...insert pedido...
```

**DEPOIS:**
```python
# models/pedido_model.py — apenas acesso a dados
def criar(usuario_id, total):
    cursor.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total)
    )
    db.commit()
    return cursor.lastrowid

def criar_item(pedido_id, produto_id, quantidade, preco_unitario):
    cursor.execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario)
    )

# controllers/pedido_controller.py — regra de negócio aqui
from models import produto_model, pedido_model

def criar_pedido(usuario_id, itens):
    total = 0
    itens_validados = []
    for item in itens:
        produto = produto_model.get_por_id(item["produto_id"])
        if produto is None:
            raise ValueError(f"Produto {item['produto_id']} não encontrado")
        if produto["estoque"] < item["quantidade"]:
            raise ValueError(f"Estoque insuficiente para {produto['nome']}")
        total += produto["preco"] * item["quantidade"]
        itens_validados.append({**item, "preco_unitario": produto["preco"]})

    pedido_id = pedido_model.criar(usuario_id, total)
    for item in itens_validados:
        pedido_model.criar_item(pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"])
        produto_model.decrementar_estoque(item["produto_id"], item["quantidade"])

    return {"pedido_id": pedido_id, "total": total}
```

---

## PT-05 — Refatorar Callback Hell para Async/Await

**Anti-pattern alvo:** AP-07 (Callback Hell)

**ANTES:**
```javascript
// 5 níveis de aninhamento
db.get("SELECT * FROM courses WHERE id = ?", [cid], (err, course) => {
    if (err || !course) return res.status(404).send("Not found");
    db.get("SELECT id FROM users WHERE email = ?", [email], (err, user) => {
        if (err) return res.status(500).send("Erro DB");
        db.run("INSERT INTO enrollments ...", [userId, cid], function(err) {
            db.run("INSERT INTO payments ...", [enrId, amount], function(err) {
                db.run("INSERT INTO audit_logs ...", [], (err) => {
                    res.status(200).json({ msg: "Sucesso" });
                });
            });
        });
    });
});
```

**DEPOIS:**
```javascript
// controllers/checkoutController.js — usando util.promisify ou better-sqlite3
const { promisify } = require('util');

async function processCheckout(db, { email, userName, courseId, cardNumber }) {
    const course = await dbGet(db, "SELECT * FROM courses WHERE id = ? AND active = 1", [courseId]);
    if (!course) throw new Error("Curso não encontrado");

    let user = await dbGet(db, "SELECT id FROM users WHERE email = ?", [email]);
    if (!user) {
        const hash = await bcrypt.hash(password || "change-me", 12);
        const result = await dbRun(db, "INSERT INTO users (name, email, pass) VALUES (?, ?, ?)", [userName, email, hash]);
        user = { id: result.lastID };
    }

    const enrollment = await dbRun(db, "INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)", [user.id, courseId]);
    await dbRun(db, "INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, 'PAID')", [enrollment.lastID, course.price]);
    await dbRun(db, "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [`Checkout curso ${courseId}`]);

    return { enrollmentId: enrollment.lastID };
}
```

---

## PT-06 — Eliminar N+1 Queries com JOIN

**Anti-pattern alvo:** AP-10 (N+1 Query Problem)

**ANTES:**
```python
# Para cada pedido, faz queries separadas para itens e produtos
cursor.execute("SELECT * FROM pedidos")
rows = cursor.fetchall()
for row in rows:
    cursor2 = db.cursor()
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (row["id"],))
    for item in cursor2.fetchall():
        cursor3 = db.cursor()
        cursor3.execute("SELECT nome FROM produtos WHERE id = ?", (item["produto_id"],))
```

**DEPOIS:**
```python
# Uma única query com JOINs
def get_pedidos_com_itens(usuario_id):
    cursor.execute("""
        SELECT
            p.id, p.status, p.total, p.criado_em,
            ip.produto_id, ip.quantidade, ip.preco_unitario,
            pr.nome AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = ip.produto_id
        WHERE p.usuario_id = ?
        ORDER BY p.id
    """, (usuario_id,))

    rows = cursor.fetchall()
    pedidos = {}
    for row in rows:
        pid = row["id"]
        if pid not in pedidos:
            pedidos[pid] = {
                "id": pid, "status": row["status"],
                "total": row["total"], "criado_em": row["criado_em"],
                "itens": []
            }
        if row["produto_id"]:
            pedidos[pid]["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"],
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"]
            })
    return list(pedidos.values())
```

---

## PT-07 — Centralizar Error Handler

**Anti-pattern alvo:** AP-17 (Bare Except / Silent Error Swallowing)

**ANTES:**
```python
# Routes com try/except repetido em cada endpoint
@app.route("/produtos")
def listar():
    try:
        produtos = models.get_todos_produtos()
        return jsonify({"dados": produtos}), 200
    except Exception as e:
        print("ERRO: " + str(e))
        return jsonify({"erro": str(e)}), 500

@app.route("/usuarios")
def listar_usuarios():
    try:
        usuarios = models.get_todos_usuarios()
        return jsonify({"dados": usuarios}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```

**DEPOIS:**
```python
# middlewares/error_handler.py
import logging
from flask import jsonify

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    @app.errorhandler(ValueError)
    def handle_value_error(e):
        return jsonify({"erro": str(e), "sucesso": False}), 400

    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({"erro": "Recurso não encontrado"}), 404

    @app.errorhandler(Exception)
    def handle_generic_error(e):
        logger.exception("Unhandled exception")
        return jsonify({"erro": "Erro interno do servidor"}), 500

# routes/produto_routes.py — sem try/except repetido
@produto_bp.route("/produtos")
def listar_produtos():
    produtos = produto_controller.listar_todos()  # deixa exceções propagarem
    return jsonify({"dados": produtos, "sucesso": True}), 200
```

---

## PT-08 — Remover Sensitive Data da API Response

**Anti-pattern alvo:** AP-11 (Sensitive Data Exposure)

**ANTES:**
```python
# model retorna senha
def get_todos_usuarios():
    result.append({
        "id": row["id"], "nome": row["nome"],
        "email": row["email"], "senha": row["senha"],  # NUNCA retornar!
        "tipo": row["tipo"]
    })
```

**DEPOIS:**
```python
# model tem serializer explícito sem senha
def serialize_usuario(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"]
    }

def get_todos_usuarios():
    cursor.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios")  # sem senha
    return [serialize_usuario(row) for row in cursor.fetchall()]
```

---

## PT-09 — Substituir APIs Deprecated

**Anti-pattern alvo:** AP-13 (Deprecated API Usage)

**ANTES (SQLAlchemy 1.x):**
```python
task = Task.query.get(task_id)       # deprecated em SQLAlchemy 2.0
user = User.query.get(user_id)
```

**DEPOIS (SQLAlchemy 2.0):**
```python
task = db.session.get(Task, task_id)  # correto em SQLAlchemy 2.0
user = db.session.get(User, user_id)
```

**ANTES (Express.js legado):**
```javascript
res.send(404)   // deprecated no Express 4+
```

**DEPOIS:**
```javascript
res.status(404).send("Not found")   // forma correta
res.status(404).json({ error: "Not found" })
```

---

## PT-10 — Extrair Lógica Duplicada

**Anti-pattern alvo:** AP-10 quando relacionado a duplicação de código

**ANTES (cálculo de overdue repetido em 3 arquivos):**
```python
# Em task_routes.py, user_routes.py e report_routes.py — idêntico
if t.due_date:
    if t.due_date < datetime.utcnow():
        if t.status != 'done' and t.status != 'cancelled':
            task_data['overdue'] = True
        else:
            task_data['overdue'] = False
    else:
        task_data['overdue'] = False
else:
    task_data['overdue'] = False
```

**DEPOIS:**
```python
# models/task_model.py — método no próprio model
def is_overdue(self):
    if not self.due_date:
        return False
    if self.status in ('done', 'cancelled'):
        return False
    return self.due_date < datetime.utcnow()

# Nos routes, simplesmente:
task_data['overdue'] = t.is_overdue()
```

---

## PT-11 — Remover Endpoint de Execução Arbitrária de SQL

**Anti-pattern alvo:** AP-03 (Remote Code Execution)

**ANTES:**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    dados = request.get_json()
    query = dados.get("sql", "")
    cursor.execute(query)  # CRÍTICO: executa SQL arbitrário!
```

**DEPOIS:**
```python
# Remover completamente o endpoint /admin/query
# Se necessidade de diagnóstico for legítima:
# - Usar ferramentas de DB com autenticação separada (pgAdmin, SQLite Browser)
# - Criar endpoints específicos com operações predefinidas e autenticadas
```

---

## Regras Gerais do Playbook

1. **Aplique em ordem:** comece por CRITICALs (segurança), depois HIGH (arquitetura), depois MEDIUM/LOW
2. **Preserve a API pública:** todos os endpoints existentes devem continuar respondendo com o mesmo contrato
3. **Um arquivo por responsabilidade:** ao extrair lógica, crie arquivos novos e exclua o código do arquivo original
4. **Adapte ao contexto:** um projeto com SQLAlchemy usa padrões diferentes de raw SQL; respeite o ORM já existente
5. **Valide após cada transformação:** após mover código, confirme que os imports estão corretos e a aplicação ainda sobe
