"""
Rotas para extração e análise de currículo
Novos endpoints: /extract, /match-profile, /infer-occupation
"""

from flask import Blueprint, request, jsonify
from app.services.extraction_service import SkillExtractionService
from app.services.occupation_inference_service import OccupationInferenceService
from app.utils.logger import setup_logger
from typing import Dict
import time

extraction_bp = Blueprint("extraction", __name__, url_prefix="/api/v1")

logger = setup_logger(__name__)

# Singletons dos serviços
_extraction_service = None
_occupation_service = None


def get_extraction_service():
    """Obtém ou cria a instância do serviço de extração"""
    global _extraction_service
    
    if _extraction_service is None:
        logger.info("Criando nova instância do SkillExtractionService...")
        _extraction_service = SkillExtractionService()
    
    return _extraction_service


def get_occupation_service():
    """Obtém ou cria a instância do serviço de inferência de ocupação"""
    global _occupation_service
    
    if _occupation_service is None:
        logger.info("Criando nova instância do OccupationInferenceService...")
        _occupation_service = OccupationInferenceService()
    
    return _occupation_service


@extraction_bp.route("/extract", methods=["POST"])
def extract_resume_skills():
    """
    Extração completa de skills do currículo
    
    Request body:
    {
        "resume_text": "Texto completo do currículo aqui...",
        "threshold": 0.75,
        "top_k": 1
    }
    
    Response:
    {
        "status": "success",
        "processing_time": 1.234,
        "total_skills_found": 25,
        "successful_matches": 20,
        "match_rate": "80%",
        "skills": [
            {
                "original": "Python",
                "matched_skill": "programação python",
                "similarity_score": 0.95,
                "confidence": "high"
            }
        ]
    }
    """
    
    try:
        start_time = time.time()
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "Request body vazio",
                "code": 400
            }), 400
        
        resume_text = data.get("resume_text", "")
        
        if not resume_text or not isinstance(resume_text, str):
            return jsonify({
                "status": "error",
                "message": "resume_text deve ser uma string não vazia",
                "code": 400
            }), 400
        
        resume_text = resume_text.strip()
        
        if len(resume_text) < 10:
            return jsonify({
                "status": "error",
                "message": "resume_text deve ter pelo menos 10 caracteres",
                "code": 400
            }), 400
        
        threshold = data.get("threshold", 0.75)
        top_k = data.get("top_k", 1)
        
        # Validações
        if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
            threshold = 0.75
        
        if not isinstance(top_k, int) or top_k < 1 or top_k > 10:
            top_k = 1
        
        logger.info(f"Extraindo skills do currículo (threshold={threshold}, top_k={top_k})")
        
        # Extrair skills
        service = get_extraction_service()
        result = service.extract_resume_skills(resume_text, threshold=threshold, top_k=top_k)
        
        processing_time = time.time() - start_time
        
        return jsonify({
            "status": "success",
            "processing_time": round(processing_time, 3),
            "total_skills_found": result["total_skills_found"],
            "successful_matches": result["successful_matches"],
            "match_rate": result["match_rate"],
            "skills": result["skills"]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao extrair skills: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Erro na extração: {str(e)}",
            "code": 500
        }), 500


