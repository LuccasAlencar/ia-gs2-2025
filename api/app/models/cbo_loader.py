"""
Módulo de carregamento e processamento dos dados CBO
"""

import pandas as pd
import os
import pickle
from typing import List, Dict, Tuple, Optional
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class CBODataLoader:
    """Carrega e processa os arquivos CSV do dataset CBO"""
    
    def __init__(self, dataset_path: str = "../dataset"):
        """
        Inicializa o carregador de dados CBO
        
        Args:
            dataset_path: Caminho para a pasta com os arquivos CSV
        """
        self.dataset_path = dataset_path
        self.ocupacoes_df = None
        self.sinonimos_df = None
        self.perfil_ocupacional_df = None
        self.skills_cache = {}
        
        self._load_datasets()
    
    def _load_datasets(self):
        """Carrega todos os arquivos CSV do dataset CBO"""
        try:
            # Encontrar o caminho relativo correto
            if not os.path.exists(self.dataset_path):
                # Tentar caminho relativo da pasta api
                self.dataset_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    "dataset"
                )
            
            logger.info(f"Carregando datasets de {self.dataset_path}")
            
            # Carregar Ocupações
            ocupacoes_path = os.path.join(self.dataset_path, "CBO2002 - Ocupacao.csv")
            if os.path.exists(ocupacoes_path):
                self.ocupacoes_df = pd.read_csv(ocupacoes_path, sep=";", encoding="latin-1")
                logger.info(f"Carregadas {len(self.ocupacoes_df)} ocupações")
            
            # Carregar Sinônimos
            sinonimos_path = os.path.join(self.dataset_path, "CBO2002 - Sinonimo.csv")
            if os.path.exists(sinonimos_path):
                self.sinonimos_df = pd.read_csv(sinonimos_path, sep=";", encoding="latin-1")
                logger.info(f"Carregados {len(self.sinonimos_df)} sinônimos")
            
            # Carregar Perfil Ocupacional
            perfil_path = os.path.join(self.dataset_path, "CBO2002 - PerfilOcupacional.csv")
            if os.path.exists(perfil_path):
                # Carregar apenas as primeiras 10000 linhas para economizar memória
                self.perfil_ocupacional_df = pd.read_csv(
                    perfil_path, 
                    sep=";", 
                    encoding="latin-1",
                    nrows=10000
                )
                logger.info(f"Carregados {len(self.perfil_ocupacional_df)} perfis ocupacionais")
            
        except Exception as e:
            logger.error(f"Erro ao carregar datasets CBO: {str(e)}")
            raise
    
    def get_all_skills(self) -> List[str]:
        """Extrai todas as habilidades/atividades do dataset"""
        
        if self.skills_cache:
            return self.skills_cache.get("all_skills", [])
        
        skills = set()
        
        try:
            # De ocupações
            if self.ocupacoes_df is not None and "TITULO" in self.ocupacoes_df.columns:
                skills.update(
                    self.ocupacoes_df["TITULO"]
                    .str.lower()
                    .str.strip()
                    .unique()
                    .tolist()
                )
            
            # De sinônimos
            if self.sinonimos_df is not None and "SINONIMO" in self.sinonimos_df.columns:
                skills.update(
                    self.sinonimos_df["SINONIMO"]
                    .str.lower()
                    .str.strip()
                    .unique()
                    .tolist()
                )
            
            # De perfil ocupacional (atividades)
            if self.perfil_ocupacional_df is not None and "NOME_ATIVIDADE" in self.perfil_ocupacional_df.columns:
                skills.update(
                    self.perfil_ocupacional_df["NOME_ATIVIDADE"]
                    .str.lower()
                    .str.strip()
                    .unique()
                    .tolist()
                )
            
            # De áreas de atuação
            if self.perfil_ocupacional_df is not None and "NOME_GRANDE_AREA" in self.perfil_ocupacional_df.columns:
                skills.update(
                    self.perfil_ocupacional_df["NOME_GRANDE_AREA"]
                    .str.lower()
                    .str.strip()
                    .unique()
                    .tolist()
                )
            
            # Filtrar strings vazias e muito curtas
            skills = [s for s in skills if len(s) > 2 and s.strip()]
            
            logger.info(f"Total de habilidades extraídas: {len(skills)}")
            self.skills_cache["all_skills"] = sorted(list(skills))
            
        except Exception as e:
            logger.error(f"Erro ao extrair habilidades: {str(e)}")
        
        return self.skills_cache.get("all_skills", [])
    
    def get_occupation_by_code(self, code: str) -> Optional[str]:
        """Retorna a descrição da ocupação por código"""
        
        if self.ocupacoes_df is None:
            return None
        
        try:
            result = self.ocupacoes_df[self.ocupacoes_df["CODIGO"] == code]
            if not result.empty:
                return result.iloc[0]["TITULO"]
        except Exception as e:
            logger.error(f"Erro ao buscar ocupação {code}: {str(e)}")
        
        return None
    
    def get_synonyms(self, skill: str) -> List[str]:
        """Retorna sinônimos de uma habilidade"""
        
        if self.sinonimos_df is None:
            return []
        
        synonyms = []
        try:
            # Procurar por ocupações que contêm o termo
            if "SINONIMO" in self.sinonimos_df.columns:
                matching = self.sinonimos_df[
                    self.sinonimos_df["SINONIMO"].str.lower().str.contains(skill.lower(), na=False)
                ]
                
                if not matching.empty:
                    synonyms = matching["SINONIMO"].unique().tolist()
        
        except KeyError:
            # Coluna SINONIMO não existe, silenciosamente retorna vazio
            pass
        except Exception as e:
            # Log apenas se for erro real, não KeyError
            pass
        
        return synonyms
    
    def search_occupations(self, query: str, limit: int = 10) -> List[Dict]:
        """Busca ocupações por termo (busca textual)"""
        
        if self.ocupacoes_df is None:
            return []
        
        results = []
        try:
            # Busca case-insensitive
            mask = self.ocupacoes_df["TITULO"].str.lower().str.contains(
                query.lower(), 
                na=False
            )
            
            matching = self.ocupacoes_df[mask].head(limit)
            
            for _, row in matching.iterrows():
                results.append({
                    "codigo": row["CODIGO"],
                    "titulo": row["TITULO"],
                    "relevancia": len(query) / len(row["TITULO"])  # Score simplificado
                })
            
            # Ordenar por relevância
            results.sort(key=lambda x: x["relevancia"], reverse=True)
        
        except Exception as e:
            logger.error(f"Erro ao buscar ocupações: {str(e)}")
        
        return results
