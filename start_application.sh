#!/bin/bash

# Configuração de cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Função para imprimir cabeçalhos coloridos
print_header() {
    echo -e "\n${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}\n"
}

# Função para executar comandos com verificação de erro
run_command() {
    echo -e "${YELLOW}Executando: $1${NC}"
    if eval "$1"; then
        echo -e "${GREEN}✅ $2 executado com sucesso${NC}"
        return 0
    else
        echo -e "${RED}❌ Erro ao executar $2${NC}"
        return 1
    fi
}

# Função para verificar se uma porta está em uso
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Função para matar processo em uma porta
kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port)
    if [ -n "$pid" ]; then
        echo -e "${YELLOW}Matando processo na porta $port (PID: $pid)${NC}"
        kill -9 $pid 2>/dev/null
        sleep 2
    fi
}

# Início do script
clear
print_header "🚀 JURISSAAS - SISTEMA DE INICIALIZAÇÃO AUTOMÁTICA"

echo -e "${PURPLE}Desenvolvido para automatizar a inicialização completa da aplicação${NC}"
echo -e "${PURPLE}Backend: Flask + Python | Frontend: React + TypeScript${NC}\n"

# Verificar se estamos no diretório correto
if [ ! -f "package.json" ] || [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Erro: Execute este script no diretório raiz do projeto${NC}"
    echo -e "${RED}   Certifique-se de que package.json e requirements.txt existem${NC}"
    exit 1
fi

# Verificar Node.js
print_header "🔍 Verificando dependências do sistema"
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js não encontrado. Instale o Node.js antes de continuar.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Node.js encontrado: $(node --version)${NC}"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 não encontrado. Instale o Python3 antes de continuar.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python3 encontrado: $(python3 --version)${NC}"

# Verificar npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm não encontrado. Instale o npm antes de continuar.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ npm encontrado: $(npm --version)${NC}"

# Criar diretórios necessários
print_header "📁 Criando estrutura de diretórios"
run_command "mkdir -p logs src/instance uploads" "Criação de diretórios"

# Criar arquivo de log
touch logs/application.log

# Limpar portas se estiverem em uso
print_header "🔧 Verificando e limpando portas"
if check_port 3000; then
    echo -e "${YELLOW}⚠️  Porta 3000 em uso. Liberando...${NC}"
    kill_port 3000
fi

if check_port 5001; then
    echo -e "${YELLOW}⚠️  Porta 5001 em uso. Liberando...${NC}"
    kill_port 5001
fi

# Configurar ambiente virtual Python
print_header "🐍 Configurando ambiente Python"
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Criando ambiente virtual...${NC}"
    run_command "python3 -m venv venv" "Criação do ambiente virtual"
else
    echo -e "${GREEN}✅ Ambiente virtual já existe${NC}"
fi

# Ativar ambiente virtual
echo -e "${YELLOW}Ativando ambiente virtual...${NC}"
source venv/bin/activate
echo -e "${GREEN}✅ Ambiente virtual ativado${NC}"

# Instalar dependências Python
print_header "📦 Instalando dependências Python"
run_command "pip install --upgrade pip" "Atualização do pip"
run_command "pip install -r requirements.txt" "Instalação de dependências Python"

# Instalar dependências adicionais para WeasyPrint (se necessário)
echo -e "${YELLOW}Instalando dependências adicionais para WeasyPrint...${NC}"
run_command "pip install weasyprint tinycss2 cssselect2 html5lib" "Instalação de dependências adicionais"

# Configurar variáveis de ambiente
print_header "⚙️  Configurando ambiente"
if [ ! -f ".env" ]; then
    if [ -f "env.template" ]; then
        echo -e "${YELLOW}Criando arquivo .env a partir do template...${NC}"
        cp env.template .env
        echo -e "${GREEN}✅ Arquivo .env criado${NC}"
        echo -e "${YELLOW}⚠️  Lembre-se de configurar suas variáveis de ambiente no arquivo .env${NC}"
    else
        echo -e "${YELLOW}⚠️  Arquivo env.template não encontrado. Criando .env básico...${NC}"
        cat > .env << EOF
FLASK_ENV=development
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(16))')
DATABASE_URL=sqlite:///jurissaas.db
OPENAI_API_KEY=your_openai_key_here
JWT_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(16))')
EOF
        echo -e "${GREEN}✅ Arquivo .env básico criado${NC}"
    fi
