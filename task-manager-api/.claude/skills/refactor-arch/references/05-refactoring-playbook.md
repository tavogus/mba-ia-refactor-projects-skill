# Referência 05 — Playbook de Refatoração (Fase 3)

Padrões concretos de transformação, com exemplos **antes/depois**. Cada padrão mapeia
para um ou mais anti-patterns do catálogo (`02-anti-patterns.md`). Os exemplos usam
Python/Flask e Node/Express, mas o **princípio** é agnóstico — aplique o equivalente
na stack detectada.

---

## P1 — Parametrizar queries (cura AP-01 SQL Injection)

**Antes (Python):**
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
```
**Depois:**
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))  # senha conferida com hash, ver P4
```
**Antes (Node):** `db.get("... WHERE id = " + cid, ...)`
**Depois:** `db.get("... WHERE id = ?", [cid], ...)`

Para filtros dinâmicos, monte a cláusula com placeholders e uma lista de parâmetros:
```python
query, params = "SELECT * FROM produtos WHERE 1=1", []
if termo:
    query += " AND (nome LIKE ? OR descricao LIKE ?)"; params += [f"%{termo}%", f"%{termo}%"]
if categoria:
    query += " AND categoria = ?"; params.append(categoria)
cursor.execute(query, params)
```

---

## P2 — Extrair config e segredos para env vars (cura AP-02, AP-11)

**Antes:**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
```
**Depois — `config/settings.py`:**
```python
import os
class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    DB_PATH = os.environ.get("DB_PATH", "loja.db")
settings = Settings()
```
**Node — `config/settings.js`:**
```javascript
module.exports = {
  port: process.env.PORT || 3000,
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || "",
  dbPath: process.env.DB_PATH || "./data.db",
};
```
Acrescente um `.env.example` documentando as variáveis. Nunca commitar segredos reais.

---

## P3 — Quebrar a God Class/God File em camadas (cura AP-03, AP-07)

**Antes:** `AppManager.js` faz `initDb()` + `setupRoutes()` + pagamento + relatório.
`models.py` de 350 linhas com 4 domínios.

**Depois:** separe por responsabilidade e domínio:
```
models/produto_model.py        # só dados de produto (queries parametrizadas)
models/usuario_model.py
models/pedido_model.py
controllers/produto_controller.py   # orquestra caso de uso de produto
controllers/pedido_controller.py
services/notification_service.py    # efeitos colaterais
views/routes.py                     # só roteamento
config/settings.py
app.py                              # composition root
```
Mova cada função para a camada certa: SQL → model; fluxo → controller; efeito → service.

---

## P4 — Hash de senha seguro (cura AP-04 e API deprecated md5/caseiro)

**Antes:**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()   # ou senha salva em texto puro
```
```javascript
function badCrypto(pwd){ /* loop base64 caseiro */ }
```
**Depois (Python):**
```python
from werkzeug.security import generate_password_hash, check_password_hash
def set_password(self, pwd): self.password = generate_password_hash(pwd)
def check_password(self, pwd): return check_password_hash(self.password, pwd)
```
**Depois (Node):**
```javascript
const bcrypt = require('bcrypt');
const hash = await bcrypt.hash(pwd, 10);
const ok = await bcrypt.compare(pwd, hash);
```
> Se não puder adicionar dependência, no mínimo troque por hash com salt da stdlib
> (ex: `hashlib.pbkdf2_hmac`/`scrypt`). Nunca md5/sha1 puro nem texto puro.

---

## P5 — Remover endpoints administrativos perigosos (cura AP-05)

**Antes:** `/admin/query` executa SQL arbitrário do body; `/admin/reset-db` apaga tudo
sem auth.
**Depois:** **remover** o endpoint de SQL arbitrário (não existe versão "segura" dele).
Para operações administrativas legítimas, exigir autenticação/autorização e expor
apenas ações específicas e parametrizadas (ex: um comando de seed protegido), nunca SQL
livre.

---

## P6 — Extrair efeitos colaterais para um Service injetado (cura AP-09)

**Antes (controller):**
```python
print("ENVIANDO EMAIL: Pedido criado ...")
print("ENVIANDO SMS: ...")
```
**Depois — `services/notification_service.py`:**
```python
class NotificationService:
    def order_created(self, pedido_id, usuario_id):
        # email/sms/push reais ou logger; testável e mockável
        logger.info("order_created", extra={"pedido": pedido_id, "user": usuario_id})
```
**Controller** recebe o service por injeção e chama `self.notifications.order_created(...)`.
Idem para `NotificationService` com SMTP: credenciais via config (P2), não hardcoded.

