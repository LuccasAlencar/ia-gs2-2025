"""
Script de teste da API
Testa os principais endpoints
"""

import requests
import json
import time

API_URL = "http://localhost:5001/api/v1"

def test_health():
    """Testa health check"""
    print("\n🏥 Testando Health Check...")
    response = requests.get(f"{API_URL}/health/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200


def test_model_info():
    """Testa informações do modelo"""
    print("\n🤖 Testando Model Info...")
    response = requests.get(f"{API_URL}/skills/model-info")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    assert response.status_code == 200
    assert data["status"] == "success"


def test_match_skills():
    """Testa matching de habilidades"""
    print("\n🎯 Testando Skill Matching...")
    
    payload = {
        "unrecognized_skills": [
            "Web3 Developer",
            "Cloud DevOps Engineer",
            "Chef executivo",
            "Data scientist"
        ],
        "top_k": 3,
        "threshold": 0.60
    }
    
    response = requests.post(
        f"{API_URL}/skills/match",
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Processing time: {data.get('processing_time_seconds')}s")
    
    for skill, results in data.get("results", {}).items():
        print(f"\n  Skill: {skill}")
        print(f"  Matched: {results['matched']}")
        if results['matches']:
            for match in results['matches'][:2]:
                print(f"    - {match['matched_skill']} ({match['similarity_score']})")
    
    assert response.status_code == 200
    assert data["status"] == "success"


def test_enrich_profile():
    """Testa enriquecimento de perfil"""
    print("\n💼 Testando Enrich Profile...")
    
    payload = {
        "skills": ["Java", "Python", "SQL", "Docker"],
        "confidence_threshold": 0.60
    }
    
    response = requests.post(
        f"{API_URL}/skills/enrich",
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Processing time: {data.get('processing_time_seconds')}s")
    
    if "data" in data:
        skills = data["data"]["skills_processed"]
        for skill in skills[:2]:
            print(f"\n  {skill['original']}")
            print(f"  Recognized: {skill['is_recognized']}")
            if skill['high_confidence_matches']:
                print(f"  Matches: {skill['high_confidence_matches'][:1]}")
    
    assert response.status_code == 200


def test_occupations():
    """Testa busca de ocupações"""
    print("\n🏢 Testando Occupations Search...")
    
    payload = {
        "skills": ["Python", "Machine Learning", "Data Analysis"],
        "limit": 5
    }
    
    response = requests.post(
        f"{API_URL}/skills/occupations",
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Occupations found: {data['data'].get('occupations_found')}")
    
    for occ in data["data"].get("occupations", [])[:3]:
        print(f"  - {occ['titulo']} ({occ['codigo']})")
    
    assert response.status_code == 200


def test_similarity():
    """Testa cálculo de similaridade"""
    print("\n📊 Testando Similarity Calculation...")
    
    payload = {
        "text1": "Python Developer",
        "text2": "Desenvolvedor Python"
    }
    
    response = requests.post(
        f"{API_URL}/skills/similarity",
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Similarity: {data.get('similarity_score')}")
    
    assert response.status_code == 200


def main():
    """Executa todos os testes"""
    print("=" * 60)
    print("IA Skills Matcher API - Test Suite")
    print("=" * 60)
    
    try:
        # Verificar se API está rodando
        print("\n⏳ Verificando conexão com API...")
        response = requests.get(f"{API_URL}/health/", timeout=5)
        if response.status_code != 200:
            print("❌ API não está respondendo")
            return
        
        print("✅ API está rodando!")
        
        # Aguardar modelo carregar
        print("\n⏳ Aguardando modelo carregar (primeira execução pode levar 1-2 minutos)...")
        time.sleep(5)
        
        # Executar testes
        test_health()
        test_model_info()
        test_similarity()
        test_match_skills()
        test_enrich_profile()
        test_occupations()
        
        print("\n" + "=" * 60)
        print("✅ Todos os testes passaram!")
        print("=" * 60)
    
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API")
        print("   Certifique-se que a API está rodando em http://localhost:5001")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")


if __name__ == "__main__":
    main()
