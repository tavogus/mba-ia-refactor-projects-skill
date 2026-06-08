"""Controller de Produto — orquestra o caso de uso; sem SQL nem montagem de resposta HTTP."""
from flask import request

from src.config.settings import settings
from src.models import produto_model
from src.validators import validar_produto


def listar():
    limit = request.args.get("limit", settings.PAGE_SIZE, type=int)
    offset = request.args.get("offset", 0, type=int)
    return {"dados": produto_model.listar(limit, offset), "sucesso": True}, 200


def buscar(produto_id):
    produto = produto_model.buscar_por_id(produto_id)
    if produto:
        return {"dados": produto, "sucesso": True}, 200
    return {"erro": "Produto não encontrado", "sucesso": False}, 404


def criar():
    dados = request.get_json(silent=True)
    erro = validar_produto(dados)
    if erro:
        return {"erro": erro}, 400
    novo_id = produto_model.criar(
        dados["nome"], dados.get("descricao", ""), dados["preco"],
        dados["estoque"], dados.get("categoria", "geral"),
    )
    return {"dados": {"id": novo_id}, "sucesso": True, "mensagem": "Produto criado"}, 201


def atualizar(produto_id):
    if not produto_model.buscar_por_id(produto_id):
        return {"erro": "Produto não encontrado"}, 404
    dados = request.get_json(silent=True)
    erro = validar_produto(dados)
    if erro:
        return {"erro": erro}, 400
    produto_model.atualizar(
        produto_id, dados["nome"], dados.get("descricao", ""), dados["preco"],
        dados["estoque"], dados.get("categoria", "geral"),
    )
    return {"sucesso": True, "mensagem": "Produto atualizado"}, 200


def deletar(produto_id):
    if not produto_model.buscar_por_id(produto_id):
        return {"erro": "Produto não encontrado"}, 404
    produto_model.deletar(produto_id)
    return {"sucesso": True, "mensagem": "Produto deletado"}, 200


def buscar_filtrado():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria")
    preco_min = request.args.get("preco_min", type=float)
    preco_max = request.args.get("preco_max", type=float)
    resultados = produto_model.buscar(termo, categoria, preco_min, preco_max)
    return {"dados": resultados, "total": len(resultados), "sucesso": True}, 200
