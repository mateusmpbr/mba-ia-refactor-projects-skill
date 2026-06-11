# Template de Relatório de Auditoria

Use este template para gerar o relatório da **Fase 2**. Preencha cada seção com os dados coletados durante a análise do código.

---

## Formato do Relatório

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: [nome do diretório/projeto]
Stack:   [Linguagem + Framework]
Files:   [N analyzed] | ~[M] lines of code

## Summary
CRITICAL: [N] | HIGH: [N] | MEDIUM: [N] | LOW: [N]

## Findings

### [CRITICAL] [Nome do Anti-Pattern]
File: [caminho/arquivo.py:linha_inicio-linha_fim]
Description: [Descrição objetiva do que foi encontrado, citando o código]
Impact: [Consequência concreta para a aplicação]
Recommendation: [Ação específica para corrigir]

### [CRITICAL] [Nome do Anti-Pattern]
File: [caminho/arquivo.py:linha]
Description: ...
Impact: ...
Recommendation: ...

### [HIGH] [Nome do Anti-Pattern]
File: [caminho/arquivo.py:linha_inicio-linha_fim]
Description: ...
Impact: ...
Recommendation: ...

[... continuar para todos os findings ...]

================================
Total: [N] findings
CRITICAL: [N] | HIGH: [N] | MEDIUM: [N] | LOW: [N]
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

---

## Regras de Preenchimento

### Severidade
Use exatamente uma das quatro palavras: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`

| Severidade | Critério |
|------------|----------|
| **CRITICAL** | Falha grave de segurança (SQL Injection, credenciais expostas, RCE) ou God Class que impede qualquer organização |
| **HIGH** | Violação forte de MVC/SOLID que dificulta muito manutenção e testes |
| **MEDIUM** | Problema de padronização, duplicação ou performance moderada |
| **LOW** | Legibilidade, nomenclatura ruim, magic numbers, imports desnecessários |

### Arquivo e Linha
- Sempre inclua o caminho relativo ao projeto e a linha exata
- Para ranges: `models.py:1-350`
- Para linhas específicas: `app.py:8`
- Para funções: `controllers.py:188-220` (início e fim da função)

### Ordenação
Sempre ordene os findings da maior para menor severidade:
1. CRITICAL (múltiplos — ordenar por impacto)
2. HIGH
3. MEDIUM
4. LOW

### Descrição
- Citar o trecho de código problemático entre backticks
- Ser objetivo: "linha 28 concatena `str(id)` diretamente na query SQL"
- Não ser vago: ~~"código ruim"~~, ~~"pode ser melhorado"~~

---

## Exemplo Preenchido

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 4 | HIGH: 3 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] SQL Injection — Concatenação de String em Query
File: models.py:28
Description: A função `get_produto_por_id` constrói a query com concatenação direta: `"SELECT * FROM produtos WHERE id = " + str(id)`. Qualquer valor injetado no parâmetro `id` é executado no banco.
Impact: Um atacante pode extrair, modificar ou destruir todos os dados do banco via manipulação do parâmetro de rota `/produtos/<id>`.
Recommendation: Usar query parametrizada: `cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))`

### [CRITICAL] Hardcoded SECRET_KEY
File: app.py:7
Description: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` — chave de sessão hardcoded no código.
Impact: Qualquer pessoa com acesso ao código pode forjar tokens de sessão.
Recommendation: Usar `os.environ.get("SECRET_KEY")` e definir via variável de ambiente.

[...]

================================
Total: 12 findings
CRITICAL: 4 | HIGH: 3 | MEDIUM: 2 | LOW: 3
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

---

## Seção de APIs Deprecated

Quando encontrar uso de APIs obsoletas, adicione uma seção específica após os findings principais:

```
## Deprecated APIs Detected

| Arquivo | Linha | API Deprecated | Substituto Recomendado |
|---------|-------|----------------|------------------------|
| routes/task_routes.py | 67 | `Task.query.get(id)` (SQLAlchemy 1.x) | `db.session.get(Task, id)` (SQLAlchemy 2.0) |
| src/app.js | 45 | `res.send(404)` (Express 4) | `res.status(404).send()` |
```
