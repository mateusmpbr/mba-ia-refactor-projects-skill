# Catálogo de Anti-Patterns — Detecção e Classificação

Use este catálogo na **Fase 2** para cruzar o código analisado e identificar problemas. Para cada anti-pattern, estão listados os **sinais de detecção** (o que procurar no código) e a **severidade**.

---

## CRITICAL

### AP-01 — Hardcoded Credentials / Secrets

**Descrição:** Senhas, chaves de API, SECRET_KEY, tokens ou strings de conexão escritos diretamente no código-fonte.

**Sinais de detecção:**
- `SECRET_KEY = "..."` (string literal, não variável de ambiente)
- `password = "senha123"` em classes de serviço
- `paymentGatewayKey: "pk_live_..."` em arquivos de config
- `dbPass: "senha_super_secreta_prod_123"` em código
- Qualquer chave iniciando com `pk_live_`, `sk_live_`, `AKIA` (AWS), `ghp_` (GitHub)
- Variáveis de ambiente definidas como strings literais em vez de `os.environ.get()`

**Impacto:** Exposição de credenciais ao código-fonte e versionamento. Risco de comprometimento de sistemas externos.

**Recomendação:** Mover para variáveis de ambiente (`os.environ.get()` / `process.env.`) e usar `.env` com `python-dotenv` ou `dotenv` (Node.js).

---

### AP-02 — SQL Injection

**Descrição:** Queries SQL construídas por concatenação de strings com dados do usuário, sem parametrização.

**Sinais de detecção (Python):**
```python
# CRÍTICO — concatenação direta
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "'")
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
query += " AND nome LIKE '%" + termo + "%'"
```

**Sinais de detecção (Node.js):**
```javascript
// CRÍTICO — template literal sem sanitização
db.query(`SELECT * FROM users WHERE id = ${userId}`)
db.run("SELECT * FROM users WHERE email = '" + email + "'")
```

**Impacto:** Permite extração, modificação ou destruição completa do banco de dados por um atacante.

**Recomendação:** Usar queries parametrizadas: `cursor.execute("SELECT * FROM t WHERE id = ?", (id,))` ou `db.query("SELECT * FROM t WHERE id = $1", [id])`.

---

### AP-03 — Remote Code Execution / Admin Endpoint Desprotegido

**Descrição:** Endpoint que aceita e executa SQL arbitrário, código, ou comandos do sistema sem autenticação.

**Sinais de detecção:**
- Rota `/admin/query` que recebe `sql` do corpo da request e executa `cursor.execute(query)`
- `eval()` ou `exec()` com input do usuário
- `subprocess.run()` ou `os.system()` com dados da request

**Impacto:** Execução remota de código, destruição total do banco, comprometimento do servidor.

**Recomendação:** Remover o endpoint ou proteger com autenticação forte e lista de operações permitidas.

---

### AP-04 — God Class / God Method

**Descrição:** Uma única classe ou arquivo que acumula responsabilidades de banco de dados, lógica de negócio, roteamento e configuração.

**Sinais de detecção:**
- Arquivo único com > 200 linhas contendo funções de roteamento, queries SQL e regras de negócio
- Classe com métodos `initDb()`, `setupRoutes()` e `processPayment()` no mesmo escopo
- Arquivo `models.py` ou `AppManager.js` com 300+ linhas cobrindo 4+ domínios diferentes

**Impacto:** Impossível testar em isolamento. Qualquer mudança afeta toda a aplicação.

**Recomendação:** Separar em camadas (model, controller, route) por domínio funcional.

---

### AP-05 — Weak Cryptography / Fake Hashing

**Descrição:** Uso de algoritmos de criptografia fracos, implementação caseira de hashing, ou armazenamento de senhas em plaintext.

**Sinais de detecção:**
```javascript
// Fake crypto — não é hashing real
function badCrypto(pwd) {
    hash += Buffer.from(pwd).toString('base64').substring(0, 2)
    return hash.substring(0, 10)
}
```
```python
# Senha em plaintext no banco
cursor.execute("INSERT INTO usuarios ... VALUES ('" + senha + "')")
senha = row["senha"]  # retornado pela API
```

**Impacto:** Senhas recuperáveis ou quebráveis trivialmente. Violação de LGPD/GDPR.

**Recomendação:** Usar `bcrypt`, `argon2` (Python: `werkzeug.security.generate_password_hash`, `bcrypt`) ou `bcryptjs` (Node.js).

---

## HIGH

### AP-06 — Business Logic in Model / Route

**Descrição:** Regras de negócio complexas implementadas dentro de models (acesso a dados) ou diretamente em routes (transporte HTTP), violando a separação de responsabilidades do MVC.

