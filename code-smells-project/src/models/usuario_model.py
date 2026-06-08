"""Model de Usuário — hashing seguro e nunca expõe a senha (cura AP-01/AP-04/AP-06)."""
from werkzeug.security import check_password_hash, generate_password_hash

from src.database import get_db

# Campos públicos — `senha` deliberadamente fora da serialização (cura AP-06).
_PUBLIC = ("id", "nome", "email", "tipo", "criado_em")


def _to_public(row):
    return {f: row[f] for f in _PUBLIC}


def listar():
    cur = get_db().cursor()
    cur.execute("SELECT * FROM usuarios")
    return [_to_public(r) for r in cur.fetchall()]


def buscar_por_id(usuario_id):
    cur = get_db().cursor()
    cur.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
    row = cur.fetchone()
    return _to_public(row) if row else None


def criar(nome, email, senha, tipo="cliente"):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, generate_password_hash(senha, method="pbkdf2:sha256"), tipo),
    )
    db.commit()
    return cur.lastrowid


def autenticar(email, senha):
    """Confere o hash com check_password_hash; nunca compara senha em texto puro."""
    cur = get_db().cursor()
    cur.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    row = cur.fetchone()
    if row and check_password_hash(row["senha"], senha):
        return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}
    return None
