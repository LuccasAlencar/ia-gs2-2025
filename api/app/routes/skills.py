"""
Rotas para matching e processamento de habilidades
"""

from flask import Blueprint, request, jsonify
from app.services.skills_service import SkillsMatchingService
from app.utils.logger import setup_logger
import time

skills_bp = Blueprint("skills", __name__, url_prefix="/api/v1/skills")

logger = setup_logger(__name__)

# Singleton do serviço
_service_instance = None


def get_service():
    """Obtém ou cria a instância do serviço"""
    global _service_instance
    
    if _service_instance is None:
        logger.info("Criando nova instância do SkillsMatchingService...")
        _service_instance = SkillsMatchingService()
    
    return _service_instance


@skills_bp.route("/match", methods=["POST"])
def match_skills():
    """
    Endpoint para matching de habilidades não reconhecidas
    
    Request body:
    {
        "unrecognized_skills": ["Python Developer", "Machine Learning Engineer"],
        "top_k": 3,
        "threshold": 0.60
    }
    
    Response:
    {
        "status": "success",
        "processing_time": 0.123,
        "results": {
            "python developer": {
                "matched": true,
                "matches": [
                    {
                        "matched_skill": "desenvolvedor python",
                        "similarity_score": 0.8523,
                        "synonyms": [...],
                        "related_occupations": [...]
                    }
                ],
                "total_matches": 1,
                "threshold_used": 0.60
            }
        }
    }
    """
    
    try:
        start_time = time.time()
        
        # Validar request
        if not request.is_json:
            return jsonify({
                "status": "error",
                "message": "Content-Type deve ser application/json",
                "code": 400
            }), 400
        
        data = request.get_json()
        unrecognized_skills = data.get("unrecognized_skills", [])
        
        # Validações
        if not isinstance(unrecognized_skills, list):
            return jsonify({
                "status": "error",
                "message": "unrecognized_skills deve ser uma lista",
                "code": 400
            }), 400
        
        if len(unrecognized_skills) == 0:
            return jsonify({
                "status": "error",
                "message": "unrecognized_skills não pode estar vazia",
                "code": 400
            }), 400
        
        if len(unrecognized_skills) > 100:
            return jsonify({
                "status": "error",
                "message": "Máximo de 100 habilidades por requisição",
                "code": 400
            }), 400
        
        # Parâmetros opcionais
        top_k = data.get("top_k", 3)
        threshold = data.get("threshold", 0.75)
        
        # Validar parâmetros
        if not isinstance(top_k, int) or top_k < 1 or top_k > 20:
            top_k = 3
        
        if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
            threshold = 0.75
        
        logger.info(f"Matching de {len(unrecognized_skills)} habilidades (top_k={top_k}, threshold={threshold})")
        
        # Obter serviço e fazer matching
        service = get_service()
        
        if not service.skills_matcher.is_corpus_ready():
            return jsonify({
                "status": "error",
                "message": "Modelo não está pronto. Tente novamente em alguns segundos.",
                "code": 503
            }), 503
        
        results = service.match_unrecognized_skills(
            unrecognized_skills,
            top_k=top_k,
            threshold=threshold
        )
        
        if "error" in results:
            return jsonify({
                "status": "error",
                "message": results["error"],
                "code": 500
            }), 500
        
        processing_time = time.time() - start_time
        
        return jsonify({
            "status": "success",
            "processing_time_seconds": round(processing_time, 4),
            "input_skills_count": len(unrecognized_skills),
            "results": results,
            "parameters": {
                "top_k": top_k,
                "threshold": threshold
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Erro no endpoint /match: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e),
            "code": 500
        }), 500


