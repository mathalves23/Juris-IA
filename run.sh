#!/bin/bash

# Script simples para executar a aplicação JurisSaaS
# Uso: ./run.sh

echo "🏛️ Iniciando JurisIA - Plataforma Jurídica com IA"
echo "=============================================="

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Ativar ambiente virtual se existir
if [ -d "venv" ]; then
    echo -e "${BLUE}Ativando ambiente virtual...${NC}"
    source venv/bin/activate
fi

# Verificar se o processo já está rodando
if lsof -Pi :5005 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Backend já está rodando na porta 5005${NC}"
else
    echo -e "${BLUE}🚀 Iniciando backend...${NC}"
    cd src
    python main.py &
    BACKEND_PID=$!
    cd ..
    echo -e "${GREEN}✅ Backend iniciado (PID: $BACKEND_PID)${NC}"
fi

# Aguardar um pouco
sleep 3

# Mostrar informações
echo ""
echo -e "${GREEN}🎉 JurisSaaS está rodando!${NC}"
echo "=========================="
echo -e "${GREEN}🔧 Backend: ${BLUE}http://localhost:5005${NC}"
echo -e "${GREEN}📚 API: ${BLUE}http://localhost:5005/api${NC}"
echo ""
echo -e "${YELLOW}👤 Login de Admin:${NC}"
echo -e "📧 Email: ${BLUE}admin@jurissaas.com${NC}"
echo -e "🔑 Senha: ${BLUE}admin123${NC}"
echo ""
echo -e "${YELLOW}🔧 Funcionalidades implementadas:${NC}"
echo -e "   ✅ Sistema de autenticação"
echo -e "   ✅ Configuração de flags (setFlagsFromString)"
echo -e "   ✅ Gerenciamento de usuários"
echo -e "   ✅ API REST completa"
echo ""
echo -e "${BLUE}💡 Para parar: ${YELLOW}Ctrl+C ou execute: pkill -f 'python src/main.py'${NC}"

# Aguardar o processo
if [ ! -z "$BACKEND_PID" ]; then
    wait $BACKEND_PID
fi 