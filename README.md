# Skill de Auditoria e Refatoração Arquitetural — `refactor-arch`

Este repositório entrega uma **Claude Code Skill** (`refactor-arch`) que analisa, audita
e refatora qualquer projeto de backend para o padrão **MVC**, de forma agnóstica de
tecnologia. A skill foi aplicada a três projetos legados (2× Python/Flask, 1× Node/Express)
e os três foram refatorados e validados.

> O enunciado original do desafio está preservado em [`CHALLENGE.md`](CHALLENGE.md).

## Sumário

- [A) Análise Manual](#a-análise-manual)
- [B) Construção da Skill](#b-construção-da-skill)
- [C) Resultados](#c-resultados)
- [D) Como Executar](#d-como-executar)

---

## A) Análise Manual

Antes de construir a skill, li o código dos três projetos e documentei os problemas de
maior impacto arquitetural. A escala de severidade segue o enunciado (CRITICAL / HIGH /
MEDIUM / LOW). Os relatórios completos gerados pela skill estão em [`reports/`](reports/).

### Projeto 1 — `code-smells-project` (Python/Flask, API de E-commerce)

Monólito em 4 arquivos (`app.py`, `controllers.py`, `models.py`, `database.py`), ~780 linhas.

| # | Problema | Severidade | Local | Por que é relevante |
|---|---|---|---|---|
| 1 | **SQL Injection** — queries montadas por concatenação de input | CRITICAL | `models.py:28,47,110,140,280,289` | Autenticação contornável (`' OR '1'='1`), vazamento/destruição de dados |
| 2 | **Endpoint `/admin/query`** executa SQL arbitrário do body + `/admin/reset-db` sem auth | CRITICAL | `app.py:47-78` | RCE de SQL e destruição total do banco por anônimo |
| 3 | **SECRET_KEY hardcoded** e `DEBUG=True` | CRITICAL | `app.py:7-8` | Segredo versionado; debugger exposto |
| 4 | **Senhas em texto puro**, login compara `senha == input` via SQL | CRITICAL | `models.py:105-131`, `database.py:75-83` | Vazamento do banco expõe todas as senhas |
| 5 | **Dados sensíveis na resposta** — `senha` em `/usuarios`, `secret_key` em `/health` | CRITICAL | `controllers.py:128-132,285-289` | Vaza credenciais e o segredo da app |
| 6 | **God File** — `models.py` mistura dados+regra+formatação de 4 domínios | HIGH | `models.py:1-315` | Impossível testar isoladamente |
| 7 | **Efeitos colaterais no controller** (email/SMS/push como `print`) | HIGH | `controllers.py:208-210,247-250` | Acoplamento; regra de pedido não testável |
| 8 | **Estado global mutável** — conexão única com `check_same_thread=False` | HIGH | `database.py:4-11` | Race conditions entre requests |
| 9 | **Query N+1** na listagem de pedidos (loops aninhados de query) | MEDIUM | `models.py:187-199,219-231` | Gargalo cresce com pedidos×itens |
| 10 | **Validação duplicada** (create vs update) e listagens sem paginação | MEDIUM | `controllers.py:28-90` | Duplicação divergente, gargalo |
| 11 | **Código duplicado** entre `get_pedidos_usuario`/`get_todos_pedidos` | MEDIUM | `models.py:171-233` | Manutenção em dobro |
| 12 | **Magic numbers** nas faixas de desconto | LOW | `models.py:256-262` | Intenção obscura |
| 13 | **Logging via `print`** em todo o fluxo | LOW | `controllers.py` (vários) | Sem níveis nem destino |

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express, "Frankenstein LMS")

3 arquivos (`app.js`, `AppManager.js`, `utils.js`), ~155 linhas. Domínio: e-learning com checkout.

