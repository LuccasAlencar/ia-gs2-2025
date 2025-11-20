"""
Serviço de extração completa de habilidades do currículo
Combina Regex, LLM e BERT para máxima precisão
"""

import re
from typing import List, Dict, Tuple, Optional
from app.models.cbo_loader import CBODataLoader
from app.models.skills_matcher import SkillsMatcher
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class SkillExtractionService:
    """Serviço completo de extração de habilidades do texto do currículo"""
    
    # Padrões regex para extração básica de skills
    SKILL_PATTERNS = {
        'linguagens': r'\b(Python|Java|C\+\+|JavaScript|TypeScript|C#|PHP|Ruby|Go|Rust|Kotlin|Swift|Objective-C|R|MATLAB|Scala|Groovy|Clojure|Elixir|Haskell|Lisp|Lua|Perl|Shell|Bash|PowerShell|VB\.NET|F#)\b',
        'frameworks': r'\b(Django|Flask|FastAPI|Spring|Spring Boot|React|Vue|Angular|Svelte|Next\.js|Nuxt|Express|Fastify|Laravel|Symfony|ASP\.NET|Struts|Hibernate|SQLAlchemy|Sequelize|Knex|Jest|Pytest|JUnit|RSpec|Mocha|Jasmine)\b',
        'bancos_dados': r'\b(MySQL|PostgreSQL|Oracle|SQL Server|MongoDB|Redis|Elasticsearch|Cassandra|DynamoDB|Firebase|SQLite|MariaDB|CouchDB|Neo4j|Memcached|Cassandra|Hive|Spark SQL|BigQuery|Snowflake)\b',
        'cloud': r'\b(AWS|Azure|Google Cloud|GCP|Heroku|DigitalOcean|Linode|IBM Cloud|Oracle Cloud|Alibaba Cloud|AWS Lambda|Azure Functions|Google Functions|EC2|S3|RDS|CloudFront|Route 53)\b',
        'devops': r'\b(Docker|Kubernetes|Jenkins|GitLab CI|GitHub Actions|CircleCI|Travis CI|Terraform|Ansible|Puppet|Chef|Vagrant|CloudFormation|Helm|ArgoCD|ECS|EKS|AKS)\b',
        'controle_versao': r'\b(Git|GitHub|GitLab|Bitbucket|SVN|Mercurial|Perforce)\b',
        'metodologias': r'\b(Agile|Scrum|Kanban|XP|Waterfall|CI\/CD|TDD|BDD|DDD|Clean Code|Design Patterns|SOLID|REST|GraphQL)\b',
        'microsoft_stack': r'\b(\.NET|ASP\.NET|C#|LINQ|Entity Framework|MS SQL|Azure DevOps|Visual Studio|Windows Server|Active Directory|SharePoint|Exchange|Teams|Office 365)\b',
        'jvm': r'\b(Java|Scala|Kotlin|Groovy|Clojure|JVM)\b',
        'mobile': r'\b(Android|iOS|Swift|Kotlin|React Native|Flutter|Xamarin|Ionic)\b',
        'dados': r'\b(Pandas|NumPy|SciPy|Scikit-learn|TensorFlow|PyTorch|Keras|Apache Spark|Hadoop|Hive|Pig|Tableau|Power BI|Looker|Alteryx|Data Science|Machine Learning|Deep Learning|NLP|Computer Vision)\b',
        'qualidade': r'\b(Selenium|Cypress|Postman|JMeter|LoadRunner|SoapUI|TestNG|Cucumber|Robot Framework|Gherkin)\b'
    }
    
    def __init__(self, model_name: str = "sentence-transformers/distiluse-base-multilingual-cased-v2"):
        """
        Inicializa o serviço de extração
        
        Args:
            model_name: Nome do modelo Sentence Transformers
        """
        logger.info("Inicializando SkillExtractionService...")
        
        self.cbo_loader = CBODataLoader()
        self.skills_matcher = SkillsMatcher(model_name)
        
        # Construir corpus com habilidades do CBO
        all_skills = self.cbo_loader.get_all_skills()
        
        if all_skills:
            self.skills_matcher.build_corpus(all_skills)
            logger.info(f"Corpus BERT construído com {len(all_skills)} habilidades")
        else:
            logger.warning("Nenhuma habilidade foi carregada do CBO")
        
        logger.info("SkillExtractionService inicializado com sucesso")
    
    def extract_skills_via_regex(self, text: str) -> List[str]:
        """
        Extrai skills usando padrões regex
        
        Args:
            text: Texto do currículo
            
        Returns:
            Lista de skills encontradas
        """
        skills = set()
        text_lower = text.lower()
        
        for category, pattern in self.SKILL_PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                skill = match.group(0).strip()
                if skill:
                    skills.add(skill)
        
        logger.info(f"Regex encontrou {len(skills)} skills: {skills}")
        return list(skills)
    
    def extract_skills_via_llm(self, text: str) -> List[str]:
        """
        Extrai skills usando LLM local (via regex refinado)
        Nota: Para verdadeira integração LLM, adicionar Ollama/LLaMA aqui
        
        Args:
            text: Texto do currículo
            
        Returns:
            Lista de skills extraídas
        """
        # Por enquanto, usamos padrões mais sofisticados
        # Buscar por padrões como "X anos de experiência com Y"
        
        skills = set()
        
        # Padrão: "X anos de experiência com [skill]" - mais restritivo
        # Captura apenas após "experiência com" ou similar
        pattern1 = r'(?:\d+\s*(?:anos?|meses))\s+(?:de\s+)?(?:experiência|atuação|trabalho)\s+(?:com|em|como)\s+([a-zA-Z0-9\s\-\+]+?)(?:[\.\,\;]|$)'
        matches = re.finditer(pattern1, text, re.IGNORECASE)
        for match in matches:
            if match.group(1):
                skill = match.group(1).strip()
                # Filtrar skills muito curtos ou muito longos, e com muitas palavras
                if 3 < len(skill) < 80 and len(skill.split()) <= 4:
                    skills.add(skill)
        
        # Padrão: "proficiente em [skill]" - mais restritivo
        # Apenas palavras depois de "proficiente em/de"
        pattern2 = r'(?:proficiente|expertise|especialista|conhecimento profundo|domínio)\s+(?:em|de|com)\s+([a-zA-Z0-9\s\-\+]+?)(?:[\.\,\;]|\s+e\s+|$)'
        matches = re.finditer(pattern2, text, re.IGNORECASE)
        for match in matches:
            if match.group(1):
                skill = match.group(1).strip()
                # Filtrar skills muito curtos ou muito longos
                if 3 < len(skill) < 80 and len(skill.split()) <= 4:
                    skills.add(skill)
        
        # Padrão: "especialista em [skill]" - mais restritivo
        pattern3 = r'(?:especialista|especialização|especializado)\s+(?:em|de)\s+([a-zA-Z0-9\s\-\+]+?)(?:[\.\,\;]|$)'
        matches = re.finditer(pattern3, text, re.IGNORECASE)
        for match in matches:
            if match.group(1):
                skill = match.group(1).strip()
                if 3 < len(skill) < 80 and len(skill.split()) <= 4:
                    skills.add(skill)
        
        logger.info(f"LLM (regex avançado) encontrou {len(skills)} skills: {skills}")
        return list(skills)
    
    def match_skills_with_bert(self, skills: List[str], threshold: float = 0.75, top_k: int = 1) -> List[Dict]:
        """
        Mapeia skills encontradas para o corpus CBO usando BERT
        
        Args:
            skills: Lista de skills para mapear
            threshold: Score mínimo de similaridade
            top_k: Número máximo de matches
            
        Returns:
            Lista de skills mapeadas com scores
        """
        if not skills:
            return []
        
        if not self.skills_matcher.is_corpus_ready():
            logger.error("Modelo BERT não está pronto")
            return []
        
        # Filtrar skills válidas (não None, não vazias)
        valid_skills = [s for s in skills if s and isinstance(s, str) and s.strip()]
        
        if not valid_skills:
            return []
        
        matched = []
        
        for skill in valid_skills:
            # Garantir que skill é string e não vazia
            skill = str(skill).strip()
            if not skill:
                continue
            
            # Encontrar similar no corpus CBO
            results = self.skills_matcher.find_similar(skill, top_k=top_k, threshold=threshold)
            
            if results:
                best_match = results[0]  # Melhor match
                matched.append({
                    "original": skill,
                    "matched_skill": best_match[0],
                    "similarity_score": float(best_match[1]),
                    "confidence": "high" if best_match[1] > 0.85 else "medium"
                })
            else:
                matched.append({
                    "original": skill,
                    "matched_skill": None,
                    "similarity_score": 0.0,
                    "confidence": "low",
                    "reason": "Sem match acima do threshold"
                })
        
        logger.info(f"BERT mapeou {len([m for m in matched if m['matched_skill']])} de {len(matched)} skills")
        return matched
    
    def extract_resume_skills(
        self,
        resume_text: str,
        threshold: float = 0.75,
        top_k: int = 1
    ) -> Dict:
        """
        Extração completa de skills do currículo usando 3 métodos
        
        Args:
            resume_text: Texto completo do currículo
            threshold: Score mínimo de similaridade BERT
            top_k: Número máximo de matches BERT
            
        Returns:
            Dicionário com skills extraídas e mapeadas
        """
        logger.info("Iniciando extração completa de skills do currículo...")
        
        try:
            # Passo 1: Regex (rápido)
            regex_skills = self.extract_skills_via_regex(resume_text)
            logger.info(f"Regex retornou: {regex_skills}")
            
            # Passo 2: LLM avançado (padrões sofisticados)
            llm_skills = self.extract_skills_via_llm(resume_text)
            logger.info(f"LLM retornou: {llm_skills}")
            
            # Combinar e deduplica
            all_skills = list(set(regex_skills + llm_skills))
            logger.info(f"Total de skills encontrados (Regex + LLM): {len(all_skills)}")
            
            # Passo 3: Mapear para CBO usando BERT
            mapped_skills = self.match_skills_with_bert(all_skills, threshold=threshold, top_k=top_k)
            
            # Contar matches bem-sucedidos
            successful_matches = len([m for m in mapped_skills if m['matched_skill']])
            
            return {
                "total_skills_found": len(all_skills),
                "successful_matches": successful_matches,
                "match_rate": f"{(successful_matches / len(all_skills) * 100):.1f}%" if all_skills else "0%",
                "skills": mapped_skills
            }
        except Exception as e:
            logger.error(f"Erro em extract_resume_skills: {str(e)}", exc_info=True)
            raise
    
    def calculate_profile_match(
        self,
        candidate_skills: List[str],
        job_requirements: List[str],
        weight_match: float = 0.7,
        weight_similarity: float = 0.3
    ) -> Dict:
        """
        Calcula percentual de adequação do candidato à vaga
        
        Args:
            candidate_skills: Skills que o candidato possui
            job_requirements: Skills requeridas para a vaga
            weight_match: Peso para matches exatos (0-1)
            weight_similarity: Peso para similaridade semântica (0-1)
            
        Returns:
            Dicionário com score de adequação e análise detalhada
        """
        if not job_requirements:
            return {"error": "Nenhum requisito fornecido"}
        
        if not candidate_skills:
            return {
                "match_score": 0.0,
                "match_percentage": "0%",
                "required_skills": job_requirements,
                "matched_skills": [],
                "missing_skills": job_requirements,
                "analysis": "Candidato não possui nenhuma skill mapeada"
            }
        
        candidate_skills_lower = [s.lower() for s in candidate_skills]
        job_requirements_lower = [s.lower() for s in job_requirements]
        
        matched_skills = []
        missing_skills = []
        scores = []
        
        # Verificar cada requisito
        for requirement in job_requirements:
            req_lower = requirement.lower()
            
            # Buscar match exato ou similaridade BERT
            exact_match = any(req_lower in cs or cs in req_lower for cs in candidate_skills_lower)
            
            if exact_match:
                matched_skills.append(requirement)
                scores.append(1.0)
            else:
                # Tentar BERT match
                bert_results = self.skills_matcher.find_similar(requirement, top_k=1, threshold=0.70)
                
                if bert_results:
                    matched_skill, score = bert_results[0]
                    if matched_skill.lower() in candidate_skills_lower:
                        matched_skills.append(requirement)
                        scores.append(float(score))
                    else:
                        missing_skills.append(requirement)
                else:
                    missing_skills.append(requirement)
        
        # Calcular score
        if scores:
            avg_score = sum(scores) / len(job_requirements)
        else:
            avg_score = 0.0
        
        match_percentage = min(100, int(avg_score * 100))
        
        # Determinar nível de adequação
        if match_percentage >= 90:
            level = "EXCELENTE - Candidato altamente qualificado"
        elif match_percentage >= 75:
            level = "BOM - Candidato bem qualificado"
        elif match_percentage >= 60:
            level = "MODERADO - Candidato com experiência relevante"
        elif match_percentage >= 40:
            level = "BAIXO - Candidato precisaria de treinamento"
        else:
            level = "INSUFICIENTE - Falta experiência significativa"
        
        return {
            "match_score": float(avg_score),
            "match_percentage": f"{match_percentage}%",
            "level": level,
            "matched_skills": matched_skills,
            "matched_count": len(matched_skills),
            "missing_skills": missing_skills,
            "missing_count": len(missing_skills),
            "required_skills": job_requirements,
            "required_count": len(job_requirements),
            "analysis": {
                "strengths": f"Possui {len(matched_skills)} das {len(job_requirements)} skills requeridas",
                "gaps": f"Faltam {len(missing_skills)} skills",
                "recommendation": "Forte candidato" if match_percentage >= 75 else "Candidato em desenvolvimento"
            }
        }
