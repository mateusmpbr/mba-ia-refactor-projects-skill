# Desafio Skills — Refatoração Arquitetural Automatizada

Skill criada para o MBA IA que automatiza análise, auditoria e refatoração de projetos para o padrão MVC, agnóstica de tecnologia.

---

## Análise Manual

Antes de criar a skill, cada projeto foi analisado manualmente. Os findings abaixo guiaram o catálogo de anti-patterns da skill.

### Projeto 1 — code-smells-project (Python/Flask — E-commerce API)

| Severidade | Problema | Arquivo/Linha |
|------------|----------|---------------|
| **CRITICAL** | SQL Injection em 15+ queries via concatenação de strings | `models.py:28, 48, 57, 92, 109, 126, 140, 148, 162, 280` |
| **CRITICAL** | Endpoint `/admin/query` executa SQL arbitrário sem autenticação | `app.py:59-78` |
| **CRITICAL** | SECRET_KEY hardcoded e exposta no endpoint `/health` | `app.py:7`, `controllers.py:289` |
| **CRITICAL** | Senhas armazenadas em plaintext e retornadas pela API | `models.py:82-86`, `controllers.py:128-134` |
| **HIGH** | Lógica de negócio de pedido dentro do Model (N+1 queries + regras de estoque) | `models.py:133-169` |
| **HIGH** | N+1 query problem: para cada pedido, N queries de itens, para cada item N queries de produto | `models.py:171-233` |
| **HIGH** | Campo `senha` retornado pela listagem de usuários | `models.py:72-87` |
| **MEDIUM** | Magic numbers no cálculo de descontos | `models.py:256-261` |
| **MEDIUM** | Notificações fake misturadas com lógica de controller | `controllers.py:208-210` |
| **LOW** | `print()` usado como logging em toda a aplicação | múltiplos arquivos |
| **LOW** | Endpoint `/admin/reset-db` sem autenticação | `app.py:47-57` |
| **LOW** | `DEBUG=True` hardcoded | `app.py:8` |

**Justificativas relevantes:**
- O SQL Injection em `login_usuario` (linha 109) permite bypass completo de autenticação — o mais crítico do projeto.
- O endpoint `/admin/query` é um Remote Code Execution disfarçado de "ferramenta de debug".
- O campo `senha` retornado na API expõe senhas plaintext para qualquer consumidor — dupla violação (armazenamento + exposição).

---

### Projeto 2 — ecommerce-api-legacy (Node.js/Express — LMS com Checkout)

| Severidade | Problema | Arquivo/Linha |
|------------|----------|---------------|
| **CRITICAL** | Chave `pk_live_` de gateway de pagamento e senha de DB hardcoded | `src/utils.js:1-7` |
| **CRITICAL** | Função `badCrypto` — "hashing" via base64 não é criptografia real | `src/utils.js:17-23` |
| **CRITICAL** | God Class `AppManager` com DB, rotas e regras de negócio em uma classe | `src/AppManager.js:1-141` |
| **HIGH** | Callback Hell de 5 níveis no endpoint de checkout | `src/AppManager.js:37-78` |
| **HIGH** | Número de cartão de crédito logado em produção | `src/AppManager.js:45` |
| **HIGH** | Variáveis globais mutáveis (`globalCache`, `totalRevenue`) | `src/utils.js:9-10` |
| **HIGH** | DELETE de usuário deixa matrículas e pagamentos órfãos | `src/AppManager.js:131-137` |
| **MEDIUM** | N+1 queries no relatório financeiro via callbacks aninhados | `src/AppManager.js:89-128` |
| **MEDIUM** | Ausência de validação de input no checkout | `src/AppManager.js:29-35` |
| **LOW** | Nomes de variáveis de 1 letra (`u`, `e`, `p`, `cid`, `cc`) | `src/AppManager.js:29-33` |
| **LOW** | Banco em memória (`:memory:`) — dados perdidos no restart | `src/AppManager.js:7` |
| **LOW** | `console.log` como logging de produção | múltiplos |

**Justificativas relevantes:**
- A chave `pk_live_` é uma chave de produção real de gateway de pagamento — qualquer commit a expõe permanentemente.
- O log do número de cartão viola diretamente PCI-DSS, mesmo em ambiente de testes.
- A God Class impossibilita testes unitários de qualquer parte isolada.

---

### Projeto 3 — task-manager-api (Python/Flask — Task Manager)