| # | Problema | Severidade | Local | Por que é relevante |
|---|---|---|---|---|
| 1 | **Credenciais hardcoded** (`dbPass`, `pk_live_...`, `smtpUser`) | CRITICAL | `utils.js:1-6` | Chave de pagamento *live* versionada |
| 2 | **Número do cartão + chave do gateway logados no console** | CRITICAL | `AppManager.js:45` | Vazamento de PCI/segredo em logs |
| 3 | **God Class** — `AppManager` faz DB + rotas + pagamento + relatório | CRITICAL | `AppManager.js:1-141` | Zero separação de responsabilidades |
| 4 | **Hash de senha caseiro** (`badCrypto`, loop base64, 10 chars) | HIGH | `utils.js:17-23` | Trivialmente reversível, sem salt |
| 5 | **Callback hell** (4 níveis) no checkout, sem transação | HIGH | `AppManager.js:37-78` | Ilegível; estado parcial inconsistente |
| 6 | **Estado global mutável** (`globalCache`, `totalRevenue`) | HIGH | `utils.js:9-10` | Vazamento de estado entre requests |
| 7 | **API sqlite3 por callback (deprecada)** + `sqlite3.verbose()` em prod | HIGH | `AppManager.js` (vários) | Substituir por async/await/promisify |
| 8 | **N+1 + coordenação manual de contadores** no relatório | MEDIUM | `AppManager.js:80-129` | Race-prone, explosão de queries |
| 9 | **DELETE deixa órfãos** (sem cascade) — o código admite isso | MEDIUM | `AppManager.js:131-137` | Inconsistência referencial |
| 10 | **Validação de pagamento falsa** (`card.startsWith("4")`) + DB `:memory:` | MEDIUM | `AppManager.js:7,46` | Dados perdidos no restart |
| 11 | **Nomes crípticos** (`u`, `e`, `p`, `cid`, `cc`) | LOW | `AppManager.js:29-34` | Baixa legibilidade |
| 12 | **Formato de resposta inconsistente** (string vs JSON) e `console.log` como log | LOW | vários | Sem padronização |

### Projeto 3 — `task-manager-api` (Python/Flask + SQLAlchemy, parcialmente organizado)

Já possui `models/`, `routes/`, `services/`, `utils/` — mas **sem camada de controllers** e
com regra de negócio nas rotas. ~1149 linhas.

| # | Problema | Severidade | Local | Por que é relevante |
|---|---|---|---|---|
| 1 | **SECRET_KEY hardcoded** | CRITICAL | `app.py:13` | Segredo versionado |
| 2 | **Hash de senha com MD5** (deprecado para senhas) | CRITICAL | `models/user.py:29,32` | MD5 é quebrável |
| 3 | **Hash de senha exposto nas respostas** (`password` em `to_dict`) | CRITICAL | `models/user.py:21-25` | Vaza credenciais em `/users` e `/login` |
| 4 | **Credenciais SMTP hardcoded** (`senha123`) | HIGH | `services/notification_service.py:9-10` | Segredo versionado |
| 5 | **Regra de negócio nas rotas** (sem controllers) | HIGH | `task_routes.py`, `report_routes.py` | Rotas "gordas", não testáveis |
| 6 | **Token JWT falso** (`fake-jwt-token-<id>`) | HIGH | `user_routes.py:210` | Autenticação inexistente |
| 7 | **Query N+1** em `get_tasks` e `summary_report` | MEDIUM | `task_routes.py:41-57`, `report_routes.py:53-68` | Explosão de queries |
| 8 | **Lógica de "overdue" duplicada** 6× (existindo `Task.is_overdue`) | MEDIUM | 6 locais | Divergência silenciosa |
| 9 | **`except:` genérico** engolindo erros (9+ pontos) | MEDIUM | `task_routes.py:62,236`… | Mascara bugs |
| 10 | **`db.create_all()` no import** | MEDIUM | `app.py:30-31` | Efeito colateral no import |
| 11 | **Imports mortos** (`json,os,sys,time,math,hashlib`) | LOW | vários | Ruído |
| 12 | **`if x: return True else: return False`** e magic numbers | LOW | `models/`, `utils/` | Legibilidade |