@skills_bp.route("/enrich", methods=["POST"])
def enrich_profile():
    """
    Endpoint para enriquecer perfil de habilidades
    
    Request body:
    {
        "skills": ["Java", "Python", "SQL"],
        "confidence_threshold": 0.60
    }
    """
    
    try:
        start_time = time.time()
        
        if not request.is_json:
            return jsonify({
                "status": "error",
                "message": "Content-Type deve ser application/json",
                "code": 400
            }), 400
        
        data = request.get_json()
        skills = data.get("skills", [])
        
        if not isinstance(skills, list) or len(skills) == 0:
            return jsonify({
                "status": "error",
                "message": "skills deve ser uma lista não vazia",
                "code": 400
            }), 400
        
        confidence_threshold = data.get("confidence_threshold", 0.75)
        
        logger.info(f"Enriquecendo perfil de {len(skills)} habilidades")
        
        service = get_service()
        
        if not service.skills_matcher.is_corpus_ready():
            return jsonify({
                "status": "error",
                "message": "Modelo não está pronto",
                "code": 503
            }), 503
        
        enriched = service.enrich_skills_profile(
            skills,
            confidence_threshold=confidence_threshold
        )
        
        if "error" in enriched:
            return jsonify({
                "status": "error",
                "message": enriched["error"],
                "code": 500
            }), 500
        
        processing_time = time.time() - start_time
        
        return jsonify({
            "status": "success",
            "processing_time_seconds": round(processing_time, 4),
            "data": enriched
        }), 200
    
    except Exception as e:
        logger.error(f"Erro no endpoint /enrich: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e),
            "code": 500
        }), 500


@skills_bp.route("/occupations", methods=["POST"])
def find_occupations():
    """
    Endpoint para encontrar ocupações relacionadas às habilidades
    
    Request body:
    {
        "skills": ["Python", "Machine Learning"],
        "limit": 10
    }
    """
    
    try:
        start_time = time.time()
        
        if not request.is_json:
            return jsonify({
                "status": "error",
                "message": "Content-Type deve ser application/json",
                "code": 400
            }), 400
        
        data = request.get_json()
        skills = data.get("skills", [])
        
        if not isinstance(skills, list) or len(skills) == 0:
            return jsonify({
                "status": "error",
                "message": "skills deve ser uma lista não vazia",
                "code": 400
            }), 400
        
        limit = data.get("limit", 10)
        if not isinstance(limit, int) or limit < 1 or limit > 50:
            limit = 10
        
        logger.info(f"Buscando ocupações para {len(skills)} habilidades")
        
        service = get_service()
        
        occupations = service.search_occupations_by_skills(skills, limit=limit)
        
        processing_time = time.time() - start_time
        
        return jsonify({
            "status": "success",
            "processing_time_seconds": round(processing_time, 4),
            "data": occupations
        }), 200
    
    except Exception as e:
        logger.error(f"Erro no endpoint /occupations: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e),
            "code": 500
        }), 500


@skills_bp.route("/model-info", methods=["GET"])
def model_info():
    """Retorna informações sobre o modelo e corpus carregado"""
    
    try:
        service = get_service()
        info = service.get_model_info()
        
        return jsonify({
            "status": "success",
            "model_info": info
        }), 200
    
    except Exception as e:
        logger.error(f"Erro no endpoint /model-info: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e),
            "code": 500
        }), 500


@skills_bp.route("/similarity", methods=["POST"])
def calculate_similarity():
    """
    Calcula similaridade entre dois textos
    
    Request body:
    {
        "text1": "Python Developer",
        "text2": "Desenvolvedor Python"
    }
    """
    
    try:
        if not request.is_json:
            return jsonify({
                "status": "error",
                "message": "Content-Type deve ser application/json",
                "code": 400
            }), 400
        
        data = request.get_json()
        text1 = data.get("text1", "")
        text2 = data.get("text2", "")
        
        if not text1 or not text2:
            return jsonify({
                "status": "error",
                "message": "text1 e text2 são obrigatórios",
                "code": 400
            }), 400
        
        service = get_service()
        similarity = service.skills_matcher.calculate_similarity(text1, text2)
        
        return jsonify({
            "status": "success",
            "text1": text1,
            "text2": text2,
            "similarity_score": round(similarity, 4)
        }), 200
    
    except Exception as e:
        logger.error(f"Erro no endpoint /similarity: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e),
            "code": 500
        }), 500
