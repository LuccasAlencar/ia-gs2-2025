"""
Ponto de entrada da aplicação
Executa o servidor Flask
"""

import os
from dotenv import load_dotenv
from app import create_app
from app.utils.logger import setup_logger

# Carregar variáveis de ambiente
load_dotenv()

logger = setup_logger(__name__)


def main():
    """Função principal"""
    
    # Criar aplicação
    app = create_app()
    
    # Configurações
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 5001))
    debug = os.getenv("FLASK_ENV") == "development"
    
    logger.info(f"Iniciando servidor em {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    
    # Executar
    app.run(
        host=host,
        port=port,
        debug=debug,
        use_reloader=debug
    )


if __name__ == "__main__":
    main()