| Severidade | Problema | Arquivo/Linha |
|------------|----------|---------------|
| **CRITICAL** | SECRET_KEY hardcoded | `app.py:13` |
| **CRITICAL** | Senha SMTP hardcoded no NotificationService | `services/notification_service.py:6-9` |
| **HIGH** | Token JWT falso e previsível (`fake-jwt-token-{id}`) | `routes/user_routes.py:209` |
| **HIGH** | Lógica de negócio pesada inline nas routes (50-70 linhas por handler) | `routes/task_routes.py:85-154` |
| **HIGH** | Ausência completa de middleware de autenticação | todas as routes |
| **MEDIUM** | Cálculo de `overdue` duplicado em 4 arquivos diferentes | `task_routes.py`, `user_routes.py`, `report_routes.py` |
| **MEDIUM** | API deprecated: `Query.get()` em 8+ ocorrências (SQLAlchemy 2.0) | `task_routes.py:67` e outros |
| **MEDIUM** | Política de senha mínima de 4 caracteres — insuficiente | `user_routes.py:64-65` |
| **MEDIUM** | NotificationService acumula notificações em memória infinitamente | `notification_service.py:6-7` |
| **LOW** | Bare `except:` em 7 blocos try/except | múltiplos |
| **LOW** | Imports não utilizados (`json, os, sys, time`) | `task_routes.py:7` |
| **LOW** | Serialização `to_dict()` reimplementada na route em vez de usar o método do model | `task_routes.py:17-29` |

**Justificativas relevantes:**
- Apesar de já ter alguma organização (models, routes, services), o projeto está longe de MVC: as routes concentram lógica de negócio que pertence a controllers inexistentes.
- O token JWT falso é o problema mais grave — anula completamente qualquer tentativa de segurança.
- O uso de API deprecated do SQLAlchemy é uma bomba-relógio que quebra a aplicação na próxima atualização.

---

## Construção da Skill

### Estrutura e Design

A skill foi organizada em 6 arquivos dentro de `.claude/skills/refactor-arch/`:

```
.claude/skills/refactor-arch/
├── SKILL.md                    ← prompt principal: instrui o agente nas 3 fases
├── 01-project-analysis.md      ← heurísticas de detecção de stack e arquitetura
├── 02-antipatterns-catalog.md  ← 18 anti-patterns com sinais de detecção e severidade
├── 03-report-template.md       ← template estruturado para o relatório da Fase 2
├── 04-mvc-guidelines.md        ← regras de cada camada MVC com exemplos de código
└── 05-refactoring-playbook.md  ← 11 transformações concretas com before/after
```

**Decisões de design:**

1. **SKILL.md como orquestrador** — o arquivo principal instrui as 3 fases de forma sequencial e explícita. Cada fase referencia os arquivos de conhecimento necessários, sem duplicar conteúdo.

2. **Pausa obrigatória na Fase 2** — o SKILL.md inclui instrução explícita de `PAUSA OBRIGATÓRIA` com texto de confirmação `[y/n]` após imprimir o relatório. Isso garante que o humano revise antes de qualquer modificação.

3. **Separação conhecimento vs comportamento** — o `SKILL.md` descreve **o que fazer** (comportamento), enquanto os arquivos 01-05 fornecem **o que saber** (conhecimento de domínio). Isso torna a skill mais fácil de atualizar.

4. **Sinais de detecção explícitos** — o catálogo de anti-patterns não usa descrições vagas como "código ruim". Cada anti-pattern tem trechos de código exatos para matching.

### Anti-patterns no Catálogo

O catálogo cobre 18 anti-patterns:

| AP | Nome | Severidade |
|----|------|------------|
| AP-01 | Hardcoded Credentials | CRITICAL |
| AP-02 | SQL Injection | CRITICAL |
| AP-03 | Remote Code Execution / Admin Desprotegido | CRITICAL |
| AP-04 | God Class / God Method | CRITICAL |
| AP-05 | Weak Cryptography / Fake Hashing | CRITICAL |
| AP-06 | Business Logic in Model/Route | HIGH |
| AP-07 | Callback Hell | HIGH |
| AP-08 | Global Mutable State | HIGH |
| AP-09 | Missing Auth / Fake Token | HIGH |
| AP-10 | N+1 Query Problem | MEDIUM |
| AP-11 | Sensitive Data Exposure | MEDIUM |
| AP-12 | Missing Input Validation | MEDIUM |
| AP-13 | Deprecated API Usage | MEDIUM |
| AP-14 | Magic Numbers | LOW |
| AP-15 | print() como Logging | LOW |
| AP-16 | Poor Variable Naming | LOW |
| AP-17 | Bare Except | LOW |
| AP-18 | Unused Imports | LOW |

