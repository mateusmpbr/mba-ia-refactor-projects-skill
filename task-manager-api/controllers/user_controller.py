import logging
import re
from itsdangerous import URLSafeTimedSerializer
from database import db
from models.user import User
from models.task import Task
from config.settings import SECRET_KEY
from controllers.exceptions import ConflictError, AuthenticationError, AuthorizationError

logger = logging.getLogger(__name__)

VALID_ROLES = ['user', 'admin', 'manager']
MIN_PASSWORD_LENGTH = 4
EMAIL_REGEX = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'


def generate_token(user_id):
    s = URLSafeTimedSerializer(SECRET_KEY)
    return s.dumps({'user_id': user_id}, salt='user-auth')


def get_all_users():
    return [{**u.to_dict(), 'task_count': len(u.tasks)} for u in User.query.all()]


def get_user_by_id(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise LookupError('Usuário não encontrado')
    data = user.to_dict()
    data['tasks'] = [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]
    return data


def create_user(data):
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')

    if not name:
        raise ValueError('Nome é obrigatório')
    if not email:
        raise ValueError('Email é obrigatório')
    if not password:
        raise ValueError('Senha é obrigatória')
    if not re.match(EMAIL_REGEX, email):
        raise ValueError('Email inválido')
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError('Senha deve ter no mínimo 4 caracteres')
    if role not in VALID_ROLES:
        raise ValueError('Role inválido')
    if User.query.filter_by(email=email).first():
        raise ConflictError('Email já cadastrado')

    user = User()
    user.name = name
    user.email = email
    user.set_password(password)
    user.role = role
    db.session.add(user)
    db.session.commit()
    logger.info('Usuário criado: %s - %s', user.id, user.name)
    return user.to_dict()


def update_user(user_id, data):
    user = db.session.get(User, user_id)
    if not user:
        raise LookupError('Usuário não encontrado')

    if 'name' in data:
        user.name = data['name']

    if 'email' in data:
        if not re.match(EMAIL_REGEX, data['email']):
            raise ValueError('Email inválido')
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user_id:
            raise ConflictError('Email já cadastrado')
        user.email = data['email']

    if 'password' in data:
        if len(data['password']) < MIN_PASSWORD_LENGTH:
            raise ValueError('Senha muito curta')
        user.set_password(data['password'])

    if 'role' in data:
        if data['role'] not in VALID_ROLES:
            raise ValueError('Role inválido')
        user.role = data['role']

    if 'active' in data:
        user.active = data['active']

    db.session.commit()
    return user.to_dict()


def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise LookupError('Usuário não encontrado')
    Task.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    db.session.delete(user)
    db.session.commit()
    logger.info('Usuário deletado: %s', user_id)


def authenticate(email, password):
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise AuthenticationError('Credenciais inválidas')
    if not user.active:
        raise AuthorizationError('Usuário inativo')
    return user


def get_user_tasks(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise LookupError('Usuário não encontrado')
    result = []
    for t in Task.query.filter_by(user_id=user_id).all():
        result.append({
            'id': t.id,
            'title': t.title,
            'description': t.description,
            'status': t.status,
            'priority': t.priority,
            'created_at': str(t.created_at),
            'due_date': str(t.due_date) if t.due_date else None,
            'overdue': t.is_overdue()
        })
    return result