---

## B) Construção da Skill

### Estrutura

A skill vive em `.claude/skills/refactor-arch/` e é composta por um **orquestrador**
(`SKILL.md`) e **5 arquivos de referência** que carregam o conhecimento de domínio,
um por área obrigatória do desafio:

```
.claude/skills/refactor-arch/
├── SKILL.md                              # orquestrador das 3 fases + princípios invioláveis
└── references/
    ├── 01-project-analysis.md            # heurísticas de detecção (linguagem/framework/DB/arquitetura)
    ├── 02-anti-patterns.md               # catálogo de anti-patterns (+ APIs deprecated)
    ├── 03-report-template.md             # formato padronizado do relatório (Fase 2)
    ├── 04-architecture-guidelines.md     # regras do MVC alvo (Models/Views/Controllers/Services/Config)
    └── 05-refactoring-playbook.md        # padrões de transformação com exemplos antes/depois
```

**Decisão de design central:** `SKILL.md` é fino e diz *o que fazer e em que ordem*; o
conhecimento pesado fica nas referências, lidas sob demanda em cada fase. Isso mantém o
prompt principal enxuto e torna a skill fácil de evoluir (basta editar uma referência).

### Anti-patterns incluídos (e por quê)

O catálogo tem **19 anti-patterns** + uma tabela de **APIs deprecated**, distribuídos por
severidade. Foram escolhidos por serem os de maior impacto e os efetivamente presentes
nos projetos-alvo:

- **CRITICAL** (AP-01..06): SQLi, segredos hardcoded, God Class, senha em texto/hash
  inseguro, endpoint administrativo perigoso, exposição de dados sensíveis. → segurança e
  violação total de responsabilidades.
- **HIGH** (AP-07..11): regra na camada errada, estado global mutável, efeitos sem DI,
  callback hell/sem transação, debug em produção. → manutenção/testabilidade e SOLID.
- **MEDIUM** (AP-12..16): N+1, validação ausente/duplicada, erro genérico, duplicação,
  paginação/integridade referencial. → performance e padronização.
- **LOW** (AP-17..19): magic numbers, `print` como log, nomes ruins/dead code.
- **Deprecated**: MD5/SHA1 e hashing caseiro para senha, `datetime.utcnow()`, API sqlite3
  por callback, `var`, `db.create_all()` no import, CORS `*`, `app.run()` em produção — cada
  um com o **equivalente moderno** recomendado.

### Como garanti que a skill é agnóstica de tecnologia

1. **Detecção orientada a manifesto + sintaxe**, nunca por suposição: a Fase 1 lê
   `requirements.txt`/`package.json`/`pom.xml`/… e confirma pela sintaxe.