**Por que esses anti-patterns?** Foram escolhidos por cobrir as categorias presentes nos 3 projetos: segurança (SQL Injection, credentials, weak crypto), arquitetura (God Class, business logic in wrong layer, global state), e qualidade (N+1, magic numbers, bare except).

### Agnóstico de Tecnologia

A skill funciona nos 3 projetos por:

1. **Detecção automática de stack** — `01-project-analysis.md` mapeia extensões, arquivos de manifesto e imports para identificar linguagem e framework
2. **Sinais de detecção multi-linguagem** — o catálogo de anti-patterns inclui exemplos em Python E Node.js para cada problema
3. **Playbook com exemplos para ambas as stacks** — `05-refactoring-playbook.md` tem before/after em Python (`werkzeug`, raw SQL, Flask) e Node.js (`bcryptjs`, `async/await`, Express)
4. **Guidelines MVC adaptáveis** — `04-mvc-guidelines.md` define a estrutura-alvo separadamente para Python/Flask e Node.js/Express

### Desafios e Soluções

- **Projeto 3 já parcialmente organizado:** a Fase 3 precisava ser adaptativa — não criar estrutura do zero, mas melhorar o que existe. A instrução "adapte ao contexto" no SKILL.md resolve isso.
- **Pausa na Fase 2 ser seguida:** a instrução é colocada com formatação especial (⚠️ PAUSA OBRIGATÓRIA) e texto de confirmação explícito para tornar impossível de ignorar.
- **Sinais de detecção sem falsos positivos:** os sinais usam trechos de código específicos ao invés de keywords genéricas, reduzindo falsos positivos.

---

## Resultados

### Resumo dos Relatórios de Auditoria

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---------|----------|------|--------|-----|-------|
| code-smells-project (Python/Flask) | 4 | 3 | 2 | 3 | 12 |
| ecommerce-api-legacy (Node.js/Express) | 3 | 4 | 2 | 3 | 12 |
| task-manager-api (Python/Flask) | 2 | 3 | 4 | 3 | 12 |

### Comparação Antes/Depois

#### Projeto 1 — code-smells-project

**Antes:**
```
code-smells-project/
├── app.py          (roteamento + 2 endpoints admin + entry point)
├── controllers.py  (handlers HTTP com print() e lógica de notificação)
├── models.py       (queries SQL com concatenação + lógica de pedido)
└── database.py     (schema + seed)
```

**Depois:**
```
code-smells-project/src/
├── config/settings.py
├── models/{produto,usuario,pedido}_model.py
├── controllers/{produto,usuario,pedido}_controller.py
├── routes/{produto,usuario,pedido}_routes.py
├── middlewares/error_handler.py
└── app.py (composition root)
```

#### Projeto 2 — ecommerce-api-legacy

**Antes:**
```
ecommerce-api-legacy/src/
├── app.js          (entry point apenas)
├── AppManager.js   (God Class: DB init + rotas + negócio = 141 linhas)
└── utils.js        (config hardcoded + badCrypto + globalCache)
```

**Depois:**
```
ecommerce-api-legacy/src/
├── config/settings.js
├── models/{user,course,payment}Model.js
├── controllers/{checkout,report}Controller.js
├── routes/{checkout,admin}Routes.js
├── middlewares/errorHandler.js
└── app.js (createApp())
```

#### Projeto 3 — task-manager-api

**Antes:**
```
task-manager-api/
├── app.py          (SECRET_KEY hardcoded)
├── models/{task,user,category}.py
├── routes/{task,user,report}_routes.py  (com lógica de negócio inline)
├── services/notification_service.py    (SMTP hardcoded + state global)
└── utils/helpers.py
```

**Depois:**
```
task-manager-api/
├── config/settings.py       ← NOVO
├── models/{task,user,category}.py  ← melhorado (is_overdue consolidado)
├── controllers/{task,user,report}_controller.py  ← NOVO
├── routes/{task,user,report}_routes.py  ← simplificado
├── middlewares/{error_handler,auth_middleware}.py  ← NOVO
├── services/notification_service.py  ← melhorado (env vars)
└── app.py  ← limpo
```

### Checklist de Validação

#### Projeto 1 — code-smells-project

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask)
- [x] Domínio descrito corretamente (E-commerce API)
- [x] 4 arquivos analisados

**Fase 2 — Auditoria**
- [x] Relatório segue template definido
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] 12 findings identificados (mínimo: 5)
- [x] Verificação de APIs deprecated incluída
- [x] Skill pausou e pediu confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura MVC criada (config, models, controllers, routes, middlewares)
- [x] Configuração extraída (SECRET_KEY, DEBUG via os.environ)
- [x] Models com queries parametrizadas
- [x] Routes com roteamento apenas
- [x] Controllers com lógica de negócio
- [x] Error handling centralizado
- [x] Entry point limpo (composition root)
- [x] Aplicação inicia sem erros
- [x] Endpoints originais preservados

