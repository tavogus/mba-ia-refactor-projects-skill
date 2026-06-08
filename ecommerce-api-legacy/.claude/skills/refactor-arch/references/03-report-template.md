# Referência 03 — Template do Relatório de Auditoria (Fase 2)

O relatório da Fase 2 deve seguir **exatamente** este formato. Salve em
`reports/audit-project-<n>.md` e imprima no terminal.

## Estrutura

````markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome-do-projeto>
Stack:   <Linguagem + Framework>
Files:   <N> analyzed | ~<linhas> lines of code
Date:    <YYYY-MM-DD>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <Nome do anti-pattern>
File: <arquivo>:<linha(s)>
Description: <o que está errado, objetivamente>
Impact: <consequência prática>
Recommendation: <como corrigir>

### [CRITICAL] <...>
...

### [HIGH] <...>
...

### [MEDIUM] <...>
...

### [LOW] <...>
...

================================
Total: <N> findings
================================
````

## Regras de preenchimento

1. **Ordem por severidade**: todos os CRITICAL primeiro, depois HIGH, MEDIUM e LOW.
2. **Um finding por ocorrência relevante**. Se o mesmo anti-pattern aparece em vários
   pontos (ex: SQLi em 10 funções), agrupe em um finding e liste as linhas no campo
   `File:` (ex: `models.py:28, 47, 110, 140`), citando as principais.
3. **`File:` é obrigatório e específico** — sempre `arquivo:linha`. Sem isso o finding
   é inválido.
4. **Description objetiva** — o quê e onde, sem juízo de valor vago.
5. **Impact** — por que importa (segurança, performance, manutenção, correção).
6. **Recommendation** — ação concreta, alinhada ao playbook (`05-refactoring-playbook.md`).
7. **Summary** — a contagem por severidade deve bater com os findings listados.
8. **Total** — número total de findings (= soma do Summary).

## Exemplo preenchido (trecho)

````markdown
### [CRITICAL] SQL Injection / queries não parametrizadas
File: models.py:28, 47, 110, 140, 280
Description: Queries SQL são montadas concatenando input do usuário diretamente
             (ex: "SELECT * FROM produtos WHERE id = " + str(id); login com
             email/senha concatenados).
Impact: Permite injeção de SQL — vazamento, alteração e destruição de dados.
Recommendation: Usar queries parametrizadas com placeholders (?) em toda a camada
             de dados (ver playbook P1).

### [HIGH] Lógica de negócio e efeitos colaterais no Controller
File: controllers.py:208-210, 247-250
Description: Envio de email/SMS/push e notificações de status estão embutidos no
             controller como prints, misturando orquestração HTTP com regra de negócio.
Impact: Acoplamento forte, impossível testar ou reusar a lógica de pedido.
Recommendation: Extrair para um Service de notificação injetado no controller (P6).
````
