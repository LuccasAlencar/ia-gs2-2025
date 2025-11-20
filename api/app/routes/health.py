"""
Rotas de health check da API
"""

from flask import Blueprint, jsonify
from app.utils.logger import setup_logger

health_bp = Blueprint("health", __name__, url_prefix="/api/v1/health")

logger = setup_logger(__name__)


@health_bp.route("/", methods=["GET"])
def health_check():
    """Health check básico"""
    return jsonify({
        "status": "healthy",
        "service": "IA Skills Matcher API",
        "version": "1.0.0"
    }), 200


@health_bp.route("/live", methods=["GET"])
def liveness():
    """Liveness probe - verifica se a aplicação está rodando"""
    return jsonify({
        "status": "alive"
    }), 200


@health_bp.route("/ready", methods=["GET"])
def readiness():
    """Readiness probe - verifica se a aplicação está pronta"""
    return jsonify({
        "status": "ready"
    }), 200