**Sinais de detecção (Model com negócio):**
```python
def criar_pedido(usuario_id, itens):  # model.py
    # Calcula total, valida estoque, cria itens — tudo aqui
    for item in itens:
        cursor.execute("SELECT * FROM produtos WHERE id = ...")
        if produto["estoque"] < item["quantidade"]:
            return {"erro": "Estoque insuficiente"}
        total += produto["preco"] * item["quantidade"]
    # ...
```

**Sinais de detecção (Route com negócio):**
```python
@app.route("/tasks", methods=["POST"])
def create_task():
    # 50+ linhas de validação e lógica de negócio na route
```

**Impacto:** Lógica de negócio não testável, alto acoplamento, difícil manutenção.

**Recomendação:** Mover lógica de negócio para Controllers. Models apenas consultam/persistem dados.

---

### AP-07 — Callback Hell / Pyramid of Doom

**Descrição:** Callbacks profundamente aninhados no Node.js, gerando código difícil de ler e manter.

**Sinais de detecção:**
```javascript
db.get("SELECT ...", [], (err, course) => {
    db.get("SELECT ...", [], (err, user) => {
        db.run("INSERT ...", [], function(err) {
            db.run("INSERT ...", [], function(err) {
                db.run("INSERT ...", [], (err) => {
                    // 5+ níveis de aninhamento
                })
            })
        })
    })
})
```

**Impacto:** Código ilegível, difícil de testar, propenso a erros de tratamento de erro.

**Recomendação:** Refatorar para `async/await` com Promises ou extrair funções nomeadas.

---

### AP-08 — Global Mutable State

**Descrição:** Variáveis de estado mutável no escopo global/módulo, compartilhadas entre requisições.

**Sinais de detecção:**
```javascript
let globalCache = {};    // módulo utils.js
let totalRevenue = 0;    // acumulado entre requests
```
```python
db_connection = None    # global em database.py sem threading safety
```

**Impacto:** Race conditions em ambientes concorrentes; estado imprevisível entre requisições; impossível testar.

**Recomendação:** Usar injeção de dependência, conexões por request (ou pool), e cache explícito com TTL.

---

### AP-09 — Missing Authentication / Fake Token

**Descrição:** Endpoints que deveriam ser autenticados não têm proteção, ou o sistema usa tokens falsos/previsíveis.

**Sinais de detecção:**
```python
return jsonify({
    'token': 'fake-jwt-token-' + str(user.id)  # previsível!
})
```
- Endpoints `/admin/*` sem middleware de autenticação
- Ausência de decorator `@login_required` ou middleware de verificação de JWT

**Impacto:** Qualquer usuário pode acessar recursos protegidos.

**Recomendação:** Implementar JWT real com `PyJWT` / `jsonwebtoken`, ou usar sessões seguras.

---

## MEDIUM

### AP-10 — N+1 Query Problem

**Descrição:** Uma query principal retorna N registros, e então para cada registro é feita uma query adicional — resultando em N+1 queries totais.

**Sinais de detecção:**
```python
cursor.execute("SELECT * FROM pedidos")  # query principal
for row in rows:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in itens:
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```

```javascript
// Para cada curso, busca matrículas; para cada matrícula, busca usuário e pagamento
courses.forEach(c => {
    db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrollments) => {
        enrollments.forEach(enr => {
            db.get("SELECT name FROM users WHERE id = ?", [enr.user_id], ...)
        })
    })
})
```

**Impacto:** Performance degradada exponencialmente com crescimento dos dados.

**Recomendação:** Usar JOINs SQL ou eager loading do ORM. Substituir por uma única query com JOIN.

---

### AP-11 — Sensitive Data Exposure

**Descrição:** Dados sensíveis (senhas, chaves, dados pessoais) expostos em respostas de API, logs ou health checks.