#### Projeto 2 — ecommerce-api-legacy

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (Node.js/JavaScript)
- [x] Framework detectado corretamente (Express.js)
- [x] Domínio descrito corretamente (LMS com checkout)
- [x] 3 arquivos analisados

**Fase 2 — Auditoria**
- [x] Relatório segue template definido
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade
- [x] 12 findings identificados
- [x] APIs deprecated detectadas (sqlite3 callback-style)
- [x] Skill pausou e pediu confirmação

**Fase 3 — Refatoração**
- [x] Estrutura MVC criada
- [x] Credenciais extraídas para process.env
- [x] Callback hell refatorado para async/await
- [x] God Class decomposta em camadas
- [x] Error handler Express adicionado
- [x] Aplicação inicia sem erros
- [x] Endpoints preservados

#### Projeto 3 — task-manager-api

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask + SQLAlchemy)
- [x] Domínio descrito corretamente (Task Manager)
- [x] 10 arquivos analisados

**Fase 2 — Auditoria**
- [x] Relatório segue template definido
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade
- [x] 12 findings identificados
- [x] 8 ocorrências de API deprecated (`Query.get`) detectadas
- [x] Skill pausou e pediu confirmação

**Fase 3 — Refatoração**
- [x] Estrutura melhorada sem quebrar organização existente
- [x] Configurações extraídas para config/settings.py
- [x] Deprecated API substituída (`db.session.get`)
- [x] Controllers criados com lógica extraída das routes
- [x] Middleware de auth adicionado
- [x] Aplicação inicia sem erros
- [x] Endpoints preservados

### Observações sobre Comportamento em Stacks Diferentes

A skill se comportou de forma consistente nos 3 projetos:

- **Python/Flask (ambos):** Detectou corretamente Flask via `from flask import Flask` e SQLAlchemy via imports. Os padrões de SQL injection por concatenação foram identificados em `models.py` do projeto 1. No projeto 3, detectou o padrão deprecated `Query.get()`.

- **Node.js/Express:** Detectou `require('express')` no `package.json` e identificou o padrão de callback hell via aninhamento de `db.get()` dentro de outros `db.get()`. O `badCrypto` foi identificado pelo sinal de "base64 + substring em loop".

- **Projeto parcialmente organizado (projeto 3):** A Fase 3 foi adaptativa — criou `controllers/` e `config/` que faltavam, e melhorou os `routes/` existentes sem recriar toda a estrutura do zero. Endpoints continuaram respondendo.

---

## Como Executar

### Pré-requisitos

- **Claude Code** instalado e configurado
- Python 3.10+ (para projetos 1 e 3)
- Node.js 18+ (para projeto 2)

### Instalar dependências

```bash
# Projeto 1
cd code-smells-project && pip install -r requirements.txt

# Projeto 2
cd ecommerce-api-legacy && npm install

# Projeto 3
cd task-manager-api && pip install -r requirements.txt
```

### Executar a Skill

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

### Estrutura dos Relatórios

Os relatórios gerados pela Fase 2 estão em:
- [`reports/audit-project-1.md`](reports/audit-project-1.md) — code-smells-project
- [`reports/audit-project-2.md`](reports/audit-project-2.md) — ecommerce-api-legacy
- [`reports/audit-project-3.md`](reports/audit-project-3.md) — task-manager-api

### Validar que a Refatoração Funcionou

```bash
# Projeto 1 (Python/Flask)
cd code-smells-project
python -c "from app import app; print('OK')"
python app.py &
curl http://localhost:5000/health
kill %1

# Projeto 2 (Node.js)
cd ecommerce-api-legacy
node -e "require('./src/app'); console.log('OK')"

# Projeto 3 (Python/Flask)
cd task-manager-api
python -c "from app import app; print('OK')"
```

### Localização das Skills

```
code-smells-project/.claude/skills/refactor-arch/
ecommerce-api-legacy/.claude/skills/refactor-arch/
task-manager-api/.claude/skills/refactor-arch/
```

Cada pasta contém os mesmos 6 arquivos:
- `SKILL.md` — prompt principal (não alterar o nome)
- `01-project-analysis.md` — heurísticas de detecção
- `02-antipatterns-catalog.md` — catálogo de 18 anti-patterns
- `03-report-template.md` — template do relatório
- `04-mvc-guidelines.md` — guidelines de arquitetura MVC
- `05-refactoring-playbook.md` — 11 padrões de transformação
