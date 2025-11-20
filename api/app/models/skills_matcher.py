"""
Modelo de IA baseado em Sentence Transformers para matching semântico de habilidades
Utiliza embeddings BERT multilíngue para comparação de similaridade
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from sentence_transformers import SentenceTransformer, util
from app.utils.logger import setup_logger
import torch

logger = setup_logger(__name__)


class SkillsMatcher:
    """Modelo de IA para matching de habilidades profissionais usando embeddings"""
    
    def __init__(self, model_name: str = "sentence-transformers/distiluse-base-multilingual-cased-v2"):
        """
        Inicializa o modelo de matching
        
        Args:
            model_name: Nome do modelo Sentence Transformers a usar
        """
        self.model_name = model_name
        self.model = None
        self.corpus_embeddings = None
        self.corpus = []
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"Usando device: {self.device}")
        self._load_model()
    
    def _load_model(self):
        """Carrega o modelo Sentence Transformers"""
        try:
            logger.info(f"Carregando modelo {self.model_name}...")
            self.model = SentenceTransformer(
                self.model_name,
                device=self.device
            )
            logger.info("Modelo carregado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {str(e)}")
            raise
    
    def encode_texts(self, texts: List[str]) -> np.ndarray:
        """
        Codifica textos em embeddings
        
        Args:
            texts: Lista de textos a codificar
        
        Returns:
            Array de embeddings (numpy)
        """
        try:
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=True,
                batch_size=32
            )
            return embeddings
        except Exception as e:
            logger.error(f"Erro ao codificar textos: {str(e)}")
            return np.array([])
    
    def build_corpus(self, skills: List[str]):
        """
        Constrói o corpus de habilidades conhecidas
        
        Args:
            skills: Lista de habilidades a indexar
        """
        try:
            logger.info(f"Construindo corpus com {len(skills)} habilidades...")
            
            # Limpar duplicatas e vazios
            self.corpus = [s.strip().lower() for s in skills if s.strip()]
            self.corpus = list(dict.fromkeys(self.corpus))  # Remove duplicatas mantendo ordem
            
            # Codificar corpus
            self.corpus_embeddings = self.encode_texts(self.corpus)
            
            logger.info(f"Corpus construído com {len(self.corpus)} habilidades únicas")
        
        except Exception as e:
            logger.error(f"Erro ao construir corpus: {str(e)}")
            raise
    
    def find_similar(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.75
    ) -> List[Tuple[str, float]]:
        """
        Encontra as habilidades mais similares a uma query
        
        Args:
            query: Habilidade/texto a buscar
            top_k: Número máximo de resultados
            threshold: Score mínimo de similaridade (0-1)
        
        Returns:
            Lista de tuplas (habilidade, score_similaridade)
        """
        
        if self.corpus_embeddings is None or len(self.corpus) == 0:
            logger.warning("Corpus não foi construído. Use build_corpus() primeiro.")
            return []
        
        try:
            # Codificar a query
            query_embedding = self.model.encode(
                query.strip().lower(),
                convert_to_numpy=True
            )
            
            # Calcular similaridade cosseno
            similarities = util.pytorch_cos_sim(
                torch.from_numpy(query_embedding).unsqueeze(0),
                torch.from_numpy(self.corpus_embeddings)
            )[0]
            
            similarities = similarities.cpu().numpy()
            
            # Filtrar por threshold e ordenar
            results = [
                (self.corpus[idx], float(score))
                for idx, score in enumerate(similarities)
                if score >= threshold
            ]
            
            # Ordenar por score descendente e limitar a top_k
            results.sort(key=lambda x: x[1], reverse=True)
            results = results[:top_k]
            
            logger.debug(f"Query '{query}' encontrou {len(results)} matches com threshold {threshold}")
            
            return results
        
        except Exception as e:
            logger.error(f"Erro ao buscar similares para '{query}': {str(e)}")
            return []
    
    def batch_find_similar(
        self,
        queries: List[str],
        top_k: int = 5,
        threshold: float = 0.75
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        Encontra similares para múltiplas queries em batch
        
        Args:
            queries: Lista de queries
            top_k: Número máximo de resultados por query
            threshold: Score mínimo de similaridade
        
        Returns:
            Dicionário com queries como chave e lista de resultados como valor
        """
        
        results = {}
        for query in queries:
            results[query] = self.find_similar(query, top_k, threshold)
        
        return results
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calcula similaridade entre dois textos
        
        Args:
            text1: Primeiro texto
            text2: Segundo texto
        
        Returns:
            Score de similaridade (0-1)
        """
        
        try:
            embeddings = self.model.encode(
                [text1.strip().lower(), text2.strip().lower()],
                convert_to_numpy=True
            )
            
            similarity = util.pytorch_cos_sim(
                torch.from_numpy(embeddings[0]).unsqueeze(0),
                torch.from_numpy(embeddings[1]).unsqueeze(0)
            )[0][0]
            
            return float(similarity.cpu().numpy())
        
        except Exception as e:
            logger.error(f"Erro ao calcular similaridade: {str(e)}")
            return 0.0
    
    def expand_skills(
        self,
        skill: str,
        expansion_terms: List[str] = None,
        threshold: float = 0.65
    ) -> Dict:
        """
        Expande uma habilidade encontrando variações e relacionados
        
        Args:
            skill: Habilidade a expandir
            expansion_terms: Termos adicionais para considerar
            threshold: Score mínimo para inclusão
        
        Returns:
            Dicionário com informações de expansão
        """
        
        try:
            similar = self.find_similar(skill, top_k=10, threshold=threshold)
            
            # Construir resposta
            expansion = {
                "original_skill": skill,
                "similar_skills": [
                    {
                        "skill": s[0],
                        "similarity_score": s[1]
                    }
                    for s in similar
                ],
                "total_found": len(similar),
                "threshold_used": threshold
            }
            
            return expansion
        
        except Exception as e:
            logger.error(f"Erro ao expandir habilidade: {str(e)}")
            return {
                "original_skill": skill,
                "similar_skills": [],
                "total_found": 0,
                "error": str(e)
            }
    
    def is_corpus_ready(self) -> bool:
        """Verifica se o corpus está pronto para uso"""
        return (
            self.model is not None and
            self.corpus_embeddings is not None and
            len(self.corpus) > 0
        )