**Sinais de detecção:**
```python
# Senha retornada pela API
return {"id": row["id"], "email": row["email"], "senha": row["senha"]}

# Informação sensível no health check
return jsonify({"secret_key": "minha-chave", "debug": True})

# Log de cartão de crédito
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`)
```

**Impacto:** Exposição de dados privados de usuários e credenciais do sistema.

**Recomendação:** Nunca retornar campos de senha ou tokens em respostas. Usar serializers/DTOs explícitos.

---

### AP-12 — Missing Input Validation

**Descrição:** Dados recebidos do usuário são usados sem validação de tipo, formato ou limites.

**Sinais de detecção:**
- Ausência de verificação de tipo antes de usar parâmetros numéricos
- Ausência de verificação de formato para emails, datas, UUIDs
- `data.get("campo")` sem verificar se é None antes de usar
- Ausência de limite de tamanho para strings recebidas

**Impacto:** Erros 500 imprevisíveis, possibilidade de injeção, dados corrompidos.

**Recomendação:** Validar todos os inputs na camada de controller/route. Usar bibliotecas como `marshmallow`, `pydantic`, `joi`, `zod`.

---

### AP-13 — Deprecated API Usage

**Descrição:** Uso de APIs obsoletas que foram ou serão removidas em versões futuras do framework/biblioteca.

**Sinais de detecção:**

**SQLAlchemy 2.0 (Python):**
```python
# DEPRECATED — não use em SQLAlchemy >= 2.0
Task.query.get(task_id)          # use: db.session.get(Task, task_id)
User.query.get(user_id)          # use: db.session.get(User, user_id)
Task.query.filter_by(...)        # ainda ok, mas preferir select()
```

**Node.js / Express:**
```javascript
// req.param() foi removido no Express 5
req.param('id')    // use: req.params.id
// res.send(status) com número foi removido
res.send(404)      // use: res.status(404).send()
```

**SQLite3 (Node.js):**
```javascript
// sqlite3 callback-style é legado
db.get(sql, params, callback)   // considere usar better-sqlite3 (síncrono) ou sqlite (Promise-based)
```

**Impacto:** Aplicação pode quebrar ao atualizar dependências. Warnings em runtime.

**Recomendação:** Migrar para a API atual documentada. Ver seção de migração da biblioteca.

---

## LOW

### AP-14 — Magic Numbers / Magic Strings

**Descrição:** Números ou strings literais no código sem nomeação que explique seu significado.

**Sinais de detecção:**
```python
if faturamento > 10000:      # O que é 10000? Um limite de desconto?
    desconto = faturamento * 0.1
elif faturamento > 5000:
    desconto = faturamento * 0.05
```
```python
if priority < 1 or priority > 5:   # 1 e 5 são "magic numbers" de prioridade
```

**Impacto:** Código difícil de entender e manter. Números repetidos podem ser alterados em alguns lugares mas esquecidos em outros.

**Recomendação:** Extrair para constantes nomeadas: `DESCONTO_ALTO = 0.10`, `PRIORIDADE_MIN = 1`.

---

### AP-15 — print() como Logging

**Descrição:** Uso de `print()` ou `console.log()` para logging de operações em vez de um sistema de log estruturado.

**Sinais de detecção:**
```python
print("Listando " + str(len(produtos)) + " produtos")
print("ERRO: " + str(e))
print("ENVIANDO EMAIL: Pedido " + str(id) + " criado")
```
```javascript
console.log(`Processando cartão ${cc}`)
```

**Impacto:** Sem níveis de log, sem formatação estruturada, impossível filtrar por severidade em produção. Pode expor dados sensíveis nos logs.

**Recomendação:** Usar `logging` do Python com níveis (`INFO`, `WARNING`, `ERROR`) ou `winston`/`pino` no Node.js.

---

### AP-16 — Poor Variable Naming / Readability

**Descrição:** Nomes de variáveis muito curtos, não descritivos ou que usam abreviações obscuras.

**Sinais de detecção:**
```javascript
let u = req.body.usr;   // u? usr? → use: userName
let e = req.body.eml;   // → use: email
let p = req.body.pwd;   // → use: password
let cid = req.body.c_id; // → use: courseId
let cc = req.body.card;  // → use: cardNumber
```

**Impacto:** Código difícil de revisar e manter. Aumenta o tempo para entender o fluxo.

**Recomendação:** Usar nomes descritivos que expressem a intenção da variável.

---

### AP-17 — Bare Except / Silent Error Swallowing

**Descrição:** Captura de exceções genéricas sem tipo, ocultando a causa real do erro.

**Sinais de detecção:**
```python
except:                          # captura tudo, inclusive KeyboardInterrupt
    return jsonify({'error': 'Erro interno'}), 500

try:
    db.session.commit()
except:                          # qual erro? impossível saber
    db.session.rollback()
```

**Impacto:** Impossível diagnosticar erros em produção. Pode mascarar bugs críticos.

**Recomendação:** Sempre especificar o tipo de exceção: `except Exception as e:` e logar `str(e)`.

---

### AP-18 — Unused Imports

**Descrição:** Imports declarados mas nunca utilizados no arquivo.

**Sinais de detecção:**
```python
import json, os, sys, time   # se nenhum desses é usado no arquivo
```

**Impacto:** Poluição do namespace, confusão para novos desenvolvedores, possível aumento de tempo de startup.

**Recomendação:** Remover imports não utilizados. Usar ferramentas como `autoflake`, `isort` ou o lint do editor.
