from database import get_db

STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]


def criar(usuario_id, total):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    )
    db.commit()
    return cursor.lastrowid


def criar_item(pedido_id, produto_id, quantidade, preco_unitario):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario),
    )
    db.commit()


def atualizar_status(pedido_id, novo_status):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE pedidos SET status = ? WHERE id = ?",
        (novo_status, pedido_id),
    )
    db.commit()


def _agrupar_pedidos(rows):
    pedidos = {}
    for row in rows:
        pid = row["id"]
        if pid not in pedidos:
            pedidos[pid] = {
                "id": pid,
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
        if row["produto_id"]:
            pedidos[pid]["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"],
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())


_JOIN_QUERY = """
    SELECT
        p.id, p.usuario_id, p.status, p.total, p.criado_em,
        ip.produto_id, ip.quantidade, ip.preco_unitario,
        pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = ip.produto_id
"""


def get_por_usuario(usuario_id):
    cursor = get_db().cursor()
    cursor.execute(_JOIN_QUERY + "WHERE p.usuario_id = ? ORDER BY p.id", (usuario_id,))
    return _agrupar_pedidos(cursor.fetchall())


def get_todos():
    cursor = get_db().cursor()
    cursor.execute(_JOIN_QUERY + "ORDER BY p.id")
    return _agrupar_pedidos(cursor.fetchall())


def get_estatisticas():
    cursor = get_db().cursor()
    cursor.execute("SELECT COUNT(*) FROM pedidos")
    total_pedidos = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(total), 0) FROM pedidos")
    faturamento = cursor.fetchone()[0]

    cursor.execute(
        "SELECT status, COUNT(*) as contagem FROM pedidos GROUP BY status"
    )
    por_status = {row["status"]: row["contagem"] for row in cursor.fetchall()}

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "por_status": por_status,
    }
