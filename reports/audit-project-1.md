================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 4 | HIGH: 3 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] Remote Code Execution — Endpoint de SQL Arbitrário
File: app.py:59-78
Description: O endpoint `POST /admin/query` recebe um campo `sql` do body da request e executa diretamente via `cursor.execute(query)` sem qualquer autenticação ou restrição. Qualquer pessoa com acesso à API pode executar `DROP TABLE`, `DELETE FROM`, ou ler dados sensíveis.
Impact: Destruição completa do banco de dados ou exfiltração total de dados por qualquer usuário não autenticado.
Recommendation: Remover completamente o endpoint. Se necessário para manutenção, proteger com autenticação forte e lista de operações permitidas (allow-list).

### [CRITICAL] SQL Injection — Concatenação em Múltiplas Queries
File: models.py:28, 48-50, 57-62, 92, 109-111, 126-129, 140, 148-151, 154-165, 280-296
Description: Diversas queries constroem SQL por concatenação direta de strings: `"SELECT * FROM produtos WHERE id = " + str(id)`, `"INSERT INTO usuarios ... VALUES ('" + nome + "'"`. A função `login_usuario` (linha 109) é especialmente crítica pois permite bypass de autenticação.
Impact: Um atacante pode extrair todas as senhas, injetar registros falsos, ou destruir dados via manipulação de parâmetros de rota ou body.
Recommendation: Substituir todas as concatenações por queries parametrizadas: `cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))`.

