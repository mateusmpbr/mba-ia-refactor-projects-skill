import logging
from database import db
from models.category import Category
from models.task import Task

logger = logging.getLogger(__name__)


def get_all_categories():
    result = []
    for c in Category.query.all():
        data = c.to_dict()
        data['task_count'] = Task.query.filter_by(category_id=c.id).count()
        result.append(data)
    return result


def create_category(data):
    name = data.get('name')
    if not name:
        raise ValueError('Nome é obrigatório')
    category = Category()
    category.name = name
    category.description = data.get('description', '')
    category.color = data.get('color', '#000000')
    db.session.add(category)
    db.session.commit()
    return category.to_dict()


def update_category(cat_id, data):
    cat = db.session.get(Category, cat_id)
    if not cat:
        raise LookupError('Categoria não encontrada')
    if 'name' in data:
        cat.name = data['name']
    if 'description' in data:
        cat.description = data['description']
    if 'color' in data:
        cat.color = data['color']
    db.session.commit()
    return cat.to_dict()


def delete_category(cat_id):
    cat = db.session.get(Category, cat_id)
    if not cat:
        raise LookupError('Categoria não encontrada')
    db.session.delete(cat)
    db.session.commit()
