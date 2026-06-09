# Referência 02 — Catálogo de Anti-Patterns (Fase 2)

Catálogo agnóstico de tecnologia. Para cada item: **sinais de detecção** concretos e
**severidade**. Varra o código procurando os sinais. Cada ocorrência vira um finding
com `arquivo:linha`.

## Escala de severidade

- **CRITICAL** — Falha grave de arquitetura/segurança: impede funcionamento correto,
  expõe dados sensíveis (credenciais hardcoded, SQL Injection) ou viola completamente
  a separação de responsabilidades (God Class com DB + regra + roteamento juntos).
- **HIGH** — Forte violação de MVC/SOLID que dificulta muito manutenção e testes:
  regra de negócio pesada presa em Controller, acoplamento forte sem injeção de
  dependência, estado global mutável.
- **MEDIUM** — Padronização, duplicação ou performance moderada: queries N+1, uso
  inadequado de middleware, validações ausentes nas rotas, except genérico.
- **LOW** — Legibilidade: nomes ruins, magic numbers, prints como log, imports mortos.

---

## CRITICAL

### AP-01 — SQL Injection / queries não parametrizadas
**Sinais:** concatenação ou interpolação de input em SQL —
`"... WHERE id = " + str(id)`, `f"... LIKE '%{termo}%'"`, template strings com
variáveis dentro de `execute(...)`. Qualquer query montada com `+`, `%`, `.format()`
ou f-string em vez de placeholders (`?`, `%s`, `:param`).
**Por quê:** permite injeção de SQL, vazamento e destruição de dados.

### AP-02 — Credenciais / segredos hardcoded
**Sinais:** `SECRET_KEY = "..."`, senhas, API keys (`pk_live_...`, `sk_...`), strings
de conexão, `dbPass`, `paymentGatewayKey`, `email_password` literais no código.
**Por quê:** segredo versionado vaza em qualquer leak do repositório.

### AP-03 — God Class / God File / God Method
**Sinais:** um único arquivo/classe que faz **roteamento + acesso a dados + regra de
negócio + formatação** ao mesmo tempo; arquivo com centenas de linhas cobrindo vários
domínios; método único com muitos níveis de responsabilidade.
**Por quê:** impossível testar em isolamento; qualquer mudança arrisca tudo.

### AP-04 — Senhas em texto puro ou hash inseguro
**Sinais:** senha salva sem hash (`INSERT ... senha ...` com valor cru); comparação
`senha == input`; uso de `md5`/`sha1` para senha; hashing caseiro
(loops de `base64`, `badCrypto`).
**Por quê:** vazamento do banco expõe todas as senhas; MD5/SHA1 são quebráveis.
**Correto:** `bcrypt`, `argon2` ou `werkzeug.security.generate_password_hash`.

### AP-05 — Endpoint administrativo perigoso / execução arbitrária
**Sinais:** rota que executa SQL arbitrário vindo do body (`/admin/query` com
`execute(request.sql)`), reset de banco sem auth (`/admin/reset-db`), `eval`/`exec`
de input.
**Por quê:** RCE/SQL arbitrário; qualquer um apaga ou lê o banco inteiro.

### AP-06 — Exposição de dados sensíveis na resposta
**Sinais:** campo `senha`/`password`/`pass`/`secret_key` dentro de `to_dict()`,
serializers ou respostas JSON; `/health` retornando `secret_key`/`debug`.
**Por quê:** vaza credenciais e segredos para qualquer cliente da API.

---

## HIGH

### AP-07 — Lógica de negócio na camada errada (Fat Controller / Fat Route / Fat Model)
**Sinais:** rota/controller que faz queries diretas, calcula regras (descontos,
relatórios, agregações), monta DTOs e dispara efeitos colaterais; OU model que, além
de dados, faz validação de request e formatação de resposta.
**Por quê:** mistura HTTP, regra e dados; impede reuso e teste unitário.

### AP-08 — Estado global mutável / singleton mutável
**Sinais:** `globalCache = {}`, `totalRevenue = 0` no escopo de módulo e mutados em
runtime; conexão de DB global única reaproveitada entre requests
(`db_connection = None` + `global`); `check_same_thread=False`.
**Por quê:** condições de corrida, vazamento de estado entre requests, difícil testar.

### AP-09 — Efeitos colaterais acoplados / sem injeção de dependência
**Sinais:** envio de email/SMS/push escrito inline na rota (até como `print`); cliente
externo instanciado dentro do método; dependências concretas criadas com `new`/import
direto sem possibilidade de mock.
**Por quê:** acoplamento forte, impossível testar sem disparar o efeito real.

### AP-10 — Callback hell / fluxo assíncrono manual sem transação
**Sinais (Node):** callbacks aninhados 3+ níveis (`db.get(... => db.run(... => ...))`);
coordenação manual de paralelismo com contadores (`pending--; if(pending===0)`);
sequência de escritas (enrollment → payment → audit) **sem transação**.
**Por quê:** ilegível, propenso a race condition e a estado parcial inconsistente.

