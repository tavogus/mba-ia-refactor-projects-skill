"""Controller de Usuário — cadastro e autenticação (sem expor senha)."""
from flask import request

from src.models import usuario_model


def listar():
    return {"dados": usuario_model.listar(), "sucesso": True}, 200


def buscar(usuario_id):
    usuario = usuario_model.buscar_por_id(usuario_id)
    if usuario:
        return {"dados": usuario, "sucesso": True}, 200
    return {"erro": "Usuário não encontrado"}, 404


def criar():
    dados = request.get_json(silent=True) or {}
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        return {"erro": "Nome, email e senha são obrigatórios"}, 400
    novo_id = usuario_model.criar(nome, email, senha)
    return {"dados": {"id": novo_id}, "sucesso": True}, 201


def login():
    dados = request.get_json(silent=True) or {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha:
        return {"erro": "Email e senha são obrigatórios"}, 400
    usuario = usuario_model.autenticar(email, senha)
    if usuario:
        return {"dados": usuario, "sucesso": True, "mensagem": "Login OK"}, 200
    return {"erro": "Email ou senha inválidos", "sucesso": False}, 401
