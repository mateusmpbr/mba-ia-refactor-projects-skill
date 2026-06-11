# Guidelines de Arquitetura MVC

Use este documento na **Fase 3** para definir a estrutura-alvo do projeto refatorado. O padrão MVC aplicado a APIs REST segue uma variação onde **Views são substituídas por Routes** (roteamento + serialização HTTP).

---

## 1. Estrutura de Diretórios Alvo

### Python / Flask

```
src/
├── config/
│   └── settings.py          # Toda configuração via variáveis de ambiente
├── models/
│   ├── __init__.py
│   ├── produto_model.py     # Entidade + acesso a dados (queries)
│   └── usuario_model.py
├── controllers/
│   ├── __init__.py
│   ├── produto_controller.py  # Lógica de negócio orquestrada
│   └── pedido_controller.py
├── routes/
│   ├── __init__.py
│   ├── produto_routes.py    # Roteamento + serialização HTTP (Blueprint)
│   └── usuario_routes.py
├── middlewares/
│   ├── __init__.py
│   └── error_handler.py     # Tratamento centralizado de erros
└── app.py                   # Composition root: cria o app, registra blueprints
```

### Node.js / Express

```
src/
├── config/
│   └── settings.js          # process.env.VARIABLE com defaults
├── models/
│   ├── userModel.js         # Queries SQL parametrizadas
│   └── courseModel.js
├── controllers/
│   ├── checkoutController.js  # Lógica de negócio
│   └── reportController.js
├── routes/
│   ├── checkoutRoutes.js    # express.Router() com handlers mínimos
│   └── adminRoutes.js
├── middlewares/
│   ├── errorHandler.js      # Express error middleware
│   └── authMiddleware.js
└── app.js                   # createApp() + registrar routers
```

---

## 2. Responsabilidades de Cada Camada

### Config / Settings

**Responsabilidade:** Centralizar toda configuração da aplicação.

**Regras:**
- Ler de variáveis de ambiente: `os.environ.get("SECRET_KEY", "dev-only-key")`
- Nunca ter strings literais de senhas, chaves ou URLs de produção
- Pode ter valores padrão para desenvolvimento (mas nunca para produção)
- Deve ser importado pelas outras camadas, não o contrário

**Exemplo (Python):**
```python
# config/settings.py
import os

SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///app.db")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
```

**Exemplo (Node.js):**
```javascript
// config/settings.js
module.exports = {
    port: process.env.PORT || 3000,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    jwtSecret: process.env.JWT_SECRET,
};
```

---

### Model

**Responsabilidade:** Representar entidades do domínio e abstrair o acesso ao banco de dados.

**Regras:**
- Contém apenas queries SQL ou chamadas ao ORM
- NÃO contém regras de negócio (validações de domínio, cálculos, orquestrações)
- NÃO acessa `request` ou `response`
- Retorna dados puros (dicts, objetos, listas) — nunca respostas HTTP
- Uma classe/módulo por entidade do domínio

**Exemplo (Python — raw SQL):**
```python
# models/produto_model.py
from database import get_db

def get_por_id(produto_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
    return cursor.fetchone()

def criar(nome, descricao, preco, estoque, categoria):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria)
    )
    db.commit()
    return cursor.lastrowid
```

**Exemplo (Python — SQLAlchemy):**
```python
# models/task_model.py
from database import db
from datetime import datetime

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default='pending')

    @classmethod
    def get_by_id(cls, task_id):
        return db.session.get(cls, task_id)  # SQLAlchemy 2.0

    @classmethod
    def get_all(cls):
        return cls.query.all()
```

---

### Controller

**Responsabilidade:** Orquestrar a lógica de negócio, chamar models e retornar dados processados.

**Regras:**
- Recebe dados já validados (provenientes da Route)
- Chama um ou mais Models para buscar/persistir dados
- Aplica regras de negócio: validações de domínio, cálculos, decisões
- Retorna um resultado (dict, objeto, tuple) — nunca um `Response` HTTP diretamente
- NÃO acessa `request` ou `jsonify` diretamente
- Um controller por domínio funcional