@extraction_bp.route("/match-profile", methods=["POST"])
def match_candidate_to_job():
    """
    Calcula percentual de adequação do candidato à vaga
    
    Request body:
    {
        "candidate_skills": ["Python", "Django", "PostgreSQL", "Docker"],
        "job_requirements": ["Python", "Django", "AWS", "Docker", "Kubernetes"],
        "weight_match": 0.7,
        "weight_similarity": 0.3
    }
    
    Response:
    {
        "status": "success",
        "processing_time": 0.123,
        "match_score": 0.8,
        "match_percentage": "80%",
        "level": "BOM - Candidato bem qualificado",
        "matched_skills": ["Python", "Django", "Docker"],
        "matched_count": 3,
        "missing_skills": ["AWS", "Kubernetes"],
        "missing_count": 2,
        "required_count": 5,
        "analysis": {
            "strengths": "Possui 3 das 5 skills requeridas",
            "gaps": "Faltam 2 skills",
            "recommendation": "Forte candidato"
        }
    }
    """
    
    try:
        start_time = time.time()
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "Request body vazio",
                "code": 400
            }), 400
        
        candidate_skills = data.get("candidate_skills", [])
        job_requirements = data.get("job_requirements", [])
        
        # Validações
        if not isinstance(candidate_skills, list) or len(candidate_skills) == 0:
            return jsonify({
                "status": "error",
                "message": "candidate_skills deve ser uma lista não vazia",
                "code": 400
            }), 400
        
        if not isinstance(job_requirements, list) or len(job_requirements) == 0:
            return jsonify({
                "status": "error",
                "message": "job_requirements deve ser uma lista não vazia",
                "code": 400
            }), 400
        
        if len(candidate_skills) > 100 or len(job_requirements) > 100:
            return jsonify({
                "status": "error",
                "message": "Máximo de 100 skills por lista",
                "code": 400
            }), 400
        
        weight_match = data.get("weight_match", 0.7)
        weight_similarity = data.get("weight_similarity", 0.3)
        
        if not isinstance(weight_match, (int, float)) or not isinstance(weight_similarity, (int, float)):
            weight_match, weight_similarity = 0.7, 0.3
        
        logger.info(f"Calculando adequação: {len(candidate_skills)} skills candidato vs {len(job_requirements)} requisitos vaga")
        
        # Calcular match
        service = get_extraction_service()
        result = service.calculate_profile_match(
            candidate_skills,
            job_requirements,
            weight_match=weight_match,
            weight_similarity=weight_similarity
        )
        
        processing_time = time.time() - start_time
        
        return jsonify({
            "status": "success",
            "processing_time": round(processing_time, 3),
            "match_score": result.get("match_score"),
            "match_percentage": result.get("match_percentage"),
            "level": result.get("level"),
            "matched_skills": result.get("matched_skills"),
            "matched_count": result.get("matched_count"),
            "missing_skills": result.get("missing_skills"),
            "missing_count": result.get("missing_count"),
            "required_count": result.get("required_count"),
            "analysis": result.get("analysis")
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao calcular adequação: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Erro no cálculo: {str(e)}",
            "code": 500
        }), 500


@extraction_bp.route("/health/extract", methods=["GET"])
def health_extraction():
    """Health check para o serviço de extração"""
    try:
        service = get_extraction_service()
        is_ready = service.skills_matcher.is_corpus_ready()
        
        return jsonify({
            "status": "healthy" if is_ready else "initializing",
            "service": "extraction",
            "model_ready": is_ready,
            "timestamp": time.time()
        }), 200
        
    except Exception as e:
        logger.error(f"Health check falhou: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "service": "extraction",
            "error": str(e)
        }), 503


@extraction_bp.route("/infer-occupation", methods=["POST"])
def infer_occupation():
    """
    Infere a ocupação/profissão a partir do currículo
    
    Request body:
    {
        "resume_text": "Texto completo do currículo aqui...",
        "top_k": 5,
        "threshold": 0.65
    }
    
    Response:
    {
        "status": "success",
        "processing_time": 1.234,
        "occupations": [
            {
                "titulo": "cardiologista",
                "codigo": "225101",
                "score": 0.92,
                "confidence": "high"
            }
        ]
    }
    """
    
    try:
        start_time = time.time()
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "Request body vazio",
                "code": 400
            }), 400
        
        resume_text = data.get("resume_text", "")
        
        if not resume_text or not isinstance(resume_text, str):
            return jsonify({
                "status": "error",
                "message": "resume_text deve ser uma string não vazia",
                "code": 400
            }), 400
        
        resume_text = resume_text.strip()
        
        if len(resume_text) < 10:
            return jsonify({
                "status": "error",
                "message": "resume_text deve ter pelo menos 10 caracteres",
                "code": 400
            }), 400
        
        top_k = data.get("top_k", 5)
        threshold = data.get("threshold", 0.65)
        
        # Validações
        if not isinstance(top_k, int) or top_k < 1 or top_k > 20:
            top_k = 5
        
        if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
            threshold = 0.65
        
        logger.info(f"Inferindo ocupação (top_k={top_k}, threshold={threshold})")
        
        # Inferir ocupação
        service = get_occupation_service()
        occupations = service.infer_occupations(resume_text, top_k=top_k, threshold=threshold)
        
        processing_time = time.time() - start_time
        
        return jsonify({
            "status": "success",
            "processing_time": round(processing_time, 3),
            "occupations_found": len(occupations),
            "occupations": occupations
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao inferir ocupação: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Erro na inferência: {str(e)}",
            "code": 500
        }), 500


