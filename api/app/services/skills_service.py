"""
Serviço de matching de habilidades
Orquestra a interação entre o carregador CBO e o modelo IA
"""

from typing import List, Dict, Tuple, Optional
from app.models.cbo_loader import CBODataLoader
from app.models.skills_matcher import SkillsMatcher
from app.utils.logger import setup_logger
import time

logger = setup_logger(__name__)


class SkillsMatchingService:
    """Serviço para matching e expansão de habilidades profissionais"""
    
    def __init__(self, model_name: str = "sentence-transformers/distiluse-base-multilingual-cased-v2"):
        """
        Inicializa o serviço de matching
        
        Args:
            model_name: Nome do modelo Sentence Transformers
        """
        logger.info("Inicializando SkillsMatchingService...")
        
        self.cbo_loader = CBODataLoader()
        self.skills_matcher = SkillsMatcher(model_name)
        
        # Construir corpus com habilidades do CBO
        all_skills = self.cbo_loader.get_all_skills()
        
        if all_skills:
            self.skills_matcher.build_corpus(all_skills)
        else:
            logger.warning("Nenhuma habilidade foi carregada do CBO")
        
        logger.info("SkillsMatchingService inicializado com sucesso")
    
    def match_unrecognized_skills(
        self,
        unrecognized_skills: List[str],
        top_k: int = 3,
        threshold: float = 0.75
    ) -> Dict[str, List[Dict]]:
        """
        Faz matching de habilidades não reconhecidas
        
        Args:
            unrecognized_skills: Lista de habilidades não reconhecidas
            top_k: Número máximo de matches por habilidade
            threshold: Score mínimo de similaridade
        
        Returns:
            Dicionário com resultados de matching
        """
        
        if not self.skills_matcher.is_corpus_ready():
            logger.error("Modelo não está pronto")
            return {"error": "Modelo não está pronto para processamento"}
        
        try:
            logger.info(f"Processando {len(unrecognized_skills)} habilidades desconhecidas")
            
            results = {}
            
            for skill in unrecognized_skills:
                if not skill.strip():
                    continue
                
                # Encontrar matches
                similar = self.skills_matcher.find_similar(
                    skill,
                    top_k=top_k,
                    threshold=threshold
                )
                
                # Enriquecer com informações adicionais
                enhanced_matches = []
                for matched_skill, score in similar:
                    # Buscar sinônimos e ocupações
                    synonyms = self.cbo_loader.get_synonyms(matched_skill)
                    occupations = self.cbo_loader.search_occupations(matched_skill, limit=2)
                    
                    enhanced_matches.append({
                        "matched_skill": matched_skill,
                        "similarity_score": round(score, 4),
                        "synonyms": synonyms[:3],  # Top 3 sinônimos
                        "related_occupations": [
                            {
                                "titulo": occ["titulo"],
                                "codigo": occ["codigo"]
                            }
                            for occ in occupations[:2]  # Top 2 ocupações
                        ]
                    })
                
                results[skill.lower().strip()] = {
                    "matched": len(enhanced_matches) > 0,
                    "matches": enhanced_matches,
                    "total_matches": len(enhanced_matches),
                    "threshold_used": threshold
                }
            
            logger.info(f"Matching concluído com sucesso")
            return results
        
        except Exception as e:
            logger.error(f"Erro no matching: {str(e)}")
            return {
                "error": str(e),
                "partial_results": results if 'results' in locals() else {}
            }
    
    def enrich_skills_profile(
        self,
        skills: List[str],
        confidence_threshold: float = 0.75
    ) -> Dict:
        """
        Enriquece o perfil de habilidades com informações adicionais
        
        Args:
            skills: Lista de habilidades
            confidence_threshold: Score mínimo para inclusão
        
        Returns:
            Perfil enriquecido de habilidades
        """
        
        if not self.skills_matcher.is_corpus_ready():
            return {"error": "Modelo não está pronto"}
        
        try:
            enriched_profile = {
                "input_skills_count": len(skills),
                "skills_processed": [],
                "summary": {
                    "total_original": len(skills),
                    "confidence_threshold": confidence_threshold
                }
            }
            
            for skill in skills:
                if not skill.strip():
                    continue
                
                skill_clean = skill.lower().strip()
                
                # Encontrar matches com threshold mais baixo
                similar = self.skills_matcher.find_similar(
                    skill_clean,
                    top_k=5,
                    threshold=0.50
                )
                
                # Filtrar por threshold de confiança
                confident_matches = [
                    s for s in similar if s[1] >= confidence_threshold
                ]
                
                processed_skill = {
                    "original": skill,
                    "normalized": skill_clean,
                    "high_confidence_matches": [
                        {
                            "skill": m[0],
                            "score": round(m[1], 4)
                        }
                        for m in confident_matches
                    ],
                    "is_recognized": len(confident_matches) > 0
                }
                
                enriched_profile["skills_processed"].append(processed_skill)
            
            return enriched_profile
        
        except Exception as e:
            logger.error(f"Erro ao enriquecer perfil: {str(e)}")
            return {"error": str(e)}
    
    def search_occupations_by_skills(
        self,
        skills: List[str],
        limit: int = 10
    ) -> Dict:
        """
        Busca ocupações relacionadas às habilidades
        
        Args:
            skills: Lista de habilidades
            limit: Número máximo de ocupações a retornar
        
        Returns:
            Dicionário com ocupações relacionadas
        """
        
        try:
            occupations = set()
            
            for skill in skills:
                if skill.strip():
                    # Buscar ocupações relacionadas a cada skill
                    results = self.cbo_loader.search_occupations(skill.strip(), limit=5)
                    for occ in results:
                        occupations.add((occ["titulo"], occ["codigo"]))
            
            # Converter para lista e limitar
            occupations_list = [
                {
                    "titulo": titulo,
                    "codigo": codigo
                }
                for titulo, codigo in list(occupations)[:limit]
            ]
            
            return {
                "input_skills_count": len(skills),
                "occupations_found": len(occupations_list),
                "occupations": occupations_list,
                "limit": limit
            }
        
        except Exception as e:
            logger.error(f"Erro ao buscar ocupações: {str(e)}")
            return {
                "error": str(e),
                "occupations": []
            }
    
    def get_model_info(self) -> Dict:
        """Retorna informações sobre o modelo e corpus"""
        
        return {
            "model_name": self.skills_matcher.model_name,
            "model_ready": self.skills_matcher.is_corpus_ready(),
            "device": self.skills_matcher.device,
            "corpus_size": len(self.skills_matcher.corpus),
            "corpus_built": self.skills_matcher.corpus_embeddings is not None
        }