2. **Anti-patterns descritos por *sinais de detecção*** (ex: "query SQL concatenada com
   input", "callback aninhado 3+ níveis"), não por uma API específica de framework.
3. **Playbook bilíngue**: cada transformação tem exemplo em Python/Flask **e** Node/Express,
   sempre deixando claro o *princípio* genérico por trás.
4. **Guidelines de MVC em termos de responsabilidades** (Models/Views/Controllers/Services/
   Config), com regra explícita de **adaptação ao contexto** (monólito × projeto já
   organizado).
5. **Prova empírica**: a mesma skill rodou nos 3 projetos (2 stacks diferentes, 2 níveis de
   organização) e atingiu todos os critérios de aceite.

### Desafios encontrados e como resolvi

- **Preservar contrato vs. corrigir bug de segurança.** Para SQLi/senhas, mantive os
  *endpoints e formatos de resposta*, mudando só a implementação interna. Os endpoints
  administrativos perigosos (`/admin/query`) foram **removidos** — não há versão "segura" de
  executar SQL arbitrário.
- **`werkzeug` sem `scrypt` neste build do Python 3.9.** O default do
  `generate_password_hash` (scrypt) quebrava. Solução: fixar `method="pbkdf2:sha256"`. Isso
  virou uma nota explícita no playbook/execução.
- **Projeto 3 já tinha camadas.** A skill precisou *não destruir* o que estava bom e focar
  na camada faltante (Controllers/Services), extração de config e centralização de erros.
- **Adaptação de quantidade de transformação por projeto** — o monólito do Projeto 1 exigiu
  a árvore MVC inteira; o Projeto 3 exigiu refinamento cirúrgico.

---

## C) Resultados

### Resumo dos relatórios de auditoria

| Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total | Relatório |
|---|---|:--:|:--:|:--:|:--:|:--:|---|
| 1 — code-smells-project | Python/Flask | 5 | 4 | 3 | 3 | **15** | [audit-project-1.md](reports/audit-project-1.md) |
| 2 — ecommerce-api-legacy | Node/Express | 3 | 4 | 4 | 3 | **14** | [audit-project-2.md](reports/audit-project-2.md) |
| 3 — task-manager-api | Python/Flask | 3 | 3 | 4 | 3 | **13** | [audit-project-3.md](reports/audit-project-3.md) |

### Antes / Depois da estrutura

**Projeto 1 — de monólito para MVC completo:**
```
ANTES                          DEPOIS
app.py                         app.py                       (entry point)
controllers.py   (292 l)       src/
models.py        (314 l)       ├── config/settings.py       (segredos via env)
database.py                    ├── database.py              (conexão por request via g)
                               ├── models/{produto,usuario,pedido}_model.py
                               ├── controllers/{produto,usuario,pedido,relatorio}_controller.py
                               ├── services/notification_service.py
                               ├── validators.py
                               ├── middlewares/error_handler.py
                               ├── views/routes.py          (roteamento fino)
                               └── app.py                   (composition root + DI)
```

**Projeto 2 — God Class quebrada em camadas:**
```
ANTES                          DEPOIS
src/app.js                     src/
src/AppManager.js (141 l)      ├── config/settings.js       (process.env)
src/utils.js                   ├── database/db.js           (sqlite promisificado + seed)
                               ├── models/{user,course,enrollment,payment,audit}Model.js
                               ├── services/{payment,cache}Service.js
                               ├── controllers/{checkout,report,user}Controller.js
                               ├── routes/index.js          (express.Router fino)
                               ├── middlewares/errorHandler.js
                               └── app.js                   (composition root)
```

**Projeto 3 — camada de Controllers introduzida, rotas emagrecidas:**
```
ANTES                          DEPOIS (adições/alterações)
models/ routes/ services/      + config/settings.py         (SECRET_KEY/SMTP via env)
utils/  app.py                 + controllers/{task,user,report,category}_controller.py
routes/*  (300/211/223 l)      + middlewares/error_handler.py
                               ~ routes/* emagrecidas (300→44, 211→44, 223→39 l)
                               ~ models/user.py: pbkdf2, password fora do to_dict()
                               ~ app.py: create_app() factory
```

### Checklist de validação (preenchido — idêntico nos 3 projetos)

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (Python×2, JavaScript×1)
- [x] Framework detectado corretamente (Flask 3.1.1 / Express 4 / Flask 3.0+SQLAlchemy)
- [x] Domínio descrito corretamente (E-commerce / LMS-checkout / Task Manager)
- [x] Nº de arquivos analisados condiz (4 / 3 / 10)

**Fase 2 — Auditoria**
- [x] Relatório segue o template definido nas referências
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings (15 / 14 / 13)
- [x] Detecção de APIs deprecated incluída
- [x] Skill pausa e pede confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura de diretórios segue padrão MVC
- [x] Config extraída para módulo (sem hardcoded; via env vars)
- [x] Models abstraem os dados (queries parametrizadas)
- [x] Views/Routes separadas para roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado
- [x] Entry point claro (composition root)
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente

### Logs de validação (pós-refatoração)

**Projeto 1 (Flask test client — 13 endpoints):** todos `2xx`, exceto `POST /login` com
senha errada → `401` (comportamento esperado). SQLi de bypass no login → `401`. `/usuarios`
sem campo `senha`; `/health` sem `secret_key`.
```
GET / 200 | GET /health 200 | GET /produtos 200 | GET /produtos/1 200
GET /produtos/busca 200 | POST /produtos 201 | GET /usuarios 200
POST /login (ok) 200 | POST /login (errada) 401 | POST /pedidos 201
GET /pedidos 200 | GET /pedidos/usuario/2 200 | GET /relatorios/vendas 200
```

**Projeto 2 (servidor real, porta 3000):**
```
POST /api/checkout (card 4xxx) -> 200    POST /api/checkout (card 5xxx) -> 400
GET  /api/admin/financial-report -> 200  DELETE /api/users/1 -> 200
grep pk_live / senha_super_secreta / console.log(card) em src/ -> nenhum
```

**Projeto 3 (Flask test client — 13 endpoints):** todos `2xx`/`201`. `POST /login`
(`joao@email.com`/`1234`) → `200`. Respostas de `/users` e `/login` **sem** `password`.
`grep super-secret-key-123 / senha123 / hashlib.md5` no código → nenhum.
```
GET / 200 | GET /health 200 | GET /tasks 200 | GET /tasks/1 200 | POST /tasks 201
GET /tasks/search 200 | GET /tasks/stats 200 | GET /users 200 | GET /users/1 200
POST /login 200 | GET /reports/summary 200 | GET /reports/user/1 200 | GET /categories 200
```

### Como a skill se comportou em stacks diferentes

- **Detecção** funcionou nas duas linguagens via manifesto + sintaxe.
- **Catálogo por sinais** pegou os mesmos conceitos (SQLi, segredos, N+1, God Class) em
  Python e em Node, sem regras específicas de framework.
- **Adaptação ao contexto** foi visível: monólitos (1 e 2) viraram a árvore MVC inteira; o
  projeto já organizado (3) recebeu apenas a camada faltante e refinos cirúrgicos — exatamente
  o comportamento prescrito nas guidelines.

---

## D) Como Executar

### Pré-requisitos

- **Claude Code** instalado e configurado.
- **Python 3.9+** (projetos 1 e 3) e **Node.js 18+** (projeto 2).

### Executar a skill

A skill está em `.claude/skills/refactor-arch/` dentro de **cada** projeto. Basta entrar no
projeto e invocá-la:

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

A skill roda 3 fases: imprime a análise (Fase 1), gera o relatório de auditoria e **pede
confirmação** (Fase 2) e, após o `y`, refatora e valida (Fase 3). O relatório de cada
projeto é salvo em `reports/audit-project-{1,2,3}.md`.

### Validar manualmente que a refatoração funciona

**Projeto 1 (Flask):**
```bash
cd code-smells-project
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python app.py            # sobe em http://localhost:5000
curl http://localhost:5000/health  # {"status":"ok",...}
curl http://localhost:5000/produtos
```

**Projeto 2 (Express):**
```bash
cd ecommerce-api-legacy
npm install
npm start                          # sobe em http://localhost:3000
curl -X POST http://localhost:3000/api/checkout \
  -H 'Content-Type: application/json' \
  -d '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"x","c_id":2,"card":"4111222233334444"}'
curl http://localhost:3000/api/admin/financial-report
```

**Projeto 3 (Flask/SQLAlchemy):**
```bash
cd task-manager-api
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py           # popula o banco
.venv/bin/python app.py            # sobe em http://localhost:5000
curl http://localhost:5000/tasks
curl -X POST http://localhost:5000/login \
  -H 'Content-Type: application/json' -d '{"email":"joao@email.com","password":"1234"}'
```

Os segredos saem de variáveis de ambiente — copie `.env.example` para `.env` e ajuste antes
de subir em produção. `.venv/`, `node_modules/` e `*.db` são ignorados pelo git.
