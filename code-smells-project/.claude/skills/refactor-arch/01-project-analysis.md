# Análise de Projeto — Heurísticas de Detecção

Use este documento como guia para executar a **Fase 1** da skill `refactor-arch`.

---

## 1. Detecção de Linguagem

| Arquivo / Extensão | Linguagem |
|--------------------|-----------|
| `*.py` + `requirements.txt` | Python |
| `*.js` + `package.json` (sem `tsconfig`) | JavaScript / Node.js |
| `*.ts` + `tsconfig.json` | TypeScript / Node.js |
| `*.go` + `go.mod` | Go |
| `*.java` + `pom.xml` ou `build.gradle` | Java |
| `*.rb` + `Gemfile` | Ruby |
| `*.php` + `composer.json` | PHP |

**Comando para contar arquivos:**
```bash
find . -name "*.py" | grep -v __pycache__ | grep -v .git | wc -l
find . -name "*.js" | grep -v node_modules | grep -v .git | wc -l
```

---

## 2. Detecção de Framework

### Python
| Sinal no código / arquivo | Framework |
|---------------------------|-----------|
| `from flask import Flask` ou `Flask` em `requirements.txt` | Flask |
| `from django.` ou `Django` em `requirements.txt` | Django |
| `from fastapi import FastAPI` | FastAPI |
| `from aiohttp import web` | aiohttp |

### Node.js / JavaScript
| Sinal no código / arquivo | Framework |
|---------------------------|-----------|
| `require('express')` ou `express` em `package.json` | Express.js |
| `require('fastify')` ou `fastify` em `package.json` | Fastify |
| `require('koa')` | Koa |
| `import { NestFactory }` | NestJS |

### Go
| Sinal no código / arquivo | Framework |
|---------------------------|-----------|
| `github.com/gin-gonic/gin` em `go.mod` | Gin |
| `github.com/go-chi/chi` em `go.mod` | Chi |
| `github.com/gofiber/fiber` em `go.mod` | Fiber |
| `net/http` apenas | Stdlib |

---

## 3. Detecção de Banco de Dados

### Python
| Sinal | Banco |
|-------|-------|
| `import sqlite3` | SQLite (raw) |
| `from flask_sqlalchemy import SQLAlchemy` | SQLAlchemy ORM |
| `from sqlalchemy` | SQLAlchemy raw |
| `import psycopg2` | PostgreSQL |
| `import pymysql` ou `import mysql.connector` | MySQL |
| `from pymongo import MongoClient` | MongoDB |
| `from tortoise` | Tortoise ORM |

### Node.js
| Sinal | Banco |
|-------|-------|
| `require('sqlite3')` | SQLite |
| `require('sequelize')` | Sequelize ORM |
| `require('typeorm')` | TypeORM |
| `require('mongoose')` | MongoDB (Mongoose) |
| `require('pg')` ou `require('postgres')` | PostgreSQL |
| `require('mysql2')` | MySQL |
| `require('knex')` | Knex.js (query builder) |

---

## 4. Mapeamento de Arquitetura

### Padrões de Identificação de Responsabilidades

Para cada arquivo, classifique a responsabilidade observando os imports e o conteúdo:

| O arquivo contém... | Responsabilidade |
|--------------------|-----------------|
| Definição de app + `app.run()` ou `app.listen()` | Entry point / composition root |
| `app.route()`, `app.get()`, `app.post()`, `Blueprint`, `Router` | Routing / Views |
| Classes de Model com campos e relações; queries SQL | Model / Data Access |
| Lógica de negócio: cálculos, validações, orquestrações | Controller / Service |
| `SECRET_KEY`, `DATABASE_URL`, porta, chaves de API | Config / Settings |
| Funções auxiliares reutilizáveis sem lógica de domínio | Utils / Helpers |

### Diagnóstico de Arquitetura

| Padrão Observado | Diagnóstico |
|-----------------|-------------|
| Um único arquivo com tudo | Monolito — sem camadas |
| Routes + lógica de negócio no mesmo arquivo | Falta de Controller |
| SQL direto dentro de routes | Falta de Model |
| Configuração misturada com código | Falta de Config |
| Models com regras de negócio complexas | Violação MVC — model com responsabilidades de controller |
| Pastas `models/`, `routes/`, `services/` mas sem controllers | Arquitetura parcial |

---

## 5. Mapeamento de Domínio

Leia os nomes de endpoints, tabelas e classes para identificar o domínio:

| Palavras-chave encontradas | Domínio provável |
|---------------------------|-----------------|
| `produtos`, `pedidos`, `pagamentos`, `carrinho`, `estoque` | E-commerce |
| `tasks`, `tarefas`, `categories`, `users`, `priority` | Task Manager / Produtividade |
| `courses`, `enrollments`, `payments`, `students`, `checkout` | LMS / Educação |
| `users`, `posts`, `comments`, `likes`, `follows` | Social / Blog |
| `employees`, `departments`, `salaries`, `attendance` | RH / Corporativo |

---

## 6. Contagem de Arquivos e Linhas

```bash
# Python — contar linhas de código
find . -name "*.py" | grep -v __pycache__ | grep -v .git | xargs wc -l 2>/dev/null | tail -1

# Node.js — contar linhas de código
find . -name "*.js" | grep -v node_modules | grep -v .git | xargs wc -l 2>/dev/null | tail -1

# Listar tabelas SQLite via Python
python3 -c "import sqlite3; c=sqlite3.connect('*.db'); print([r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")])"

# Listar tabelas via Node/sqlite3 — checar initDb() ou migrations
grep -r "CREATE TABLE" . --include="*.js" --include="*.ts" | grep -v node_modules
```

---

## 7. Template de Saída da Fase 1

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.1.1
Dependencies:  flask-cors, flask-sqlalchemy
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — 4 arquivos sem separação de camadas
Source files:  4 files analyzed (~800 lines total)
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```
