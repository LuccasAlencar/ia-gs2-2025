"""
Serviço de inferência de ocupação a partir do currículo
Mapeia o currículo para as ocupações do CBO usando BERT
"""

import re
from typing import List, Dict, Tuple
from app.models.cbo_loader import CBODataLoader
from app.models.skills_matcher import SkillsMatcher
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class OccupationInferenceService:
    """Infere a ocupação/profissão a partir do texto do currículo"""
    
    def __init__(self, model_name: str = "sentence-transformers/distiluse-base-multilingual-cased-v2"):
        """
        Inicializa o serviço de inferência de ocupação
        
        Args:
            model_name: Nome do modelo Sentence Transformers
        """
        logger.info("Inicializando OccupationInferenceService...")
        
        self.cbo_loader = CBODataLoader()
        self.skills_matcher = SkillsMatcher(model_name)
        
        # Carregar todas as ocupações do CBO
        self.occupations = self._load_occupations()
        
        # Construir corpus com títulos de ocupação
        if self.occupations:
            occupation_titles = [occ["titulo"] for occ in self.occupations]
            self.skills_matcher.build_corpus(occupation_titles)
            logger.info(f"Corpus de ocupações construído com {len(occupation_titles)} ocupações")
        else:
            logger.warning("Nenhuma ocupação foi carregada do CBO")
        
        logger.info("OccupationInferenceService inicializado com sucesso")
    
    def _load_occupations(self) -> List[Dict]:
        """
        Carrega todas as ocupações do CBO
        
        Returns:
            Lista de dicionários com codigo e titulo
        """
        try:
            occupations = []
            
            # Obter dados do CBO loader
            if self.cbo_loader.ocupacoes_df is not None:
                for idx, row in self.cbo_loader.ocupacoes_df.iterrows():
                    occupations.append({
                        "codigo": str(row["CODIGO"]),
                        "titulo": str(row["TITULO"]).strip().lower()
                    })
            
            logger.info(f"Carregadas {len(occupations)} ocupações do CBO")
            return occupations
        
        except Exception as e:
            logger.error(f"Erro ao carregar ocupações: {str(e)}")
            return []
    
    def extract_professional_context(self, resume_text: str) -> Dict:
        """
        Extrai contexto profissional do currículo
        Busca por formação, experiência, especialidades
        
        Args:
            resume_text: Texto do currículo
            
        Returns:
            Dicionário com contexto profissional
        """
        context = {
            "formations": [],
            "experiences": [],
            "specializations": [],
            "keywords": []
        }
        
        text_lower = resume_text.lower()
        
        # Padrões para formação (graduação, especialização, mestrado, etc)
        formation_patterns = [
            r'(?:graduado?|bacharel|tecnólogo|technologoem|formado?|cursando)\s+(?:em|de)\s+([a-záéíóú\s\-]+?)(?:[\.\,\n])',
            r'(?:pós-graduação|especialização|mestrado|doutorado|mba|certificado?|extensão)\s+(?:em|de)\s+([a-záéíóú\s\-]+?)(?:[\.\,\n])',
            r'([a-záéíóú\s\-]+?)\s+(?:bacharel|tecnólogo|especialista|mestre|doutor)',
        ]
        
        for pattern in formation_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if match.group(1):
                    formation = match.group(1).strip()
                    if len(formation) > 3 and len(formation) < 100:
                        context["formations"].append(formation)
        
        # Padrões para experiência (anos de experiência em X)
        experience_patterns = [
            r'(?:\d+\s*(?:anos?|meses))\s+(?:de\s+)?(?:experiência|atuação|trabalho)\s+(?:com|em|como)\s+([a-záéíóú\s\-]+?)(?:[\.\,\n])',
            r'(?:trabalhei?|atuei?)\s+(?:como|de|em)\s+([a-záéíóú\s\-]+?)(?:[\.\,\n])',
            r'(?:experiência|expertise)\s+(?:em|com)\s+([a-záéíóú\s\-]+?)(?:[\.\,\n])',
        ]
        
        for pattern in experience_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if match.group(1):
                    experience = match.group(1).strip()
                    if len(experience) > 3 and len(experience) < 100:
                        context["experiences"].append(experience)
        
        # Padrões para especialização (especialista em, especialização em)
        specialization_patterns = [
            r'(?:especialist|especializ|especializad)\w*\s+(?:em|de)\s+([a-záéíóú\s\-]+?)(?:[\.\,\n])',
            r'(?:especialidade|especialidades|área)\s+(?:em|de)\s+([a-záéíóú\s\-]+?)(?:[\.\,\n])',
        ]
        
        for pattern in specialization_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if match.group(1):
                    spec = match.group(1).strip()
                    if len(spec) > 3 and len(spec) < 100:
                        context["specializations"].append(spec)
        
        # Combinar contexto em keywords principais
        all_context = context["formations"] + context["experiences"] + context["specializations"]
        context["keywords"] = list(set(all_context))  # Remover duplicatas
        
        logger.info(f"Contexto extraído: {len(context['formations'])} formações, "
                   f"{len(context['experiences'])} experiências, "
                   f"{len(context['specializations'])} especializações")
        
        return context
    
    def infer_occupations(
        self,
        resume_text: str,
        top_k: int = 5,
        threshold: float = 0.65
    ) -> List[Dict]:
        """
        Infere as ocupações mais prováveis a partir do currículo
        
        Args:
            resume_text: Texto do currículo
            top_k: Número máximo de ocupações a retornar
            threshold: Score mínimo de similaridade
            
        Returns:
            Lista de ocupações com scores de probabilidade
        """
        logger.info(f"Inferindo ocupações (top_k={top_k}, threshold={threshold})...")
        
        # Extrair contexto profissional
        context = self.extract_professional_context(resume_text)
        
        if not context["keywords"]:
            logger.warning("Nenhum contexto profissional foi extraído do currículo")
            return []
        
        # Para cada keyword, buscar occupações similares
        occupation_scores = {}
        
        for keyword in context["keywords"]:
            if len(keyword.strip()) < 3:
                continue
            
            # Buscar ocupações similares usando BERT
            results = self.skills_matcher.find_similar(
                keyword,
                top_k=10,
                threshold=threshold
            )
            
            # Adicionar ao score consolidado
            for occupation_title, score in results:
                if occupation_title not in occupation_scores:
                    occupation_scores[occupation_title] = []
                occupation_scores[occupation_title].append(float(score))
        
        # Consolidar scores (média dos matches)
        final_occupations = []
        
        for occupation_title, scores in occupation_scores.items():
            avg_score = sum(scores) / len(scores) if scores else 0
            
            # Encontrar código da ocupação
            occupation_code = None
            for occ in self.occupations:
                if occ["titulo"] == occupation_title:
                    occupation_code = occ["codigo"]
                    break
            
            final_occupations.append({
                "titulo": occupation_title,
                "codigo": occupation_code,
                "score": round(avg_score, 4),
                "confidence": "high" if avg_score > 0.80 else "medium" if avg_score > 0.70 else "low"
            })
        
        # Ordenar por score descendente e limitar a top_k
        final_occupations.sort(key=lambda x: x["score"], reverse=True)
        final_occupations = final_occupations[:top_k]
        
        logger.info(f"Inferência concluída: {len(final_occupations)} ocupações encontradas")
        
        return final_occupations
    
    def infer_primary_occupation(
        self,
        resume_text: str,
        threshold: float = 0.65
    ) -> Dict:
        """
        Infere a ocupação PRIMARY (mais provável) a partir do currículo
        
        Args:
            resume_text: Texto do currículo
            threshold: Score mínimo de similaridade
            
        Returns:
            Dicionário com a ocupação primary
        """
        occupations = self.infer_occupations(resume_text, top_k=1, threshold=threshold)
        
        if occupations:
            return occupations[0]
        else:
            return {
                "titulo": None,
                "codigo": None,
                "score": 0.0,
                "confidence": "low",
                "error": "Nenhuma ocupação foi inferida"
            }
