from models import usuario_model


def listar_todos():
    return usuario_model.get_todos()


def buscar_por_id(usuario_id):
    usuario = usuario_model.get_por_id(usuario_id)
    if not usuario:
        raise ValueError("Usuário não encontrado")
    return usuario


def criar(dados):
    nome = dados.get("nome", "").strip()
    email = dados.get("email", "").strip()
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        raise ValueError("Nome, email e senha são obrigatórios")
    if "@" not in email or "." not in email.split("@")[-1]:
        raise ValueError("Formato de email inválido")

    usuario_id = usuario_model.criar(nome, email, senha)
    return {"id": usuario_id}


def login(email, senha):
    if not email or not senha:
        raise ValueError("Email e senha são obrigatórios")
    usuario = usuario_model.verificar_login(email, senha)
    if not usuario:
        raise PermissionError("Email ou senha inválidos")
    return usuario
