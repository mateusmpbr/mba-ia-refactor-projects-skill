import logging
from flask import jsonify
from controllers.exceptions import ConflictError, AuthenticationError, AuthorizationError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(LookupError)
    def handle_lookup_error(e):
        return jsonify({'error': str(e)}), 404

    @app.errorhandler(ValueError)
    def handle_value_error(e):
        return jsonify({'error': str(e)}), 400

    @app.errorhandler(ConflictError)
    def handle_conflict(e):
        return jsonify({'error': str(e)}), 409

    @app.errorhandler(AuthenticationError)
    def handle_authentication(e):
        return jsonify({'error': str(e)}), 401

    @app.errorhandler(AuthorizationError)
    def handle_authorization(e):
        return jsonify({'error': str(e)}), 403

    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({'error': 'Recurso não encontrado'}), 404

    @app.errorhandler(500)
    def handle_internal_error(e):
        logger.exception('Unhandled exception')
        return jsonify({'error': 'Erro interno do servidor'}), 500
