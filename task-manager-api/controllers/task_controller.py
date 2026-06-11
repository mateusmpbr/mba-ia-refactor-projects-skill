import logging
from datetime import datetime
from sqlalchemy.orm import joinedload
from database import db
from models.task import Task
from models.user import User
from models.category import Category

logger = logging.getLogger(__name__)

VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']
TITLE_MIN = 3
TITLE_MAX = 200
PRIORITY_MIN = 1
PRIORITY_MAX = 5


def get_all_tasks():
    tasks = Task.query.options(
        joinedload(Task.user),
        joinedload(Task.category)
    ).all()
    result = []
    for t in tasks:
        data = t.to_dict()
        data['overdue'] = t.is_overdue()
        data['user_name'] = t.user.name if t.user else None
        data['category_name'] = t.category.name if t.category else None
        result.append(data)
    return result


def get_task_by_id(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise LookupError('Task não encontrada')
    data = task.to_dict()
    data['overdue'] = task.is_overdue()
    return data


def create_task(data):
    title = data.get('title')
    if not title:
        raise ValueError('Título é obrigatório')
    title = title.strip()
    if len(title) < TITLE_MIN:
        raise ValueError('Título muito curto')
    if len(title) > TITLE_MAX:
        raise ValueError('Título muito longo')

    status = data.get('status', 'pending')
    if status not in VALID_STATUSES:
        raise ValueError('Status inválido')

    priority = data.get('priority', 3)
    if not isinstance(priority, int) or priority < PRIORITY_MIN or priority > PRIORITY_MAX:
        raise ValueError('Prioridade deve ser entre 1 e 5')

    user_id = data.get('user_id')
    if user_id and not db.session.get(User, user_id):
        raise LookupError('Usuário não encontrado')

    category_id = data.get('category_id')
    if category_id and not db.session.get(Category, category_id):
        raise LookupError('Categoria não encontrada')

    task = Task()
    task.title = title
    task.description = data.get('description', '')
    task.status = status
    task.priority = priority
    task.user_id = user_id
    task.category_id = category_id

    due_date = data.get('due_date')
    if due_date:
        try:
            task.due_date = datetime.strptime(due_date, '%Y-%m-%d')
        except ValueError:
            raise ValueError('Formato de data inválido. Use YYYY-MM-DD')

    tags = data.get('tags')
    if tags:
        task.tags = ','.join(tags) if isinstance(tags, list) else tags

    db.session.add(task)
    db.session.commit()
    logger.info('Task criada: %s - %s', task.id, task.title)
    return task.to_dict()


def update_task(task_id, data):
    task = db.session.get(Task, task_id)
    if not task:
        raise LookupError('Task não encontrada')

    if 'title' in data:
        title = data['title'].strip()
        if len(title) < TITLE_MIN:
            raise ValueError('Título muito curto')
        if len(title) > TITLE_MAX:
            raise ValueError('Título muito longo')
        task.title = title

    if 'description' in data:
        task.description = data['description']

    if 'status' in data:
        if data['status'] not in VALID_STATUSES:
            raise ValueError('Status inválido')
        task.status = data['status']

    if 'priority' in data:
        p = data['priority']
        if p < PRIORITY_MIN or p > PRIORITY_MAX:
            raise ValueError('Prioridade deve ser entre 1 e 5')
        task.priority = p

    if 'user_id' in data:
        if data['user_id'] and not db.session.get(User, data['user_id']):
            raise LookupError('Usuário não encontrado')
        task.user_id = data['user_id']

    if 'category_id' in data:
        if data['category_id'] and not db.session.get(Category, data['category_id']):
            raise LookupError('Categoria não encontrada')
        task.category_id = data['category_id']

    if 'due_date' in data:
        if data['due_date']:
            try:
                task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
            except ValueError:
                raise ValueError('Formato de data inválido')
        else:
            task.due_date = None

    if 'tags' in data:
        tags = data['tags']
        task.tags = ','.join(tags) if isinstance(tags, list) else tags

    task.updated_at = datetime.utcnow()
    db.session.commit()
    logger.info('Task atualizada: %s', task.id)
    return task.to_dict()


def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise LookupError('Task não encontrada')
    db.session.delete(task)
    db.session.commit()
    logger.info('Task deletada: %s', task_id)


def search_tasks(query='', status='', priority='', user_id=''):
    q = Task.query
    if query:
        q = q.filter(db.or_(
            Task.title.like(f'%{query}%'),
            Task.description.like(f'%{query}%')
        ))
    if status:
        q = q.filter(Task.status == status)
    if priority:
        q = q.filter(Task.priority == int(priority))
    if user_id:
        q = q.filter(Task.user_id == int(user_id))
    return [t.to_dict() for t in q.all()]


def get_task_stats():
    total = Task.query.count()
    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()
    overdue_count = sum(1 for t in Task.query.all() if t.is_overdue())
    return {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'done': done,
        'cancelled': cancelled,
        'overdue': overdue_count,
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0
    }
