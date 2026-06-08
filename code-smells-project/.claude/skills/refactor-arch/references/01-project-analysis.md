# Referência 01 — Análise de Projeto (Fase 1)

Heurísticas para detectar **linguagem, framework, persistência, domínio e
arquitetura** de qualquer projeto, sem assumir a stack a priori.

## 1. Detecção de linguagem e framework (pelo manifesto)

Procure primeiro o arquivo-manifesto na raiz. Ele é a fonte mais confiável.

| Manifesto encontrado | Linguagem | Como achar o framework |
|---|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` | Python | Procure `flask`, `django`, `fastapi`, `sqlalchemy`, etc. nas deps + versão |
| `package.json` | JavaScript/TypeScript (Node) | Veja `dependencies`: `express`, `fastify`, `koa`, `nestjs`, `next` |
| `pom.xml`, `build.gradle` | Java/Kotlin | `spring-boot`, `quarkus`, `micronaut` |
| `Gemfile` | Ruby | `rails`, `sinatra` |
| `go.mod` | Go | `gin`, `echo`, `fiber`, net/http |
| `composer.json` | PHP | `laravel`, `symfony`, `slim` |
| `*.csproj` | C# | ASP.NET Core |

Sempre **anote a versão** do framework (ex: `flask==3.1.1`, `"express": "^4.18.2"`).
Liste também dependências relevantes para arquitetura (CORS, ORM, validação, auth).

## 2. Confirmação pela sintaxe (quando o manifesto for ambíguo)

- **Flask**: `from flask import Flask`, `@app.route`, `app.add_url_rule`, `Blueprint`.
- **Express**: `require('express')`, `app.get/post(...)`, `app.use(...)`, `express.Router()`.
- **Django**: `urls.py`, `settings.py`, `models.Model`.
- **FastAPI**: `from fastapi import FastAPI`, decorators `@app.get`.
- **Spring**: anotações `@RestController`, `@Service`, `@Repository`.

## 3. Detecção de persistência e entidades

Identifique **como** os dados são armazenados — isso determina a estratégia de Model
na Fase 3:

| Sinal | Mecanismo |
|---|---|
| `sqlite3.connect`, `cursor.execute("SELECT ...")` (Python) | SQLite cru / SQL em string |
| `new sqlite3.Database(...)`, `db.run/get/all` (Node) | SQLite cru via callbacks |
| `db.Column`, `db.Model`, `SQLAlchemy()` | ORM SQLAlchemy |
| `mongoose.Schema`, `Sequelize`, `Prisma`, `TypeORM` | ORM/ODM Node |
| `CREATE TABLE ...` em strings | Schema embutido no código |

**Entidades/tabelas**: extraia de `CREATE TABLE <nome>`, de classes de model
(`class Produto(db.Model)`, `__tablename__`), ou de coleções/repos. Liste-as.

## 4. Inferência de domínio

Combine os nomes de **tabelas + rotas + entidades** para descrever o domínio em uma
linha. Exemplos:

- Tabelas `produtos, usuarios, pedidos, itens_pedido` + rotas `/produtos`, `/pedidos`,
  `/login` → **"API de E-commerce"**.
- Tabelas `users, courses, enrollments, payments` + rota `/api/checkout` →
  **"API de LMS / e-learning com fluxo de checkout"**.
- Tabelas `tasks, users, categories` + rotas `/tasks`, `/reports` →
  **"API de Task Manager"**.

## 5. Mapeamento da arquitetura atual

Responda mentalmente e descreva em 1 linha:

- **Quantos arquivos-fonte** existem? (não conte manifestos, dbs, caches)
- **Há separação de camadas?** Procure pastas/arquivos como `models/`, `controllers/`,
  `routes/`, `services/`, `views/`, `config/`. Sua ausência indica monolito.
- **Onde está a lógica de negócio?** Dentro de rotas/controllers? Misturada com SQL?
- **Há um entry point claro?** (`app.py`, `src/app.js`, `main.go`…)
- **Há "God Class"/"God File"?** Um único arquivo/classe que faz roteamento + DB +
  regras + formatação.

Classifique a arquitetura em um espectro:

- **Monolítica / sem camadas** — tudo em poucos arquivos, sem separação.
- **Parcialmente organizada** — existem algumas pastas (`models/`, `routes/`), mas a
  lógica vaza entre camadas (ex: regra de negócio dentro das rotas).
- **MVC adequado** — Models, Views/Routes e Controllers bem separados (alvo).

## 6. Contagem de arquivos

Conte apenas arquivos-fonte reais analisados. Exclua: `node_modules/`, `venv/`,
`.git/`, `__pycache__/`, `dist/`, `build/`, `*.db`, `*.sqlite`, lockfiles.

## 7. Saída da Fase 1

Preencha o bloco `PHASE 1: PROJECT ANALYSIS` do SKILL.md com os dados coletados e siga
para a Fase 2. Não modifique nenhum arquivo nesta fase.
