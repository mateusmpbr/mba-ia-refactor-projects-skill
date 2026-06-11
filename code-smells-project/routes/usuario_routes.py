from flask import Blueprint, request, jsonify
from controllers import usuario_controller

usuario_bp = Blueprint("usuarios", __name__)


@usuario_bp.route("/usuarios", methods=["GET"])
def listar_usuarios():
    usuarios = usuario_controller.listar_todos()
    return jsonify({"dados": usuarios, "sucesso": True}), 200


@usuario_bp.route("/usuarios/<int:id>", methods=["GET"])
def buscar_usuario(id):
    usuario = usuario_controller.buscar_por_id(id)
    return jsonify({"dados": usuario, "sucesso": True}), 200


@usuario_bp.route("/usuarios", methods=["POST"])
def criar_usuario():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400
    resultado = usuario_controller.criar(dados)
    return jsonify({"dados": resultado, "sucesso": True}), 201


@usuario_bp.route("/login", methods=["POST"])
def login():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    usuario = usuario_controller.login(email, senha)
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