### [CRITICAL] Hardcoded SECRET_KEY Exposta em Health Check
File: app.py:7, controllers.py:289
Description: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` hardcoded no código. Adicionalmente, a chave é retornada diretamente no endpoint `/health` em `controllers.py:289`: `"secret_key": "minha-chave-super-secreta-123"`.
Impact: Qualquer usuário da API pode obter a SECRET_KEY via `/health`. Chaves de sessão podem ser forjadas.
Recommendation: Mover para `os.environ.get("SECRET_KEY")`. Remover do response do health check.

### [CRITICAL] Senhas em Plaintext no Banco de Dados
File: models.py:122-130, database.py:75-82, models.py:105-120
Description: Senhas são armazenadas diretamente sem hashing: `cursor.execute("INSERT INTO usuarios ... VALUES ('" + senha + "')")`. O seed em `database.py` insere `"admin123"`, `"123456"`, `"senha123"` em plaintext. O endpoint de listagem de usuários (`controllers.py:128-134`) retorna o campo `senha` completo.
Impact: Violação de LGPD. Em caso de vazamento do banco, todas as senhas são imediatamente comprometidas.
Recommendation: Usar `werkzeug.security.generate_password_hash()` no cadastro e `check_password_hash()` no login. Remover campo `senha` das respostas da API.

### [HIGH] Business Logic no Model — Criação de Pedido
File: models.py:133-169
Description: A função `criar_pedido` em `models.py` contém toda a lógica de negócio do fluxo de pedido: validação de estoque, cálculo de total, orquestração de múltiplas queries, e retorno de erros de negócio. Isso viola a separação de responsabilidades do MVC.
Impact: Impossível testar a lógica de negócio sem um banco de dados real. Qualquer mudança de regra de negócio exige modificar o Model.
Recommendation: Mover a lógica de orquestração para `controllers/pedido_controller.py`. O model deve apenas executar queries individuais.

### [HIGH] N+1 Query Problem — Listagem de Pedidos
File: models.py:171-201, models.py:203-233
Description: As funções `get_pedidos_usuario` e `get_todos_pedidos` realizam queries aninhadas dentro de loops: para cada pedido, busca os itens; para cada item, busca o nome do produto. Para 10 pedidos com 3 itens cada, isso resulta em 1 + 10 + 30 = 41 queries.
Impact: Performance degradada exponencialmente. Com poucos dados já é perceptível; com escala é inviável.
Recommendation: Substituir por uma única query com JOIN entre `pedidos`, `itens_pedido` e `produtos`.

### [HIGH] Senha Exposta na Listagem de Usuários
File: models.py:72-87, controllers.py:128-134
Description: A função `get_todos_usuarios` inclui o campo `"senha": row["senha"]` na resposta, e o controller retorna isso diretamente via `jsonify`. O endpoint `GET /usuarios` expõe as senhas (plaintext) de todos os usuários.
Impact: Qualquer consumidor da API tem acesso imediato a todas as senhas.
Recommendation: Remover o campo `senha` da serialização. Usar um serializer explícito que lista apenas campos seguros.

### [MEDIUM] Lógica de Desconto com Magic Numbers
File: models.py:256-261
Description: A função `relatorio_vendas` usa valores literais `10000`, `5000`, `1000`, `0.1`, `0.05`, `0.02` sem nenhuma nomeação. Não é possível entender o que representam sem contexto externo.
Impact: Difícil de entender, manter e testar. Mudança de regra de negócio exige encontrar todos os magic numbers.
Recommendation: Extrair para constantes nomeadas: `LIMITE_DESCONTO_ALTO = 10000`, `TAXA_DESCONTO_ALTO = 0.10`.

### [MEDIUM] Notificações Fake Misturadas com Lógica do Controller
File: controllers.py:208-210, controllers.py:248-250
Description: O controller usa `print()` para simular envio de email, SMS e notificação push: `print("ENVIANDO EMAIL: ...")`. Isso não é uma implementação real, mas também não está encapsulado em um serviço separado.
Impact: Se um serviço de notificação real for adicionado futuramente, exige modificar controllers. Sem interface definida, difícil de testar.
Recommendation: Criar um `NotificationService` com métodos `send_email()`, `send_sms()`, `send_push()` e injetá-lo no controller.

### [LOW] print() como Logging em Toda a Aplicação
File: controllers.py:8, 57, 61, 106, 162, 179, 208-210, 248-250, app.py:56
Description: Uso extensivo de `print()` para logging de operações: `print("Listando " + str(len(produtos)) + " produtos")`, `print("ERRO: " + str(e))`. Não há níveis de log, sem formatação estruturada.
Impact: Impossível filtrar logs por severidade em produção. Saída misturada com output normal da aplicação.
Recommendation: Substituir por `import logging; logger = logging.getLogger(__name__)` com `logger.info()`, `logger.error()`.

### [LOW] Endpoint /admin/reset-db Sem Autenticação
File: app.py:47-57
Description: O endpoint `POST /admin/reset-db` apaga todos os dados das 4 tabelas sem autenticação alguma. Qualquer pessoa pode fazer um POST e limpar o banco.
Impact: Destruição de dados de produção por acidente ou ataque.
Recommendation: Remover em produção. Se necessário, proteger com autenticação administrativa.

### [LOW] DEBUG=True Hardcoded
File: app.py:8
Description: `app.config["DEBUG"] = True` hardcoded, o que expõe traceback completo da aplicação em respostas de erro.
Impact: Stack traces expõem estrutura interna, nomes de arquivos, e detalhes da aplicação para atacantes.
Recommendation: Usar `DEBUG = os.environ.get("DEBUG", "false").lower() == "true"`.

================================
Total: 12 findings
CRITICAL: 4 | HIGH: 3 | MEDIUM: 2 | LOW: 3
================================

## Deprecated APIs Detected

| Arquivo | Linha | Situação | Observação |
|---------|-------|----------|------------|
| models.py | múltiplas | SQL via concatenação de strings | Não é API deprecated, é anti-pattern de segurança (SQL Injection) |

Nenhuma API deprecated de framework detectada. O projeto usa raw SQLite sem ORM, portanto não há deprecações de SQLAlchemy.

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── config/
│   └── settings.py           ← SECRET_KEY e DEBUG via os.environ
├── models/
│   ├── __init__.py
│   ├── produto_model.py      ← queries parametrizadas, sem senha
│   ├── usuario_model.py      ← hash de senha com werkzeug
│   └── pedido_model.py       ← apenas CRUD, sem lógica de negócio
├── controllers/
│   ├── __init__.py
│   ├── produto_controller.py ← validações de negócio
│   ├── usuario_controller.py ← lógica de autenticação
│   └── pedido_controller.py  ← orquestração do fluxo de pedido
├── routes/
│   ├── __init__.py
│   ├── produto_routes.py     ← Blueprint Flask, apenas HTTP
│   ├── usuario_routes.py
│   └── pedido_routes.py
├── middlewares/
│   └── error_handler.py      ← error handlers centralizados
└── app.py                    ← composition root

## Transformations Applied
- PT-01: SECRET_KEY e DEBUG extraídos para config/settings.py com os.environ
- PT-02: Todas as 15+ queries com concatenação convertidas para parametrizadas (?)
- PT-03: Senhas hasheadas com werkzeug.security.generate_password_hash()
- PT-04: Lógica de negócio de pedido movida de models.py para pedido_controller.py
- PT-05: N/A (Python, não Node.js)
- PT-06: N+1 queries de pedidos substituídas por JOIN único
- PT-07: Error handler centralizado em middlewares/error_handler.py
- PT-08: Campo senha removido de todas as respostas de API
- PT-11: Endpoints /admin/query e /admin/reset-db removidos

## Validation
  ✓ Application boots without errors
  ✓ All endpoints preserved (produtos, usuarios, pedidos, login, relatorios, health)
  ✓ Zero CRITICAL anti-patterns remaining
  ✓ Configuration externalized (SECRET_KEY, DEBUG via env)
  ✓ SQL Injection vulnerabilities fixed (parametrized queries)
  ✓ Passwords hashed (werkzeug bcrypt)
  ✓ Sensitive data removed from API responses
================================
