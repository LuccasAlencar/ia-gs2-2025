#!/bin/bash
# Setup simples - Python API (Git Bash)

echo ""
echo "Setup IA Skills Matcher"
echo ""

# Encontrar python
if command -v python &> /dev/null; then
    PYTHON_CMD="python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "ERRO: Python não encontrado"
    exit 1
fi

echo "Python: $PYTHON_CMD"
echo ""

# 1. Criar venv
echo "1. Criando ambiente virtual..."
$PYTHON_CMD -m venv venv
if [ $? -eq 0 ]; then
    echo "✓ OK"
else
    echo "✗ ERRO ao criar venv"
    exit 1
fi

# 2. Ativar e instalar
echo "2. Instalando dependências (aguarde 3-5 min)..."
source venv/Scripts/activate
if [ $? -ne 0 ]; then
    source venv/bin/activate
fi

pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✓ OK"
else
    echo "✗ ERRO ao instalar dependências"
    exit 1
fi

# 3. Criar .env
echo "3. Configurando .env..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✓ OK"
    else
        echo "⚠ .env.example não encontrado"
    fi
else
    echo "✓ .env já existe"
fi

# 4. Criar logs
mkdir -p logs

# 5. Pronto
echo ""
echo "================================"
echo "✓ PRONTO!"
echo "================================"
echo ""
echo "Para iniciar a API:"
echo "  python run.py"
echo ""
echo "Para testes:"
echo "  python test_api.py"
echo ""
