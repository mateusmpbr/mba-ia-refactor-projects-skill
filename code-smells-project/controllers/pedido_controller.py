import logging
from models import produto_model, pedido_model

logger = logging.getLogger(__name__)

STATUS_VALIDOS = pedido_model.STATUS_VALIDOS

DESCONTO_ALTO_LIMITE = 10_000
DESCONTO_MEDIO_LIMITE = 5_000
DESCONTO_BAIXO_LIMITE = 1_000
DESCONTO_ALTO = 0.10
DESCONTO_MEDIO = 0.05
DESCONTO_BAIXO = 0.02


def criar(usuario_id, itens):
    total = 0.0
    itens_validados = []

    for item in itens:
        produto = produto_model.get_por_id(item["produto_id"])
        if produto is None:
            raise ValueError(f"Produto {item['produto_id']} não encontrado")
        if produto["estoque"] < item["quantidade"]:
            raise ValueError(f"Estoque insuficiente para {produto['nome']}")
        preco_unitario = produto["preco"]
        total += preco_unitario * item["quantidade"]
        itens_validados.append({**item, "preco_unitario": preco_unitario})

    pedido_id = pedido_model.criar(usuario_id, total)
    for item in itens_validados:
        pedido_model.criar_item(pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"])
        produto_model.decrementar_estoque(item["produto_id"], item["quantidade"])

    logger.info("Pedido %s criado para usuário %s — total R$%.2f", pedido_id, usuario_id, total)
    return {"pedido_id": pedido_id, "total": total}


def listar_por_usuario(usuario_id):
    return pedido_model.get_por_usuario(usuario_id)


def listar_todos():
    return pedido_model.get_todos()


def atualizar_status(pedido_id, novo_status):
    if novo_status not in STATUS_VALIDOS:
        raise ValueError(f"Status inválido. Válidos: {STATUS_VALIDOS}")
    pedido_model.atualizar_status(pedido_id, novo_status)
    logger.info("Pedido %s → status '%s'", pedido_id, novo_status)


def relatorio_vendas():
    stats = pedido_model.get_estatisticas()
    faturamento = stats["faturamento_bruto"]
    por_status = stats["por_status"]

    if faturamento > DESCONTO_ALTO_LIMITE:
        desconto = faturamento * DESCONTO_ALTO
    elif faturamento > DESCONTO_MEDIO_LIMITE:
        desconto = faturamento * DESCONTO_MEDIO
    elif faturamento > DESCONTO_BAIXO_LIMITE:
        desconto = faturamento * DESCONTO_BAIXO
    else:
        desconto = 0.0

    total_pedidos = stats["total_pedidos"]
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": faturamento,
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": por_status.get("pendente", 0),
        "pedidos_aprovados": por_status.get("aprovado", 0),
        "pedidos_cancelados": por_status.get("cancelado", 0),
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
