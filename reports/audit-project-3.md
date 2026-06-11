================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask + SQLAlchemy
Files:   10 analyzed | ~750 lines of code

## Summary
CRITICAL: 2 | HIGH: 3 | MEDIUM: 4 | LOW: 3

## Findings

### [CRITICAL] Hardcoded SECRET_KEY na Aplicação
File: app.py:13
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` hardcoded diretamente na configuração da aplicação Flask. Não há uso de variável de ambiente.
Impact: Chave de sessão comprometida para qualquer pessoa com acesso ao código. Em produção, permite forjar cookies de sessão.
Recommendation: Substituir por `app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-only-insecure-key')`.

### [CRITICAL] Credenciais SMTP Hardcoded no NotificationService
File: services/notification_service.py:6-9
Description: O serviço de notificação contém `self.email_password = 'senha123'` e `self.email_user = 'taskmanager@gmail.com'` hardcoded no construtor da classe. Qualquer commit expõe essas credenciais no histórico Git.
Impact: Credenciais de email comprometidas. Se usadas em produção, permite acesso indevido à conta de email.
Recommendation: Mover para variáveis de ambiente: `os.environ.get('SMTP_USER')`, `os.environ.get('SMTP_PASSWORD')`.

### [HIGH] Token JWT Falso — Autenticação sem Segurança Real
File: routes/user_routes.py:209
Description: O endpoint `/login` retorna `'token': 'fake-jwt-token-' + str(user.id)` — um token completamente previsível. O token para o usuário de ID 5 é sempre `fake-jwt-token-5`. Não há verificação desse token em nenhum endpoint protegido.
Impact: Qualquer pessoa pode se passar por qualquer usuário simplesmente gerando `fake-jwt-token-{id}`. Todas as rotas são efetivamente públicas.
Recommendation: Implementar JWT real com `PyJWT`: `jwt.encode({'user_id': user.id, 'exp': datetime.utcnow() + timedelta(hours=24)}, SECRET_KEY, algorithm='HS256')`.

### [HIGH] Lógica de Negócio Pesada nas Routes
File: routes/task_routes.py:85-154, routes/user_routes.py:42-90
Description: As routes contêm extensas validações de negócio inline: verificação de usuário existente (`User.query.get(user_id)`), verificação de categoria, validação de prioridade, parseamento de data — tudo dentro do handler da route. As routes têm 50-70 linhas cada.
Impact: Viola a separação de responsabilidades. Lógica de negócio não é reutilizável nem testável isoladamente.
Recommendation: Extrair validações e regras de negócio para `controllers/task_controller.py` e `controllers/user_controller.py`. Routes devem chamar controller e serializar resultado.

### [HIGH] Ausência de Middleware de Autenticação
File: routes/task_routes.py, routes/user_routes.py, routes/report_routes.py
Description: Nenhuma rota verifica o token de autenticação antes de processar a requisição. Qualquer endpoint pode ser acessado sem autenticação: `GET /tasks`, `DELETE /tasks/<id>`, `GET /reports/summary`, `GET /users`.
Impact: API completamente aberta. Qualquer pessoa pode listar todas as tasks e usuários, deletar dados, acessar relatórios.
Recommendation: Criar `middlewares/auth_middleware.py` com decorator `@require_auth` que verifica o JWT e rejeita requests sem token válido.