### AP-11 — Modo debug / configuração de desenvolvimento em produção
**Sinais:** `DEBUG = True`, `app.run(debug=True)`, `app.config["DEBUG"]=True`,
verbose logging ligado, CORS liberado para `*` sem necessidade.
**Por quê:** debugger expõe stack traces e console interativo; risco de segurança.

---

## MEDIUM

### AP-12 — Query N+1
**Sinais:** loop que executa uma query por iteração — `for row in rows: cursor.execute(
... WHERE id = row.x)`; em ORM, `for t in tasks: User.query.get(t.user_id)`; relatórios
que fazem uma query por entidade dentro de outra.
**Por quê:** explode o número de idas ao banco; gargalo de performance.
**Correto:** JOIN, `IN (...)`, eager loading (`joinedload`), ou agregação no SQL.

### AP-13 — Validação ausente ou duplicada nas rotas
**Sinais:** mesma cadeia de `if not dados: ... if "x" not in dados` copiada em vários
handlers; ausência de validação de tipos/limites; validação misturada com regra.
**Por quê:** inconsistência, duplicação, regras divergindo entre create/update.
**Correto:** schema/validador único (marshmallow, pydantic, Joi, zod) reutilizado.

### AP-14 — Tratamento de erro genérico / silencioso
**Sinais:** `except:` ou `except Exception` retornando 500 genérico engolindo a causa;
`catch` vazio; erros não logados com contexto; cada handler com seu próprio try/except
repetido.
**Por quê:** mascara bugs, dificulta diagnóstico; deveria ser centralizado.

### AP-15 — Código duplicado / DRY violado
**Sinais:** funções quase idênticas (`get_pedidos_usuario` vs `get_todos_pedidos`);
serialização manual repetida; mesma lógica de "overdue"/cálculo copiada em 3+ lugares
em vez de reutilizar um método existente.
**Por quê:** manutenção multiplicada, divergência silenciosa de comportamento.

### AP-16 — Ausência de paginação / integridade referencial
**Sinais:** endpoints de listagem retornando a tabela inteira sem `limit/offset`;
`DELETE` que deixa registros órfãos (sem cascade/FK), inclusive admitindo isso.
**Por quê:** performance e consistência de dados degradam com volume.

---

## LOW

### AP-17 — Magic numbers / strings mágicas
**Sinais:** números/limiares soltos sem nome (`if faturamento > 10000`, `* 0.1`,
`priority 1..5`, status como strings repetidas).
**Por quê:** intenção obscura, difícil de ajustar com segurança.

### AP-18 — Logging via print / console.log
**Sinais:** `print(...)`/`console.log(...)` para log de aplicação; sem níveis
(info/warn/error); logs ruidosos em fluxo normal.
**Por quê:** sem níveis, sem destino configurável, polui a saída.

### AP-19 — Nomes ruins / imports mortos / dead code
**Sinais:** variáveis crípticas (`u`, `e`, `p`, `cid`, `cc`); imports não usados
(`import os, sys, json, time` sem uso); funções nunca chamadas; `if x: return True else
return False` em vez de `return x`.
**Por quê:** ruído cognitivo, sinal de copy-paste e baixa manutenção.

---

## APIs DEPRECATED (verificação obrigatória)

Sempre verifique uso de APIs obsoletas e recomende o equivalente moderno.

| Deprecated / obsoleto | Onde aparece | Equivalente moderno | Severidade |
|---|---|---|---|
| `hashlib.md5` / `sha1` para senha | hashing de senha | `bcrypt`, `argon2`, `werkzeug.security` | HIGH |
| Hashing caseiro (`badCrypto`, loop base64) | utils | lib de hashing testada | HIGH |
| `datetime.utcnow()` (deprecado no Python 3.12+) | timestamps | `datetime.now(datetime.UTC)` | LOW |
| sqlite3 callback API (Node) | acesso a dados | `better-sqlite3` ou wrapper `promisify`/async-await | MEDIUM |
| `var` (JS) | declarações | `const`/`let` | LOW |
| `sqlite3.verbose()` em produção | init de DB | remover em produção | LOW |
| `db.create_all()` na importação do módulo | bootstrap | migrations (Alembic/Flask-Migrate) ou factory | MEDIUM |
| CORS `*` sem restrição | config | origins explícitas | MEDIUM |
| `request.get_json()` sem `silent`/validação | parsing | validação de schema | LOW |
| `app.run()` como servidor de produção | entry point | gunicorn/uvicorn/WSGI server | MEDIUM |

> Adapte a tabela à stack detectada — se for outra linguagem, aplique o mesmo
> princípio: identificar API obsoleta e apontar o substituto atual.

---

## Como usar este catálogo na Fase 2

1. Percorra **todas** as seções (CRITICAL → LOW + deprecated).
2. Para cada sinal encontrado, crie um finding (ver `03-report-template.md`).
3. Não invente findings: cada um precisa de `arquivo:linha` real.
4. Garanta o mínimo: ≥ 5 findings e ≥ 1 CRITICAL/HIGH. Se ficar abaixo, releia —
   segredos hardcoded, SQLi, lógica em rota e N+1 são quase sempre presentes em legado.
