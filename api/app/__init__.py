"""
IA Skills Matcher API
API de IA para matching de habilidades profissionais usando Deep Learning
"""

from flask import Flask
from flask_cors import CORS
from app.routes.skills import skills_bp
from app.routes.health import health_bp
from app.routes.extraction import extraction_bp
from app.utils.logger import setup_logger
import os

logger = setup_logger(__name__)


def create_app(config=None):
    """Factory para criar a aplicação Flask"""
    app = Flask(__name__)
    
    # Configurações
    app.config['JSON_SORT_KEYS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
    
    if config:
        app.config.update(config)
    
    # CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Registrar blueprints
    app.register_blueprint(skills_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(extraction_bp)
    
    # Handlers de erro
    @app.errorhandler(404)
    def not_found(error):
        return {
            "status": "error",
            "message": "Recurso não encontrado",
            "code": 404
        }, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Erro interno: {str(error)}")
        return {
            "status": "error",
            "message": "Erro interno do servidor",
            "code": 500
        }, 500
    
    logger.info("Aplicação Flask criada com sucesso")
    return app