### [MEDIUM] Cálculo de Overdue Duplicado em 4 Arquivos
File: routes/task_routes.py:30-39, routes/task_routes.py:71-80, routes/user_routes.py:171-180, routes/report_routes.py:34-40
Description: A lógica de verificação de tarefa atrasada é copiada e colada identicamente em pelo menos 4 lugares diferentes:
```python
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
Impact: Mudança na regra de negócio de "overdue" exige atualizar 4 locais. Risco de inconsistência.
Recommendation: Consolidar no método `is_overdue()` do model `Task` (já existe em `models/task.py:50-60`, basta usar via `t.is_overdue()`).

### [MEDIUM] Deprecated SQLAlchemy API — Query.get()
File: routes/task_routes.py:67, routes/task_routes.py:117, routes/task_routes.py:122, routes/task_routes.py:158, routes/task_routes.py:189, routes/user_routes.py:29, routes/user_routes.py:96, routes/report_routes.py:105
Description: O padrão `Task.query.get(id)`, `User.query.get(id)`, `Category.query.get(id)` é deprecated no SQLAlchemy 2.0 e foi removido. Emite `LegacyAPIWarning` em SQLAlchemy >= 1.4.
Impact: Aplicação pode quebrar ao atualizar SQLAlchemy para versão 2.x.
Recommendation: Substituir todos por `db.session.get(Task, task_id)`, `db.session.get(User, user_id)`, `db.session.get(Category, cat_id)`.

### [MEDIUM] Política de Senha Fraca
File: routes/user_routes.py:64-65
Description: A validação de senha aceita mínimo de 4 caracteres: `if len(password) < 4: return jsonify({'error': 'Senha deve ter no mínimo 4 caracteres'})`. Senhas como `"1234"` ou `"abcd"` são aceitas.
Impact: Usuários podem ter senhas trivialmente adivinháveis, especialmente com o token JWT falso que permite identificar IDs.
Recommendation: Aumentar para mínimo de 8 caracteres e adicionar validação de complexidade (letras + números).

### [MEDIUM] NotificationService com Estado Global Mutável
File: services/notification_service.py:6-7
Description: `self.notifications = []` é uma lista de instância que acumula notificações infinitamente em memória. Como o serviço pode ser usado como singleton, esse estado cresce sem limite durante o ciclo de vida da aplicação.
Impact: Memory leak em ambientes de longa execução. Dados de notificação perdidos no restart.
Recommendation: Usar banco de dados ou tabela de notificações para persistência. Remover o acúmulo em memória.

### [LOW] Bare Except em Múltiplas Routes
File: routes/task_routes.py:62, routes/task_routes.py:233, routes/user_routes.py:87, routes/user_routes.py:130, routes/report_routes.py:183, routes/report_routes.py:204, routes/report_routes.py:217
Description: Múltiplos blocos `except:` sem especificar o tipo de exceção capturam qualquer erro, incluindo `KeyboardInterrupt` e `SystemExit`.
Impact: Impossível distinguir erros esperados de bugs. Silencia erros críticos.
Recommendation: Substituir `except:` por `except Exception as e:` e logar `str(e)`.

### [LOW] Imports Não Utilizados
File: routes/task_routes.py:7, app.py:7
Description: `routes/task_routes.py:7` importa `json, os, sys, time` — nenhum utilizado no arquivo. `app.py:7` importa `os, sys, json, datetime` — `os`, `sys`, `json` não são utilizados.
Impact: Poluição do namespace, confusão para leitores do código.
Recommendation: Remover imports não utilizados. Usar `autoflake --remove-all-unused-imports` ou linter.

### [LOW] To_dict Duplicado Entre Model e Route
File: models/task.py:23-36, routes/task_routes.py:17-29
Description: O método `Task.to_dict()` serializa o objeto, mas `get_tasks()` em `task_routes.py` reimplementa a mesma serialização manualmente em vez de chamar `t.to_dict()`. Isso resulta em dois formatos potencialmente divergentes.
Impact: Risco de inconsistência na serialização entre endpoints diferentes.
Recommendation: Usar `t.to_dict()` consistentemente em todas as routes que serializam tarefas.

================================
Total: 12 findings
CRITICAL: 2 | HIGH: 3 | MEDIUM: 4 | LOW: 3
================================

## Deprecated APIs Detected

| Arquivo | Linha | API Deprecated | Substituto Recomendado |
|---------|-------|----------------|------------------------|
| routes/task_routes.py | 67 | `Task.query.get(task_id)` (SQLAlchemy 1.x) | `db.session.get(Task, task_id)` (SQLAlchemy 2.0) |
| routes/task_routes.py | 117 | `User.query.get(user_id)` | `db.session.get(User, user_id)` |
| routes/task_routes.py | 122 | `Category.query.get(cat_id)` | `db.session.get(Category, cat_id)` |
| routes/task_routes.py | 158 | `Task.query.get(task_id)` | `db.session.get(Task, task_id)` |
| routes/task_routes.py | 189 | `User.query.get(user_id)` | `db.session.get(User, user_id)` |
| routes/user_routes.py | 29 | `User.query.get(user_id)` | `db.session.get(User, user_id)` |
| routes/user_routes.py | 96 | `User.query.get(user_id)` | `db.session.get(User, user_id)` |
| routes/report_routes.py | 105 | `User.query.get(user_id)` | `db.session.get(User, user_id)` |

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
(estrutura já parcialmente organizada, melhorias aplicadas)

models/           ← já existia — mantido com melhorias
  task.py         ← is_overdue() consolidado
  user.py         ← mantido
  category.py     ← mantido
controllers/      ← NOVO
  task_controller.py    ← lógica extraída das routes
  user_controller.py
  report_controller.py
routes/           ← já existia — simplificado
  task_routes.py        ← handlers delgando para controller
  user_routes.py
  report_routes.py
services/         ← já existia — melhorado
  notification_service.py  ← credenciais via env
middlewares/      ← NOVO
  error_handler.py      ← centralizdo
  auth_middleware.py    ← JWT real
config/           ← NOVO
  settings.py           ← SECRET_KEY e SMTP via env

## Transformations Applied
- PT-01: SECRET_KEY e SMTP_PASSWORD extraídos para config/settings.py (os.environ)
- PT-09: Todas as 8 ocorrências de Query.get() substituídas por db.session.get()
- PT-04: Lógica de negócio das routes extraída para controllers/
- PT-10: Cálculo de overdue consolidado no método is_overdue() do Task model
- PT-07: Error handler centralizado em middlewares/error_handler.py
- Fix: JWT real implementado com PyJWT
- Fix: Bare excepts substituídos por except Exception as e
- Fix: Imports não utilizados removidos

## Validation
  ✓ Application boots without errors
  ✓ All endpoints preserved (tasks, users, reports, categories, login, health)
  ✓ Zero CRITICAL anti-patterns remaining
  ✓ Configuration externalized (SECRET_KEY, SMTP via env)
  ✓ Deprecated SQLAlchemy API replaced (db.session.get)
  ✓ Duplicate overdue logic consolidated
  ✓ Authentication middleware added
================================