---

## P7 — Eliminar query N+1 (cura AP-12)

**Antes:**
```python
for row in pedidos:
    cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in itens:
        cursor.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```
**Depois — uma query com JOIN (ou IN):**
```python
cursor.execute("""
    SELECT ip.pedido_id, ip.produto_id, ip.quantidade, ip.preco_unitario, p.nome
    FROM itens_pedido ip JOIN produtos p ON p.id = ip.produto_id
    WHERE ip.pedido_id IN ({})""".format(",".join("?"*len(ids))), ids)
# agrupe em memória por pedido_id
```
**ORM (SQLAlchemy):** troque o loop `User.query.get(t.user_id)` por eager loading:
```python
tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
```

---

## P8 — Centralizar validação em schema reutilizável (cura AP-13, AP-15)

**Antes:** blocos `if not dados / if "nome" not in dados / if preco < 0` repetidos em
create e update.
**Depois:** um validador único por recurso:
```python
def validate_produto(data, partial=False):
    errors = []
    if not partial or "nome" in data:
        if len(data.get("nome","")) < 2: errors.append("Nome muito curto")
    if data.get("preco", 0) < 0: errors.append("Preço não pode ser negativo")
    return errors
```
Controllers de create e update chamam o mesmo validador. (Ou marshmallow/pydantic/Joi.)

---

## P9 — Centralizar tratamento de erros (cura AP-14)

**Antes:** cada handler com seu `try/except Exception: return 500`.
**Depois (Flask) — `middlewares/error_handler.py`:**
```python
def register_error_handlers(app):
    @app.errorhandler(Exception)
    def handle(e):
        app.logger.exception(e)
        code = getattr(e, "code", 500)
        return jsonify({"erro": str(e), "sucesso": False}), code
```
**Express:**
```javascript
function errorHandler(err, req, res, next){
  console.error(err);
  res.status(err.status || 500).json({ error: err.message });
}
app.use(errorHandler);
```
Handlers ficam livres do try/except repetido; lançam exceções e o middleware trata.

---

## P10 — Transação para operações multi-passo + async limpo (cura AP-10, AP-16)

**Antes (Node):** insert de enrollment → payment → audit em callbacks aninhados sem
transação; `DELETE` deixando órfãos.
**Depois:** envolva a sequência em transação e use async/await (promisify):
```javascript
await run("BEGIN");
try {
  const enr = await run("INSERT INTO enrollments ...", [userId, cid]);
  await run("INSERT INTO payments ...", [enr.lastID, price, status]);
  await run("INSERT INTO audit_logs ...", [...]);
  await run("COMMIT");
} catch (e) { await run("ROLLBACK"); throw e; }
```
Para `DELETE` com integridade: apague dependentes na mesma transação (ou ative
`FOREIGN KEY ... ON DELETE CASCADE`).

---

## P11 — Remover estado global mutável (cura AP-08)

**Antes:** `let globalCache = {}; let totalRevenue = 0;` no módulo; conexão global única.
**Depois:** encapsule estado em instâncias com tempo de vida controlado (ex: um cache
service injetado), e abra conexões por request ou use um pool — não uma global mutável
compartilhada com `check_same_thread=False`.

---

## P12 — Substituir API deprecated e limpar ruído (cura AP-18, AP-19 + deprecated)

- `print(...)`/`console.log(...)` de aplicação → `logging`/logger com níveis.
- `datetime.utcnow()` → `datetime.now(datetime.UTC)` quando aplicável.
- Remover imports mortos (`import os, sys, json, time` sem uso).
- `if x: return True else: return False` → `return x`.
- Magic numbers → constantes nomeadas (`DISCOUNT_TIERS`, `VALID_STATUSES`).
- `db.create_all()` no import → mover para o entry point/factory ou migrations.

---

## Ordem recomendada de aplicação

1. **Segurança primeiro** (P1 SQLi, P2 segredos, P4 senha, P5 endpoints perigosos,
   P11 estado global) — são os CRITICAL/HIGH.
2. **Estrutura** (P3 camadas, P6 services, P9 error handler, entry point).
3. **Qualidade** (P7 N+1, P8 validação, P10 transação, P12 limpeza).
4. **Validar** boot + endpoints a cada bloco grande; nunca termine com app quebrada.

> Lembre: preservar contratos. A API responde igual — muda só a implementação interna.
