"""Model de Produto — acesso a dados com queries parametrizadas (cura AP-01)."""
from src.database import get_db

_FIELDS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def _to_dict(row):
    """Serialização única reaproveitada (cura AP-15)."""
    return {f: row[f] for f in _FIELDS}


def listar(limit=50, offset=0):
    cur = get_db().cursor()
    cur.execute("SELECT * FROM produtos LIMIT ? OFFSET ?", (limit, offset))
    return [_to_dict(r) for r in cur.fetchall()]


def buscar_por_id(produto_id):
    cur = get_db().cursor()
    cur.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
    row = cur.fetchone()
    return _to_dict(row) if row else None


def criar(nome, descricao, preco, estoque, categoria):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cur.lastrowid


def atualizar(produto_id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    db.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    db.commit()
    return True


def deletar(produto_id):
    db = get_db()
    db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    db.commit()
    return True


def buscar(termo=None, categoria=None, preco_min=None, preco_max=None):
    query = "SELECT * FROM produtos WHERE 1=1"
    params = []
    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min is not None:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max is not None:
        query += " AND preco <= ?"
        params.append(preco_max)
    cur = get_db().cursor()
    cur.execute(query, params)
    return [_to_dict(r) for r in cur.fetchall()]
