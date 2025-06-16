#!/bin/bash

# Script para inicializar o JurisIA
# Uso: ./start_project.sh

echo "🏛️ Iniciando JurisIA - Plataforma Jurídica com IA"
echo "======================================================="

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para print colorido
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

# Verificar se o venv está ativo
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_warning "Ambiente virtual não está ativo. Ativando..."
    source venv/bin/activate
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        print_error "Não foi possível ativar o ambiente virtual."
        print_error "Execute: source venv/bin/activate"
        exit 1
    fi
fi

print_success "Ambiente virtual ativo: $VIRTUAL_ENV"

# Configurar variáveis de ambiente
export DATABASE_URL="sqlite:///$(pwd)/src/jurissaas.db"
print_status "DATABASE_URL configurado: $DATABASE_URL"

# Verificar se o banco existe
if [ ! -f "src/jurissaas.db" ]; then
    print_warning "Banco de dados não encontrado. Criando..."
    cd src
    python -c "
from main import create_app
from extensions import db
app = create_app()
with app.app_context():
    db.create_all()
    print('✅ Banco criado!')
"
    cd ..
fi

# Verificar porta 5005
PORT_CHECK=$(lsof -ti:5005 2>/dev/null)
if [ ! -z "$PORT_CHECK" ]; then
    print_warning "Porta 5005 em uso. Liberando..."
    kill -9 $PORT_CHECK 2>/dev/null
    sleep 2
fi

print_success "Porta 5005 disponível"

# Função para iniciar backend
start_backend() {
    print_status "Iniciando servidor backend na porta 5005..."
    cd src
    python main.py &
    BACKEND_PID=$!
    cd ..
    echo $BACKEND_PID > .backend_pid
    print_success "Backend iniciado (PID: $BACKEND_PID)"
}

# Função para iniciar frontend
start_frontend() {
    if [ -d "frontend" ]; then
        print_status "Iniciando frontend na porta 3005..."
        cd frontend
        
        # Verificar se node_modules existe
        if [ ! -d "node_modules" ]; then
            print_warning "Dependências do frontend não instaladas. Instalando..."
            npm install --registry=https://registry.npmjs.org/
        fi
        
        # Usar script específico para porta 3005
        npm run start:alt &
        FRONTEND_PID=$!
        cd ..
        echo $FRONTEND_PID > .frontend_pid
        print_success "Frontend iniciado (PID: $FRONTEND_PID)"
    else
        print_warning "Pasta frontend não encontrada"
    fi
}

# Função para parar serviços
stop_services() {
    print_status "Parando serviços..."
    
    if [ -f ".backend_pid" ]; then
        BACKEND_PID=$(cat .backend_pid)
        kill $BACKEND_PID 2>/dev/null
        rm .backend_pid
        print_success "Backend parado"
    fi
    
    if [ -f ".frontend_pid" ]; then
        FRONTEND_PID=$(cat .frontend_pid)
        kill $FRONTEND_PID 2>/dev/null
        rm .frontend_pid
        print_success "Frontend parado"
    fi
}

# Capturar Ctrl+C para parar serviços
trap stop_services EXIT

# Verificar argumentos
case "${1:-start}" in
    "start")
        print_status "Iniciando aplicação completa..."
        start_backend
        sleep 3
        start_frontend
        
        echo ""
        echo "🎉 Aplicação iniciada com sucesso!"
        echo "=================================="
        echo "📱 Frontend: http://localhost:3005"
        echo "🔧 Backend:  http://localhost:5005"
        echo "📚 API:      http://localhost:5005/api"
        echo ""
        echo "👤 Usuário admin:"
        echo "📧 Email: admin@jurissaas.com"
        echo "🔑 Senha: admin123"
        echo ""
        echo "Pressione Ctrl+C para parar..."
        
        # Aguardar
        wait
        ;;
    "backend")
        start_backend
        echo "Backend rodando em http://localhost:5005"
        echo "Pressione Ctrl+C para parar..."
        wait
        ;;
    "frontend")
        start_frontend
        echo "Frontend rodando em http://localhost:3005"
        echo "Pressione Ctrl+C para parar..."
        wait
        ;;
    "stop")
        stop_services
        exit 0
        ;;
    *)
        echo "Uso: $0 [start|backend|frontend|stop]"
        echo ""
        echo "Comandos:"
        echo "  start    - Inicia backend e frontend (padrão)"
        echo "  backend  - Inicia apenas o backend"
        echo "  frontend - Inicia apenas o frontend"
        echo "  stop     - Para todos os serviços"
        exit 1
        ;;
esac 