@extraction_bp.route("/infer-primary-occupation", methods=["POST"])
def infer_primary_occupation():
    """
    Infere a ocupação PRIMARY (mais provável) a partir do currículo
    
    Request body:
    {
        "resume_text": "Texto completo do currículo aqui...",
        "threshold": 0.65
    }
    
    Response:
    {
        "status": "success",
        "processing_time": 1.234,
        "primary_occupation": {
            "titulo": "cardiologista",
            "codigo": "225101",
            "score": 0.92,
            "confidence": "high"
        }
    }
    """
    
    try:
        start_time = time.time()
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "Request body vazio",
                "code": 400
            }), 400
        
        resume_text = data.get("resume_text", "")
        
        if not resume_text or not isinstance(resume_text, str):
            return jsonify({
                "status": "error",
                "message": "resume_text deve ser uma string não vazia",
                "code": 400
            }), 400
        
        resume_text = resume_text.strip()
        
        if len(resume_text) < 10:
            return jsonify({
                "status": "error",
                "message": "resume_text deve ter pelo menos 10 caracteres",
                "code": 400
            }), 400
        
        threshold = data.get("threshold", 0.65)
        
        if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
            threshold = 0.65
        
        logger.info(f"Inferindo ocupação primary (threshold={threshold})")
        
        # Inferir ocupação
        service = get_occupation_service()
        occupation = service.infer_primary_occupation(resume_text, threshold=threshold)
        
        processing_time = time.time() - start_time
        
        return jsonify({
            "status": "success",
            "processing_time": round(processing_time, 3),
            "primary_occupation": occupation
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao inferir ocupação primary: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Erro na inferência: {str(e)}",
            "code": 500
        }), 500


@extraction_bp.route("/health/occupation", methods=["GET"])
def health_occupation():
    """Health check para o serviço de inferência de ocupação"""
    try:
        service = get_occupation_service()
        is_ready = service.skills_matcher.is_corpus_ready() and len(service.occupations) > 0
        
        return jsonify({
            "status": "healthy" if is_ready else "initializing",
            "service": "occupation_inference",
            "model_ready": is_ready,
            "occupations_loaded": len(service.occupations),
            "timestamp": time.time()
        }), 200
        
    except Exception as e:
        logger.error(f"Health check occupation falhou: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "service": "occupation_inference",
            "error": str(e)
        }), 503