else
    echo -e "${GREEN}✅ Arquivo .env já existe${NC}"
fi

# Inicializar banco de dados
print_header "📊 Inicializando banco de dados"
if [ -f "src/init_db_simple.py" ]; then
    run_command "cd src && python init_db_simple.py" "Inicialização do banco de dados"
elif [ -f "src/init_db.py" ]; then
    run_command "cd src && python init_db.py" "Inicialização do banco de dados"
else
    echo -e "${RED}❌ Arquivo de inicialização do banco não encontrado${NC}"
    exit 1
fi

# Instalar dependências Node.js
print_header "📦 Instalando dependências Node.js"
if [ ! -d "node_modules" ]; then
    run_command "npm install" "Instalação de dependências Node.js"
else
    echo -e "${GREEN}✅ node_modules já existe. Verificando atualizações...${NC}"
    run_command "npm update" "Atualização de dependências Node.js"
fi

# Criar arquivo de PIDs para controle de processos
echo $$ > logs/main.pid

# Função para cleanup
cleanup() {
    echo -e "\n${YELLOW}🛑 Interrompendo aplicação...${NC}"
    
    # Matar processos em background
    if [ -f "logs/backend.pid" ]; then
        backend_pid=$(cat logs/backend.pid)
        if ps -p $backend_pid > /dev/null 2>&1; then
            echo -e "${YELLOW}Parando backend (PID: $backend_pid)...${NC}"
            kill $backend_pid 2>/dev/null
        fi
        rm -f logs/backend.pid
    fi
    
    if [ -f "logs/frontend.pid" ]; then
        frontend_pid=$(cat logs/frontend.pid)
        if ps -p $frontend_pid > /dev/null 2>&1; then
            echo -e "${YELLOW}Parando frontend (PID: $frontend_pid)...${NC}"
            kill $frontend_pid 2>/dev/null
        fi
        rm -f logs/frontend.pid
    fi
    
    # Cleanup adicional
    kill_port 3000
    kill_port 5001
    
    rm -f logs/main.pid
    
    echo -e "${GREEN}✅ Cleanup concluído${NC}"
    exit 0
}

# Configurar trap para cleanup
trap cleanup SIGINT SIGTERM

# Iniciar backend
print_header "🔧 Iniciando Backend (Flask)"
cd src
python main.py > ../logs/backend.log 2>&1 &
backend_pid=$!
echo $backend_pid > ../logs/backend.pid
cd ..

echo -e "${GREEN}✅ Backend iniciado (PID: $backend_pid)${NC}"
echo -e "${BLUE}📝 Logs do backend: logs/backend.log${NC}"

# Aguardar backend inicializar
echo -e "${YELLOW}⏳ Aguardando backend inicializar...${NC}"
sleep 5

# Verificar se backend está rodando
backend_attempts=0
max_attempts=10

while [ $backend_attempts -lt $max_attempts ]; do
    if check_port 5001; then
        echo -e "${GREEN}✅ Backend está respondendo na porta 5001${NC}"
        break
    else
        echo -e "${YELLOW}⏳ Tentativa $((backend_attempts + 1))/$max_attempts - Aguardando backend...${NC}"
        sleep 3
        backend_attempts=$((backend_attempts + 1))
    fi
done

if [ $backend_attempts -eq $max_attempts ]; then
    echo -e "${RED}❌ Backend não conseguiu inicializar após $max_attempts tentativas${NC}"
    echo -e "${RED}📝 Verifique os logs em: logs/backend.log${NC}"
    cleanup
    exit 1
fi

