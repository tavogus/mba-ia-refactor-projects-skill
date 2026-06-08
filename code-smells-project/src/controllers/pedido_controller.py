"""Controller de Pedido — orquestra criação/listagem e delega efeitos ao service."""
from flask import current_app, request

from src.models import pedido_model
from src.validators import STATUS_PEDIDO_VALIDOS


def _notifications():
    """Service injetado no composition root (DI via app.config) — cura AP-09."""
    return current_app.config["NOTIFICATIONS"]


def criar():
    dados = request.get_json(silent=True) or {}
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        return {"erro": "Usuario ID é obrigatório"}, 400
    if not itens:
        return {"erro": "Pedido deve ter pelo menos 1 item"}, 400

    resultado = pedido_model.criar(usuario_id, itens)
    if "erro" in resultado:
        return {"erro": resultado["erro"], "sucesso": False}, 400

    _notifications().pedido_criado(resultado["pedido_id"], usuario_id)
    return {"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}, 201


def listar_por_usuario(usuario_id):
    return {"dados": pedido_model.listar_por_usuario(usuario_id), "sucesso": True}, 200


def listar_todos():
    return {"dados": pedido_model.listar_todos(), "sucesso": True}, 200


def atualizar_status(pedido_id):
    dados = request.get_json(silent=True) or {}
    novo_status = dados.get("status", "")
    if novo_status not in STATUS_PEDIDO_VALIDOS:
        return {"erro": "Status inválido"}, 400
    pedido_model.atualizar_status(pedido_id, novo_status)
    _notifications().status_atualizado(pedido_id, novo_status)
    return {"sucesso": True, "mensagem": "Status atualizado"}, 200
