================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express + SQLite3
Files:   3 analyzed | ~150 lines of code

## Summary
CRITICAL: 3 | HIGH: 4 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] Hardcoded Credentials — Chaves de Produção no Código
File: src/utils.js:1-7
Description: O objeto `config` contém `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`, e `smtpUser: "no-reply@fullcycle.com.br"` hardcoded no código-fonte. A chave `pk_live_` indica uma chave de produção real de gateway de pagamento.
Impact: Qualquer pessoa com acesso ao repositório (incluindo histórico Git) tem acesso às credenciais de produção do gateway de pagamento e banco de dados.
Recommendation: Mover para variáveis de ambiente: `process.env.PAYMENT_GATEWAY_KEY`, `process.env.DB_PASS`. Criar `.env.example` e adicionar `.env` ao `.gitignore`.

### [CRITICAL] Weak Cryptography — Fake Hashing de Senhas
File: src/utils.js:17-23
Description: A função `badCrypto` realiza um "hash" codificando a senha em base64 e repetindo fragmentos em loop: `Buffer.from(pwd).toString('base64').substring(0, 2)` repetido 10.000 vezes. O resultado é determinístico e reversível. Não é um algoritmo de hashing real.
Impact: Todas as senhas armazenadas são facilmente recuperáveis. Violação grave de segurança.
Recommendation: Substituir por `bcryptjs`: `const hash = await bcrypt.hash(password, 12)` e verificar com `bcrypt.compare(password, hash)`.

### [CRITICAL] God Class — AppManager contém DB, Rotas e Negócio
File: src/AppManager.js:1-141
Description: A classe `AppManager` acumula: inicialização do banco de dados (`initDb()`), registro de todas as rotas (`setupRoutes()`), lógica de negócio do checkout (validação, pagamento, matrícula), e logging. É um monolito em uma única classe.
Impact: Impossível testar qualquer parte em isolamento. Qualquer mudança no checkout afeta o roteamento e vice-versa.
Recommendation: Separar em `models/` (queries), `controllers/` (lógica de negócio), `routes/` (HTTP) conforme padrão MVC.

### [HIGH] Callback Hell — 5 Níveis de Aninhamento no Checkout
File: src/AppManager.js:37-78
Description: O endpoint `POST /api/checkout` tem callbacks aninhados 5 níveis de profundidade: `db.get → db.get → db.run → db.run → db.run`. Torna o fluxo de controle impossível de seguir.
Impact: Código ilegível, extremamente difícil de manter ou debugar. Erros em camadas internas são silenciados.
Recommendation: Refatorar usando `util.promisify` ou `async/await` para achatar o aninhamento.

### [HIGH] Sensitive Data em Logs — Número de Cartão e Chave de API
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` — loga o número completo do cartão de crédito e a chave privada do gateway em produção.
Impact: Dados de PCI-DSS (cartão de crédito) e credenciais em logs. Violação grave de compliance e segurança.
Recommendation: Nunca logar dados de cartão. Logar apenas os últimos 4 dígitos se necessário para debug. Remover referências à chave do gateway dos logs.

### [HIGH] Global Mutable State — Cache e Revenue Globais
File: src/utils.js:9-10
Description: `let globalCache = {}` e `let totalRevenue = 0` são variáveis mutáveis no escopo do módulo, compartilhadas entre todas as requisições. Em ambiente com múltiplos workers ou testes, o estado vaza entre contextos.
Impact: Race conditions em ambientes concorrentes. Estado imprevisível entre requisições. `totalRevenue` nunca é atualizado corretamente mas existe como variável global.
Recommendation: Eliminar estado global. Usar injeção de dependência para cache (ex: Redis, Map local com TTL) e calcular revenue sob demanda.

### [HIGH] Deleção de Usuário sem Limpeza de Dados Relacionados
File: src/AppManager.js:131-137
Description: O endpoint `DELETE /api/users/:id` deleta o usuário mas o response textual admite explicitamente: `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."`. Enrollment e payment órfãos permanecem no banco.
Impact: Corrupção de dados referencial. Relatório financeiro pode incluir matrículas de usuários inexistentes.
Recommendation: Implementar deleção em cascata via `ON DELETE CASCADE` no schema, ou deleção manual na transação, ou soft-delete.

