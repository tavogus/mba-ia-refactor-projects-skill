"""Views/Routes — apenas roteamento e (de)serialização HTTP. Nenhuma regra aqui."""
from flask import Blueprint, jsonify

from src.controllers import (
    pedido_controller,
    produto_controller,
    relatorio_controller,
    usuario_controller,
)
from src.database import get_db

api_bp = Blueprint("api", __name__)


def _json(result):
    """Adapta o retorno (dict, status) dos controllers para uma resposta Flask."""
    body, status = result
    return jsonify(body), status


# ---- Produtos ----
api_bp.add_url_rule("/produtos", "listar_produtos",
                    lambda: _json(produto_controller.listar()), methods=["GET"])
api_bp.add_url_rule("/produtos/busca", "buscar_produtos",
                    lambda: _json(produto_controller.buscar_filtrado()), methods=["GET"])
api_bp.add_url_rule("/produtos/<int:produto_id>", "buscar_produto",
                    lambda produto_id: _json(produto_controller.buscar(produto_id)), methods=["GET"])
api_bp.add_url_rule("/produtos", "criar_produto",
                    lambda: _json(produto_controller.criar()), methods=["POST"])
api_bp.add_url_rule("/produtos/<int:produto_id>", "atualizar_produto",
                    lambda produto_id: _json(produto_controller.atualizar(produto_id)), methods=["PUT"])
api_bp.add_url_rule("/produtos/<int:produto_id>", "deletar_produto",
                    lambda produto_id: _json(produto_controller.deletar(produto_id)), methods=["DELETE"])

# ---- Usuários ----
api_bp.add_url_rule("/usuarios", "listar_usuarios",
                    lambda: _json(usuario_controller.listar()), methods=["GET"])
api_bp.add_url_rule("/usuarios/<int:usuario_id>", "buscar_usuario",
                    lambda usuario_id: _json(usuario_controller.buscar(usuario_id)), methods=["GET"])
api_bp.add_url_rule("/usuarios", "criar_usuario",
                    lambda: _json(usuario_controller.criar()), methods=["POST"])
api_bp.add_url_rule("/login", "login",
                    lambda: _json(usuario_controller.login()), methods=["POST"])

# ---- Pedidos ----
api_bp.add_url_rule("/pedidos", "criar_pedido",
                    lambda: _json(pedido_controller.criar()), methods=["POST"])
api_bp.add_url_rule("/pedidos", "listar_todos_pedidos",
                    lambda: _json(pedido_controller.listar_todos()), methods=["GET"])
api_bp.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario",
                    lambda usuario_id: _json(pedido_controller.listar_por_usuario(usuario_id)), methods=["GET"])
api_bp.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido",
                    lambda pedido_id: _json(pedido_controller.atualizar_status(pedido_id)), methods=["PUT"])

# ---- Relatórios ----
api_bp.add_url_rule("/relatorios/vendas", "relatorio_vendas",
                    lambda: _json(relatorio_controller.vendas()), methods=["GET"])


@api_bp.route("/health")
def health_check():
    """Health check sem expor segredos (cura AP-06)."""
    db = get_db()
    cur = db.cursor()
    counts = {}
    for tabela in ("produtos", "usuarios", "pedidos"):
        cur.execute(f"SELECT COUNT(*) FROM {tabela}")
        counts[tabela] = cur.fetchone()[0]
    return jsonify({"status": "ok", "database": "connected", "counts": counts,
                    "versao": "1.0.0"}), 200


@api_bp.route("/")
def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": "1.0.0",
        "endpoints": {
            "produtos": "/produtos", "usuarios": "/usuarios", "pedidos": "/pedidos",
            "login": "/login", "relatorios": "/relatorios/vendas", "health": "/health",
        },
    })
