#!/bin/bash

# Script para corrigir problemas do frontend
echo "🔧 Corrigindo problemas do frontend..."

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERRO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

# Parar processos nas portas 3000, 3005 e 5005
print_status "Parando processos nas portas 3000, 3005 e 5005..."
for port in 3000 3005 5005; do
    PIDS=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$PIDS" ]; then
        echo "Parando processos na porta $port: $PIDS"
        kill -9 $PIDS 2>/dev/null
    fi
done

print_success "Portas liberadas"

# Ir para a pasta frontend
if [ ! -d "frontend" ]; then
    print_error "Pasta frontend não encontrada!"
    exit 1
fi

cd frontend

# Limpar cache do npm
print_status "Limpando cache do npm..."
npm cache clean --force

# Remover node_modules e package-lock.json
print_status "Removendo node_modules e reinstalando dependências..."
rm -rf node_modules
rm -f package-lock.json

# Reinstalar dependências
print_status "Reinstalando dependências..."
npm install --registry=https://registry.npmjs.org/

# Criar arquivo .env local se não existir
if [ ! -f ".env.local" ]; then
    print_status "Criando arquivo .env.local..."
    cat > .env.local << EOF
# Configurações do Frontend
PORT=3005
BROWSER=none
SKIP_PREFLIGHT_CHECK=true

# URL da API
REACT_APP_API_URL=http://localhost:5005/api

# Outras configurações
REACT_APP_ENVIRONMENT=development
REACT_APP_VERSION=1.0.0
EOF
    print_success "Arquivo .env.local criado"
fi

# Voltar para a pasta raiz
cd ..

print_success "Frontend corrigido!"
print_status "Agora execute: ./start_project.sh" 