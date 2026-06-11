from models import produto_model

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
NOME_MIN = 2
NOME_MAX = 200


def listar_todos():
    return produto_model.get_todos()


def buscar_por_id(produto_id):
    produto = produto_model.get_por_id(produto_id)
    if not produto:
        raise ValueError("Produto não encontrado")
    return produto


def criar(dados):
    nome = dados.get("nome", "")
    descricao = dados.get("descricao", "")
    preco = dados.get("preco")
    estoque = dados.get("estoque")
    categoria = dados.get("categoria", "geral")

    if preco is None:
        raise ValueError("Preço é obrigatório")
    if estoque is None:
        raise ValueError("Estoque é obrigatório")
    if not nome:
        raise ValueError("Nome é obrigatório")
    if len(nome) < NOME_MIN:
        raise ValueError("Nome muito curto")
    if len(nome) > NOME_MAX:
        raise ValueError("Nome muito longo")
    if preco < 0:
        raise ValueError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValueError("Estoque não pode ser negativo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValueError(f"Categoria inválida. Válidas: {CATEGORIAS_VALIDAS}")

    produto_id = produto_model.criar(nome, descricao, preco, estoque, categoria)
    return {"id": produto_id}


def atualizar(produto_id, dados):
    if not produto_model.get_por_id(produto_id):
        raise ValueError("Produto não encontrado")

    nome = dados.get("nome", "")
    descricao = dados.get("descricao", "")
    preco = dados.get("preco")
    estoque = dados.get("estoque")
    categoria = dados.get("categoria", "geral")

    if not nome:
        raise ValueError("Nome é obrigatório")
    if preco is None:
        raise ValueError("Preço é obrigatório")
    if estoque is None:
        raise ValueError("Estoque é obrigatório")
    if preco < 0:
        raise ValueError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValueError("Estoque não pode ser negativo")

    produto_model.atualizar(produto_id, nome, descricao, preco, estoque, categoria)


def deletar(produto_id):
    if not produto_model.get_por_id(produto_id):
        raise ValueError("Produto não encontrado")
    produto_model.deletar(produto_id)


def buscar(termo, categoria=None, preco_min=None, preco_max=None):
    return produto_model.buscar(termo, categoria, preco_min, preco_max)
