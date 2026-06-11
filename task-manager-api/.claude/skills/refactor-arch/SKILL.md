# Skill: refactor-arch
## Refatoração Arquitetural Automatizada para Padrão MVC

Você é um especialista em arquitetura de software. Quando esta skill é invocada, execute as **3 fases obrigatórias** na sequência abaixo, usando os arquivos de referência desta pasta como base de conhecimento.

---

## FASE 1 — ANÁLISE DO PROJETO

**Objetivo:** Entender a stack, o domínio e a arquitetura atual antes de qualquer análise crítica.

### Passos obrigatórios:

1. **Detectar a linguagem principal** — procure por `*.py`, `*.js`, `*.ts`, `*.go`, `*.java`, `*.rb`
2. **Detectar o framework** — inspecione `requirements.txt`, `package.json`, `go.mod`, `Gemfile`, `pom.xml`
3. **Detectar banco de dados** — procure por imports de SQLite, PostgreSQL, MySQL, MongoDB, ORMs (SQLAlchemy, Sequelize, TypeORM, etc.)
4. **Mapear a arquitetura atual** — liste todos os arquivos-fonte e identifique qual responsabilidade cada um tem (roteamento, lógica de negócio, acesso a dados, configuração)
5. **Identificar o domínio** — leia os endpoints e os nomes das entidades para entender o que a aplicação faz
6. **Contar arquivos e linhas de código** — `find . -name "*.py" -o -name "*.js" | grep -v node_modules | grep -v .git`

### Saída da Fase 1:

Imprima exatamente neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      [linguagem detectada]
Framework:     [framework + versão se disponível]
Dependencies:  [dependências principais]
Domain:        [descrição do domínio em 1 linha]
Architecture:  [descrição da arquitetura atual]
Source files:  [N files analyzed]
DB tables:     [tabelas ou modelos detectados]
================================
```

---

## FASE 2 — AUDITORIA DE ARQUITETURA

**Objetivo:** Identificar e classificar todos os anti-patterns e violações arquiteturais encontrados no código.

### Passos obrigatórios:

1. **Leia cada arquivo-fonte completamente**
2. **Cruce o código contra o Catálogo de Anti-patterns** em `02-antipatterns-catalog.md`
3. **Para cada finding, registre:**
   - Severidade: CRITICAL | HIGH | MEDIUM | LOW
   - Arquivo e número de linha exatos
   - Descrição objetiva do problema
   - Impacto no sistema
   - Recomendação de correção
4. **Ordene os findings por severidade:** CRITICAL → HIGH → MEDIUM → LOW
5. **Verifique APIs deprecated** — identifique uso de APIs obsoletas (ex: `Query.get()` no SQLAlchemy 2.0, callbacks no Node.js quando Promises estão disponíveis)

### Saída da Fase 2:

Use o template de `03-report-template.md` para gerar o relatório completo.

### ⚠️ PAUSA OBRIGATÓRIA

Após imprimir o relatório, **PARE e pergunte:**

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

**NÃO prossiga para a Fase 3 sem confirmação explícita do usuário.**

---

## FASE 3 — REFATORAÇÃO PARA MVC

**Objetivo:** Reestruturar o projeto para o padrão MVC, eliminando os anti-patterns encontrados.

### Passos obrigatórios:

1. **Leia as diretrizes MVC** em `04-mvc-guidelines.md` para entender a estrutura-alvo
2. **Consulte o Playbook de Refatoração** em `05-refactoring-playbook.md` para cada transformação
3. **Crie a nova estrutura de diretórios** baseada no padrão MVC para a stack detectada
4. **Execute as transformações na ordem:**
   a. Criar `config/` com configurações extraídas (sem hardcoded secrets)
   b. Criar/separar `models/` para abstrair entidades e acesso a dados
   c. Criar `controllers/` com lógica de negócio extraída das rotas e models
   d. Criar/reorganizar `routes/` (views) apenas para roteamento e serialização
   e. Criar `middlewares/` para error handling centralizado
   f. Limpar o entry point (`app.py` ou `app.js`) como composition root
5. **Preservar todos os endpoints originais** — nenhuma rota deve ser removida
6. **Eliminar os anti-patterns listados no relatório da Fase 2**

### Validação obrigatória após refatoração:

1. **Boot da aplicação** — tente iniciar a aplicação e verifique que não há erros de importação
   - Python: `python -c "import app"` ou `python app.py &` (kill depois)
   - Node.js: `node -e "require('./src/app')"` ou `node src/app.js &`
2. **Verificar endpoints** — liste todos os endpoints registrados e confirme que estão presentes
3. **Verificar zero anti-patterns críticos** — confirme que os CRITICALs foram eliminados

### Saída da Fase 3:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
[árvore de diretórios da nova estrutura]

## Transformations Applied
[lista das transformações executadas]

## Validation
  ✓/✗ Application boots without errors
  ✓/✗ All endpoints preserved
  ✓/✗ Zero CRITICAL anti-patterns remaining
  ✓/✗ Configuration externalized
  ✓/✗ SQL Injection vulnerabilities fixed
================================
```

---

## Regras Gerais

- **Seja agnóstico de tecnologia** — aplique o mesmo processo para Python/Flask, Node.js/Express, Go, etc.
- **Preserve a funcionalidade** — nunca remova endpoints ou lógica de negócio durante a refatoração
- **Documente cada mudança** — ao criar/modificar arquivos, explique brevemente o que foi feito
- **Use os arquivos de referência** — todo conhecimento necessário para executar as 3 fases está nos arquivos desta pasta
- **Adapte ao contexto** — um projeto já parcialmente organizado não precisa das mesmas transformações que um monolito puro