**Exemplo (Python):**
```python
# controllers/pedido_controller.py
from models import produto_model, pedido_model

def criar_pedido(usuario_id, itens):
    total = 0
    for item in itens:
        produto = produto_model.get_por_id(item["produto_id"])
        if produto is None:
            raise ValueError(f"Produto {item['produto_id']} não encontrado")
        if produto["estoque"] < item["quantidade"]:
            raise ValueError(f"Estoque insuficiente para {produto['nome']}")
        total += produto["preco"] * item["quantidade"]

    pedido_id = pedido_model.criar(usuario_id, total)
    for item in itens:
        pedido_model.criar_item(pedido_id, item["produto_id"], item["quantidade"])
        produto_model.decrementar_estoque(item["produto_id"], item["quantidade"])

    return {"pedido_id": pedido_id, "total": total}
```

---

### Route (View no contexto de API REST)

**Responsabilidade:** Receber requisições HTTP, validar o formato dos dados de entrada, chamar o controller e serializar a resposta.

**Regras:**
- Contém apenas: parsing do request, validação de formato (campos obrigatórios, tipos), chamada ao controller, serialização da resposta
- NÃO contém regras de negócio
- NÃO contém queries SQL
- Trata erros do controller e os converte em códigos HTTP apropriados
- Retorna sempre `jsonify()` com código de status explícito

**Exemplo (Python):**
```python
# routes/pedido_routes.py
from flask import Blueprint, request, jsonify
from controllers import pedido_controller

pedido_bp = Blueprint("pedidos", __name__)

@pedido_bp.route("/pedidos", methods=["POST"])
def criar_pedido():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        return jsonify({"erro": "usuario_id é obrigatório"}), 400
    if not itens:
        return jsonify({"erro": "itens não pode ser vazio"}), 400

    try:
        resultado = pedido_controller.criar_pedido(usuario_id, itens)
        return jsonify({"dados": resultado, "sucesso": True}), 201
    except ValueError as e:
        return jsonify({"erro": str(e), "sucesso": False}), 400
    except Exception as e:
        return jsonify({"erro": "Erro interno"}), 500
```

---

### Middleware / Error Handler

**Responsabilidade:** Interceptar requisições/respostas para executar lógica transversal: logging, autenticação, tratamento de erros.

**Regras:**
- Error handler centralizado captura exceções não tratadas
- Nunca expor stack traces em produção
- Retornar sempre o mesmo formato de erro

**Exemplo (Python):**
```python
# middlewares/error_handler.py
from flask import jsonify
import logging

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"erro": "Recurso não encontrado"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Erro interno: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500
```

**Exemplo (Node.js):**
```javascript
// middlewares/errorHandler.js
function errorHandler(err, req, res, next) {
    console.error(err.stack);
    res.status(err.status || 500).json({
        error: err.message || 'Internal Server Error'
    });
}
module.exports = errorHandler;
```

---

### Entry Point (app.py / app.js)

**Responsabilidade:** Composition root — cria a aplicação, registra rotas e middlewares, inicia o servidor.

**Regras:**
- Deve ser o arquivo mais simples do projeto
- NÃO contém lógica de negócio
- NÃO contém queries SQL
- Importa e registra rotas/blueprints
- Configura middlewares globais
- Chama `app.run()` ou `app.listen()` apenas no `if __name__ == "__main__":`

**Exemplo (Python):**
```python
# app.py
from flask import Flask
from config.settings import SECRET_KEY, DEBUG
from routes.produto_routes import produto_bp
from routes.usuario_routes import usuario_bp
from routes.pedido_routes import pedido_bp
from middlewares.error_handler import register_error_handlers

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["DEBUG"] = DEBUG

    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(pedido_bp)
    register_error_handlers(app)
    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

---

## 3. Regras de Ouro do MVC em APIs

1. **Uma responsabilidade por camada** — Model não sabe de HTTP; Route não sabe de SQL
2. **Dados sobem, não descem** — Route → Controller → Model (nunca ao contrário)
3. **Config nunca em código** — toda configuração vem de variáveis de ambiente
4. **Erros com contexto** — exceções com tipos específicos, nunca `except:` genérico
5. **Endpoints preservados** — refatoração não muda a API pública
6. **Sem estado global mutável** — injetar dependências em vez de usar globais