@extraction_bp.route("/analyze-resume", methods=["POST"])
def analyze_resume():
    """
    Análise completa do currículo - Ocupa + Skills (se técnico)
    
    Request body:
    {
        "resume_text": "Texto completo do currículo...",
        "threshold_occupation": 0.65,
        "threshold_skills": 0.75,
        "top_k_occupations": 3
    }
    
    Response:
    {
        "status": "success",
        "resume_type": "technical" | "non_technical",
        "primary_occupation": {
            "titulo": "Desenvolvedor Python",
            "codigo": "317105",
            "score": 0.92,
            "confidence": "high"
        },
        "skills": [...] (somente se resume_type == "technical"),
        "processing_time": 1.234
    }
    """
    
    try:
        start_time = time.time()
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "Request body vazio",
                "code": 400
            }), 400
        
        resume_text = data.get("resume_text", "")
        
        if not resume_text or not isinstance(resume_text, str):
            return jsonify({
                "status": "error",
                "message": "resume_text deve ser uma string não vazia",
                "code": 400
            }), 400
        
        resume_text = resume_text.strip()
        
        if len(resume_text) < 10:
            return jsonify({
                "status": "error",
                "message": "resume_text deve ter pelo menos 10 caracteres",
                "code": 400
            }), 400
        
        threshold_occupation = data.get("threshold_occupation", 0.65)
        threshold_skills = data.get("threshold_skills", 0.75)
        top_k_occupations = data.get("top_k_occupations", 3)
        
        # Validações
        if not isinstance(threshold_occupation, (int, float)) or threshold_occupation < 0 or threshold_occupation > 1:
            threshold_occupation = 0.65
        
        if not isinstance(threshold_skills, (int, float)) or threshold_skills < 0 or threshold_skills > 1:
            threshold_skills = 0.75
        
        if not isinstance(top_k_occupations, int) or top_k_occupations < 1 or top_k_occupations > 10:
            top_k_occupations = 3
        
        logger.info("Analisando currículo de forma completa...")
        
        # PASSO 1: Inferir ocupação
        occupation_service = get_occupation_service()
        primary_occupation = occupation_service.infer_primary_occupation(
            resume_text,
            threshold=threshold_occupation
        )
        
        logger.info(f"Ocupação inferida: {primary_occupation.get('titulo')}")
        
        # PASSO 2: Detectar se é profissão técnica
        resume_type = _detect_resume_type(primary_occupation)
        
        logger.info(f"Tipo de currículo detectado: {resume_type}")
        
        # PASSO 3: Se técnico, extrair skills. Se não, apenas retornar ocupação
        response = {
            "status": "success",
            "resume_type": resume_type,
            "primary_occupation": primary_occupation,
            "processing_time": round(time.time() - start_time, 3)
        }
        
        if resume_type == "technical":
            # Extrair skills apenas para currículos técnicos
            extraction_service = get_extraction_service()
            skills_result = extraction_service.extract_resume_skills(
                resume_text,
                threshold=threshold_skills,
                top_k=1
            )
            
            response["skills"] = skills_result.get("skills", [])
            response["total_skills_found"] = skills_result.get("total_skills_found", 0)
            response["successful_matches"] = skills_result.get("successful_matches", 0)
        else:
            # Para não-técnico, retornar vazio ou avisar que não faz sentido extrair skills
            response["skills"] = []
            response["note"] = "Currículo de profissão não-técnica. Skills não foram extraídas."
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Erro ao analisar currículo: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Erro na análise: {str(e)}",
            "code": 500
        }), 500


def _detect_resume_type(occupation: Dict) -> str:
    """
    Detecta se uma ocupação é técnica ou não-técnica
    
    Args:
        occupation: Dicionário com dados da ocupação
        
    Returns:
        "technical" ou "non_technical"
    """
    
    # Palavras-chave que indicam profissão técnica
    technical_keywords = [
        'desenvolvedor', 'programmer', 'engineer', 'engenheiro', 'analista',
        'administrador', 'devops', 'arquiteto', 'data', 'cientista',
        'especialista em', 'técnico', 'operacional', 'sre', 'infra',
        'programador', 'web', 'mobile', 'fullstack', 'backend', 'frontend',
        'qa', 'tester', 'segurança da informação', 'iot', 'cloud',
        'banco de dados', 'database', 'sistemas', 'ti', 'tecnologia',
        'software', 'hardware', 'network', 'suporte técnico'
    ]
    
    # Palavras-chave que indicam profissão não-técnica
    non_technical_keywords = [
        'médico', 'advogado', 'enfermeiro', 'psicólogo', 'odontólogo',
        'professor', 'educador', 'contador', 'auditor', 'consultor',
        'gerente', 'diretor', 'presidente', 'cfo', 'ceo', 'rh',
        'recursos humanos', 'recrutador', 'analista de rh', 'vendedor',
        'comercial', 'vendas', 'marketing', 'designer gráfico', 'designer',
        'arquiteto', 'engenheiro civil', 'agrônomo', 'veterinário',
        'cardiologista', 'dermatologista', 'psiquiatra', 'cirurgião'
    ]
    
    if not occupation or not occupation.get("titulo"):
        return "unknown"
    
    titulo_lower = str(occupation.get("titulo", "")).lower()
    
    # Verificar palavras-chave técnicas
    for keyword in technical_keywords:
        if keyword in titulo_lower:
            logger.info(f"Detectado currículo técnico por keyword: {keyword}")
            return "technical"
    
    # Verificar palavras-chave não-técnicas
    for keyword in non_technical_keywords:
        if keyword in titulo_lower:
            logger.info(f"Detectado currículo não-técnico por keyword: {keyword}")
            return "non_technical"
    
    # Default: considerar técnico se score é alto
    score = occupation.get("score", 0)
    if score > 0.75:
        return "technical"
    
    return "non_technical"


