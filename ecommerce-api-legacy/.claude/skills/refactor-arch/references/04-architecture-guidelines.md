# Referência 04 — Guidelines de Arquitetura MVC (Fase 3)

Arquitetura **alvo** da refatoração, agnóstica de tecnologia. MVC adaptado a backends
de API (a "View" de uma API é a camada de roteamento/serialização HTTP).

## As camadas e suas responsabilidades

```
Request → [View/Route] → [Controller] → [Service?] → [Model] → DB
                ↑                                         │
          (de)serialização                          dados/queries
```

### Models (camada de dados)
- **Responsável por:** acesso e persistência de dados, mapeamento de
  tabelas/entidades, queries **parametrizadas**.
- **Pode conter:** validações de invariантes da entidade, métodos de domínio simples.
- **NÃO contém:** objetos `request`/`response`, status HTTP, regras de caso de uso
  complexas, formatação de saída para o cliente.
- **Regra:** toda query parametrizada. Nenhum `senha`/`password` em serialização.

### Views / Routes (camada de apresentação HTTP)
- **Responsável por:** declarar paths e métodos; extrair dados do request; chamar o
  controller; devolver a resposta (status + JSON).
- **NÃO contém:** queries, regras de negócio, cálculos, efeitos colaterais.
- **Regra:** uma rota é "fina" — recebe, delega, responde. Nada de SQL aqui.

### Controllers (camada de orquestração / caso de uso)
- **Responsável por:** orquestrar o fluxo de um caso de uso — validar entrada
  (via schema), chamar models/services na ordem certa, montar o resultado, decidir o
  status de retorno.
- **NÃO contém:** SQL cru nem detalhes de transporte HTTP de baixo nível (idealmente
  recebe dados já extraídos; em frameworks como Flask pode ler `request`, mas delega
  a regra).
- **Regra:** o controller conta a história do caso de uso; os detalhes ficam abaixo.

### Services (opcional, mas recomendado para regra reaproveitável)
- **Responsável por:** regra de negócio que transcende um único endpoint (cálculo de
  relatório, processamento de pagamento, notificações), e integrações externas
  (email/SMS/gateway) atrás de uma interface injetável.
- **Regra:** services são injetados (DI), não instanciados inline em controllers.

### Config (camada de configuração)
- **Responsável por:** centralizar configuração e **segredos via variáveis de
  ambiente** (com defaults seguros para dev). Nada de segredo hardcoded.
- Ex.: `SECRET_KEY`, strings de conexão, chaves de API, flags de debug.

### Middlewares / Error handling
- **Responsável por:** tratamento centralizado de erros (um handler que captura
  exceções e devolve resposta padronizada), CORS, logging.
- **Regra:** elimina o try/except repetido em cada handler.

### Entry point / Composition root
- **Responsável por:** criar a app, carregar config, registrar rotas/blueprints,
  instanciar e injetar dependências, e subir o servidor. Um lugar só.
- **Regra:** o entry point monta o grafo de dependências; o resto não se auto-instancia.

## Estrutura de diretórios alvo (modelo)

Adapte nomes às convenções da stack, mas mantenha a separação:

```
src/                         (ou raiz, conforme a stack)
├── config/                  configuração e segredos (env vars)
│   └── settings.*
├── models/                  uma model por entidade/domínio
│   ├── <entidade>_model.*
│   └── ...
├── controllers/             um controller por domínio/recurso
│   ├── <recurso>_controller.*
│   └── ...
├── services/                regra de negócio reaproveitável / integrações
│   └── <coisa>_service.*
├── views/  (ou routes/)     roteamento + (de)serialização
│   └── routes.*
├── middlewares/             error handler, etc.
│   └── error_handler.*
└── app.*                    entry point / composition root
```

## Regras de adaptação ao contexto

1. **Monolito sem camadas** (ex: tudo em 4 arquivos): crie a árvore completa, separando
   por domínio. É a transformação mais profunda.
2. **Projeto parcialmente organizado** (já tem `models/`, `routes/`): **não destrua o
   que está bom**. Foque em:
   - introduzir a camada que falta (geralmente **Controllers/Services**),
   - tirar a regra de negócio de dentro das rotas,
   - extrair config/segredos,
   - centralizar error handling,
   - remover duplicação (reusar métodos de domínio existentes).
3. **Não troque a stack.** Refatorar Flask continua Flask; Express continua Express.
4. **Preserve contratos.** Mesmos paths, métodos HTTP e formato de resposta. Se o
   entry point mudar de lugar, atualize o script de start.

## Definição de "pronto" (checklist arquitetural)

- [ ] Estrutura de diretórios reflete as camadas MVC.
- [ ] Config/segredos fora do código, via env vars.
- [ ] Models encapsulam dados com queries parametrizadas; sem segredo em serialização.
- [ ] Views/Routes apenas roteiam e (de)serializam.
- [ ] Controllers concentram o fluxo do caso de uso.
- [ ] Regra reaproveitável e integrações em Services injetados.
- [ ] Error handling centralizado.
- [ ] Entry point/composition root único e claro.
- [ ] App inicia sem erros e endpoints originais respondem igual.