# Teste de health check do backend
echo -e "${YELLOW}🔍 Testando health check do backend...${NC}"
if curl -s http://localhost:5001/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend health check passou${NC}"
else
    echo -e "${YELLOW}⚠️  Health check falhou, mas continuando...${NC}"
fi

# Iniciar frontend
print_header "⚛️  Iniciando Frontend (React)"
npm start > logs/frontend.log 2>&1 &
frontend_pid=$!
echo $frontend_pid > logs/frontend.pid

echo -e "${GREEN}✅ Frontend iniciado (PID: $frontend_pid)${NC}"
echo -e "${BLUE}📝 Logs do frontend: logs/frontend.log${NC}"

# Aguardar frontend inicializar
echo -e "${YELLOW}⏳ Aguardando frontend inicializar...${NC}"
sleep 10

# Verificar se frontend está rodando
frontend_attempts=0
max_attempts=15

while [ $frontend_attempts -lt $max_attempts ]; do
    if check_port 3000; then
        echo -e "${GREEN}✅ Frontend está respondendo na porta 3000${NC}"
        break
    else
        echo -e "${YELLOW}⏳ Tentativa $((frontend_attempts + 1))/$max_attempts - Aguardando frontend...${NC}"
        sleep 3
        frontend_attempts=$((frontend_attempts + 1))
    fi
done

if [ $frontend_attempts -eq $max_attempts ]; then
    echo -e "${RED}❌ Frontend não conseguiu inicializar após $max_attempts tentativas${NC}"
    echo -e "${RED}📝 Verifique os logs em: logs/frontend.log${NC}"
    cleanup
    exit 1
fi

# Sucesso!
print_header "🎉 APLICAÇÃO INICIADA COM SUCESSO!"

echo -e "${GREEN}✅ Backend rodando em: ${CYAN}http://localhost:5001${NC}"
echo -e "${GREEN}✅ Frontend rodando em: ${CYAN}http://localhost:3000${NC}"
echo -e ""
echo -e "${PURPLE}📋 INFORMAÇÕES DE LOGIN:${NC}"
echo -e "${YELLOW}📧 Email: admin@jurissaas.com${NC}"
echo -e "${YELLOW}🔑 Senha: admin123${NC}"
echo -e ""
echo -e "${BLUE}📊 STATUS DOS SERVIÇOS:${NC}"
echo -e "${GREEN}🔧 Backend: Ativo (PID: $backend_pid)${NC}"
echo -e "${GREEN}⚛️  Frontend: Ativo (PID: $frontend_pid)${NC}"
echo -e ""
echo -e "${CYAN}📝 LOGS DISPONÍVEIS:${NC}"
echo -e "${BLUE}   • Backend: logs/backend.log${NC}"
echo -e "${BLUE}   • Frontend: logs/frontend.log${NC}"
echo -e "${BLUE}   • Aplicação: logs/application.log${NC}"
echo -e ""
echo -e "${YELLOW}💡 DICAS:${NC}"
echo -e "${YELLOW}   • Use Ctrl+C para parar a aplicação${NC}"
echo -e "${YELLOW}   • Acesse http://localhost:3000 no seu navegador${NC}"
echo -e "${YELLOW}   • Verifique os logs se houver problemas${NC}"
echo -e ""

# Monitoramento dos processos
echo -e "${CYAN}🔍 Monitorando aplicação... (Ctrl+C para parar)${NC}\n"

while true; do
    # Verificar se os processos ainda estão rodando
    if ! ps -p $backend_pid > /dev/null 2>&1; then
        echo -e "${RED}❌ Backend parou inesperadamente!${NC}"
        cleanup
        exit 1
    fi
    
    if ! ps -p $frontend_pid > /dev/null 2>&1; then
        echo -e "${RED}❌ Frontend parou inesperadamente!${NC}"
        cleanup
        exit 1
    fi
    
    # Status a cada 30 segundos
    sleep 30
    echo -e "${GREEN}$(date '+%H:%M:%S') - ✅ Aplicação rodando normalmente${NC}"
done 