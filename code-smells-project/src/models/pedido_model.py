"""Model de Pedido — queries parametrizadas, transação e JOIN sem N+1 (cura AP-01/AP-12)."""
from src.database import get_db


def _itens_por_pedido(db, pedido_ids):
    """Carrega todos os itens de vários pedidos em UMA query com JOIN (cura AP-12)."""
    if not pedido_ids:
        return {}
    placeholders = ",".join("?" * len(pedido_ids))
    cur = db.cursor()
    cur.execute(
        f"""SELECT ip.pedido_id, ip.produto_id, ip.quantidade, ip.preco_unitario,
                   p.nome AS produto_nome
            FROM itens_pedido ip
            LEFT JOIN produtos p ON p.id = ip.produto_id
            WHERE ip.pedido_id IN ({placeholders})""",
        pedido_ids,
    )
    agrupado = {}
    for r in cur.fetchall():
        agrupado.setdefault(r["pedido_id"], []).append(
            {
                "produto_id": r["produto_id"],
                "produto_nome": r["produto_nome"] or "Desconhecido",
                "quantidade": r["quantidade"],
                "preco_unitario": r["preco_unitario"],
            }
        )
    return agrupado


def _listar(where_sql="", params=()):
    db = get_db()
    cur = db.cursor()
    cur.execute(f"SELECT * FROM pedidos {where_sql}", params)
    pedidos = [dict(r) for r in cur.fetchall()]
    itens = _itens_por_pedido(db, [p["id"] for p in pedidos])
    for p in pedidos:
        p["itens"] = itens.get(p["id"], [])
    return pedidos


def listar_todos():
    return _listar()


def listar_por_usuario(usuario_id):
    return _listar("WHERE usuario_id = ?", (usuario_id,))


def criar(usuario_id, itens):
    """Cria pedido + itens e baixa estoque numa única transação."""
    db = get_db()
    cur = db.cursor()

    total = 0
    validados = []
    for item in itens:
        cur.execute("SELECT * FROM produtos WHERE id = ?", (item["produto_id"],))
        produto = cur.fetchone()
        if produto is None:
            return {"erro": f"Produto {item['produto_id']} não encontrado"}
        if produto["estoque"] < item["quantidade"]:
            return {"erro": f"Estoque insuficiente para {produto['nome']}"}
        total += produto["preco"] * item["quantidade"]
        validados.append((item, produto["preco"]))

    try:
        cur.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (usuario_id, total),
        )
        pedido_id = cur.lastrowid
        for item, preco in validados:
            cur.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], preco),
            )
            cur.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (item["quantidade"], item["produto_id"]),
            )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"pedido_id": pedido_id, "total": total}


def atualizar_status(pedido_id, novo_status):
    db = get_db()
    db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()
    return True


def contadores_vendas():
    """Agregações de vendas em queries dedicadas (sem regra de desconto aqui)."""
    cur = get_db().cursor()
    cur.execute("SELECT COUNT(*) AS c, COALESCE(SUM(total), 0) AS s FROM pedidos")
    row = cur.fetchone()
    total_pedidos, faturamento = row["c"], row["s"]

    cur.execute("SELECT status, COUNT(*) AS c FROM pedidos GROUP BY status")
    por_status = {r["status"]: r["c"] for r in cur.fetchall()}
    return {
        "total_pedidos": total_pedidos,
        "faturamento": faturamento,
        "pendentes": por_status.get("pendente", 0),
        "aprovados": por_status.get("aprovado", 0),
        "cancelados": por_status.get("cancelado", 0),
    }
