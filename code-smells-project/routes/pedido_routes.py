from flask import Blueprint, request, jsonify
from controllers import pedido_controller

pedido_bp = Blueprint("pedidos", __name__)


@pedido_bp.route("/pedidos", methods=["POST"])
def criar_pedido():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        return jsonify({"erro": "usuario_id é obrigatório"}), 400
    if not itens:
        return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400
    resultado = pedido_controller.criar(usuario_id, itens)
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


@pedido_bp.route("/pedidos", methods=["GET"])
def listar_todos_pedidos():
    pedidos = pedido_controller.listar_todos()
    return jsonify({"dados": pedidos, "sucesso": True}), 200


@pedido_bp.route("/pedidos/usuario/<int:usuario_id>", methods=["GET"])
def listar_pedidos_usuario(usuario_id):
    pedidos = pedido_controller.listar_por_usuario(usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


@pedido_bp.route("/pedidos/<int:pedido_id>/status", methods=["PUT"])
def atualizar_status_pedido(pedido_id):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400
    novo_status = dados.get("status", "")
    pedido_controller.atualizar_status(pedido_id, novo_status)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


@pedido_bp.route("/relatorios/vendas", methods=["GET"])
def relatorio_vendas():
    relatorio = pedido_controller.relatorio_vendas()
    return jsonify({"dados": relatorio, "sucesso": True}), 200
