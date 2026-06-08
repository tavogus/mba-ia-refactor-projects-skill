```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
Date:    2026-06-08

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 3 | LOW: 3
```

## Findings

### [CRITICAL] SQL Injection / queries não parametrizadas
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-166, 174, 280, 289-297
Description: Praticamente todas as queries são montadas concatenando input do usuário
             diretamente na string SQL (ex: `"SELECT * FROM produtos WHERE id = " + str(id)`;
             login com `email`/`senha` concatenados; busca com `LIKE '%" + termo + "%'`).
Impact: Injeção de SQL — autenticação contornável, vazamento, alteração e destruição
        de todo o banco.
Recommendation: Usar queries parametrizadas com placeholders `?` em toda a camada de
             dados (playbook P1).

### [CRITICAL] Endpoint de execução de SQL arbitrário + reset de banco sem auth
File: app.py:47-57 (`/admin/reset-db`), app.py:59-78 (`/admin/query`)
Description: `/admin/query` executa qualquer SQL enviado no body; `/admin/reset-db`
             apaga todas as tabelas. Ambos sem autenticação.
Impact: RCE de SQL e destruição total dos dados por qualquer cliente anônimo.
Recommendation: Remover o endpoint de SQL arbitrário (não há versão segura). Operações
             administrativas devem ser ações específicas e autenticadas (P5).

### [CRITICAL] Credenciais / segredos hardcoded
File: app.py:7 (`SECRET_KEY = 'minha-chave-super-secreta-123'`)
Description: SECRET_KEY fixa no código-fonte; DEBUG habilitado.
Impact: Segredo versionado vaza em qualquer acesso ao repositório; permite forjar
        sessões/tokens.
Recommendation: Mover para `config/settings.py` lendo de variáveis de ambiente (P2).

### [CRITICAL] Senhas armazenadas e comparadas em texto puro
File: models.py:105-120 (`login_usuario`), models.py:122-131 (`criar_usuario`), database.py:75-83 (seed)
Description: Senhas gravadas sem hash e a autenticação compara `senha == input` via SQL.
Impact: Vazamento do banco expõe todas as senhas em claro.
Recommendation: Hash com `werkzeug.security.generate_password_hash` /
             `check_password_hash` (P4).

### [CRITICAL] Exposição de dados sensíveis nas respostas
File: controllers.py:285-289 (`/health` retorna `secret_key`/`debug`), models.py:83/99 e controllers.py:128-132 (`/usuarios` retorna campo `senha`)
Description: O hash/senha do usuário é serializado em `GET /usuarios` e o `SECRET_KEY`
             é devolvido em `GET /health`.
Impact: Vaza credenciais e o segredo da aplicação para qualquer consumidor da API.
Recommendation: Remover campos sensíveis da serialização (AP-06).

### [HIGH] God File — models.py concentra dados, regra e formatação de 4 domínios
File: models.py:1-315
Description: Um único arquivo cobre produtos, usuários, pedidos e relatório, misturando
             SQL, regra de negócio (cálculo de total/desconto) e montagem de DTO.
Impact: Impossível testar em isolamento; qualquer mudança afeta tudo.
Recommendation: Separar em models por domínio + controllers + service (P3).

### [HIGH] Lógica de negócio e efeitos colaterais presos no Controller
File: controllers.py:208-210, 247-250
Description: Envio de email/SMS/push e notificações de status estão embutidos no
             controller como `print`, misturando orquestração HTTP, regra e efeito.
Impact: Acoplamento forte; impossível reusar/testar a regra de pedido sem disparar
        os efeitos.
Recommendation: Extrair para um `NotificationService` injetado (P6).

### [HIGH] Estado global mutável — conexão única de DB compartilhada
File: database.py:4-11
Description: `db_connection` global reaproveitada entre requests com
             `check_same_thread=False`.
Impact: Condições de corrida e vazamento de estado entre requisições.
Recommendation: Conexão por request (Flask `g` + teardown) ou pool (P11).

### [HIGH] DEBUG ligado em "produção"
File: app.py:8, app.py:88 (`debug=True`)
Description: Modo debug do Flask habilitado; `/health` reporta `ambiente: producao`.
Impact: Debugger interativo e stack traces expostos — risco de segurança.
Recommendation: Flag de debug via env var, default desligado (P2, AP-11).

### [MEDIUM] Query N+1 na listagem de pedidos
File: models.py:187-199, 219-231
Description: Para cada pedido faz-se uma query de itens e, por item, uma query de
             produto, dentro de loops aninhados.
Impact: Número de idas ao banco cresce linearmente com pedidos×itens.
Recommendation: Substituir por JOIN único e agrupar em memória (P7).

### [MEDIUM] Validação duplicada e ausente de paginação
File: controllers.py:28-54 vs 72-90 (validação de produto duplicada em create/update); controllers.py:5-12, 128-132 (listagens sem paginação)
Description: As mesmas regras de validação são copiadas entre criar/atualizar produto;
             listagens retornam a tabela inteira.
Impact: Duplicação divergente e gargalo conforme o volume cresce.
Recommendation: Validador único por recurso (P8) e paginação nas listagens.

### [MEDIUM] Código duplicado entre listagens de pedidos
File: models.py:171-201 (`get_pedidos_usuario`) vs models.py:203-233 (`get_todos_pedidos`)
Description: As duas funções são quase idênticas, diferindo só pelo filtro.
Impact: Manutenção em dobro e risco de divergência.
Recommendation: Unificar em uma função parametrizada (P7/AP-15).

### [LOW] Magic numbers no cálculo de desconto
File: models.py:256-262
Description: Limiares (10000, 5000, 1000) e percentuais (0.1, 0.05, 0.02) soltos.
Impact: Intenção obscura, difícil ajustar com segurança.
Recommendation: Extrair para constantes nomeadas (P12).

### [LOW] Logging via print
File: controllers.py:8, 11, 57, 61, 179, 182, 208-210, 219, 248, 250; app.py:56, 83-85
Description: `print()` usado como log de aplicação, sem níveis nem destino configurável.
Impact: Saída poluída, sem severidade, difícil de operar.
Recommendation: Usar o módulo `logging` com níveis (P12).

### [LOW] Imports/efeitos não usados e detalhes de qualidade
File: models.py:2 (`import sqlite3` sem uso direto), controllers.py:3 (`get_db` importado e usado só no health)
Description: Imports desnecessários e responsabilidades misturadas em pequenos pontos.
Impact: Ruído cognitivo e sinais de baixa manutenção.
Recommendation: Limpar imports mortos e isolar acesso a dados nos models (P12).

```
================================
Total: 15 findings
================================
```
