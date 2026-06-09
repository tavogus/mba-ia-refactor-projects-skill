"""Validação centralizada e reaproveitada entre create/update (cura AP-13/AP-15)."""

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
STATUS_PEDIDO_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]
NOME_MIN, NOME_MAX = 2, 200


def validar_produto(dados, partial=False):
    """Retorna mensagem de erro (str) ou None se válido."""
    if not dados:
        return "Dados inválidos"
    obrigatorios = ("nome", "preco", "estoque")
    if not partial:
        for campo in obrigatorios:
            if campo not in dados:
                return f"{campo.capitalize()} é obrigatório"

    if "nome" in dados:
        nome = dados["nome"]
        if len(nome) < NOME_MIN:
            return "Nome muito curto"
        if len(nome) > NOME_MAX:
            return "Nome muito longo"
    if "preco" in dados and dados["preco"] < 0:
        return "Preço não pode ser negativo"
    if "estoque" in dados and dados["estoque"] < 0:
        return "Estoque não pode ser negativo"
    categoria = dados.get("categoria", "geral")
    if categoria not in CATEGORIAS_VALIDAS:
        return "Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS)
    return None