### [MEDIUM] N+1 Queries no Relatório Financeiro
File: src/AppManager.js:89-128
Description: O endpoint `/api/admin/financial-report` itera sobre cursos, e para cada curso busca matrículas; para cada matrícula busca o usuário e o pagamento — tudo via callbacks assíncronos aninhados. Para 2 cursos com 1 matrícula cada, já são 7 queries independentes.
Impact: Performance não escala. Com dados reais (100 cursos, 1000 matrículas), gera 2000+ queries.
Recommendation: Substituir por um JOIN único: `SELECT c.title, u.name, p.amount, p.status FROM courses c LEFT JOIN enrollments e ON e.course_id = c.id LEFT JOIN users u ON u.id = e.user_id LEFT JOIN payments p ON p.enrollment_id = e.id`.

### [MEDIUM] Falta de Validação de Input no Checkout
File: src/AppManager.js:29-35
Description: O endpoint verifica apenas se `u`, `e`, `cid`, `cc` não são falsy, mas não valida: formato de email, tamanho do número de cartão, se `c_id` é um número válido, ou se o corpo da request é JSON válido.
Impact: Erros 500 não descritivos quando dados inválidos são enviados. Potencial para injeção em campos não validados.
Recommendation: Implementar validação de schema no início do handler usando Joi, Zod, ou validações manuais explícitas.

### [LOW] Poor Variable Naming no Checkout Handler
File: src/AppManager.js:29-33
Description: Variáveis com nomes de 1-2 letras: `u` (userName), `e` (email), `p` (password), `cid` (courseId), `cc` (cardNumber). Não é possível entender o fluxo sem ler cuidadosamente o código.
Impact: Difícil de revisar, manter e onboarding de novos desenvolvedores.
Recommendation: Renomear para `userName`, `email`, `password`, `courseId`, `cardNumber`.

### [LOW] Banco de Dados In-Memory — Dados Perdidos no Restart
File: src/AppManager.js:7
Description: `new sqlite3.Database(':memory:')` — banco em memória. Todos os dados são perdidos quando o servidor reinicia.
Impact: Não adequado para ambiente de staging/produção. Dificulta testes de integração.
Recommendation: Usar arquivo persistente: `new sqlite3.Database(process.env.DB_PATH || './data.db')`.

### [LOW] Console.log como Logging de Produção
File: src/utils.js:13, src/AppManager.js:45
Description: `console.log('[LOG] Salvando no cache...')` e `console.log(...)` usados para logging em código de produção, sem níveis, sem estrutura.
Impact: Sem diferenciação entre debug, info e error. Impossível filtrar em produção.
Recommendation: Usar `winston` ou `pino` com níveis estruturados.

================================
Total: 12 findings
CRITICAL: 3 | HIGH: 4 | MEDIUM: 2 | LOW: 3
================================

## Deprecated APIs Detected

| Arquivo | Linha | API Deprecated | Substituto Recomendado |
|---------|-------|----------------|------------------------|
| src/AppManager.js | 50, 54, 57, 69 | `sqlite3` callback-style API | `better-sqlite3` (síncrono) ou `sqlite` (Promise-based) |
| src/utils.js | 17-23 | Implementação caseira de hash | `bcryptjs` (npm) |

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── config/
│   └── settings.js           ← process.env para todas as credenciais
├── models/
│   ├── userModel.js          ← queries parametrizadas, sem callback hell
│   ├── courseModel.js
│   └── paymentModel.js
├── controllers/
│   ├── checkoutController.js ← lógica de negócio com async/await
│   └── reportController.js
├── routes/
│   ├── checkoutRoutes.js     ← express.Router(), handlers mínimos
│   └── adminRoutes.js
├── middlewares/
│   └── errorHandler.js       ← Express error middleware centralizado
└── app.js                    ← createApp() + registro de routers

## Transformations Applied
- PT-01: Credenciais movidas para process.env em config/settings.js
- PT-03: Substituído badCrypto por bcryptjs com salt rounds 12
- PT-04: God Class AppManager decomposta em models + controllers + routes
- PT-05: Callback hell do checkout refatorado para async/await
- PT-07: Error handler centralizado adicionado como Express middleware
- PT-08: Número de cartão removido dos logs; apenas últimos 4 dígitos logados
- PT-06: N+1 do relatório substituído por JOIN único
- Fix: Deleção de usuário agora remove enrollments e payments relacionados

## Validation
  ✓ Application boots without errors
  ✓ All endpoints preserved (/api/checkout, /api/admin/financial-report, /api/users/:id)
  ✓ Zero CRITICAL anti-patterns remaining
  ✓ Configuration externalized (credenciais via process.env)
  ✓ Weak crypto replaced (bcryptjs)
  ✓ God Class decomposed into MVC layers
================================
