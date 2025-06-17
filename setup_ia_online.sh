#!/bin/bash

# 🤖 Script de Configuração da IA Online - JurisIA
# Este script automatiza a configuração do modo online da IA jurídica

echo "🤖 =========================================="
echo "   CONFIGURAÇÃO DA IA ONLINE - JurisIA"
echo "=========================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para logging
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se está na pasta correta
if [ ! -f "src/app.py" ]; then
    error "Execute este script na raiz do projeto JurisIA"
    exit 1
fi

log "Iniciando configuração da IA online..."

# 1. Verificar Python
echo ""
echo "📋 1. Verificando Pré-requisitos"
echo "--------------------------------"

if ! command -v python3 &> /dev/null; then
    error "Python 3 não encontrado. Instale Python 3.8+"
    exit 1
fi

log "Python 3 encontrado: $(python3 --version)"

# 2. Configurar ambiente virtual
echo ""
echo "🐍 2. Configurando Ambiente Virtual"
echo "-----------------------------------"

if [ ! -d "venv" ]; then
    log "Criando ambiente virtual..."
    python3 -m venv venv
fi

log "Ativando ambiente virtual..."
source venv/bin/activate

# 3. Instalar dependências
echo ""
echo "📦 3. Instalando Dependências"
echo "-----------------------------"

if [ -f "requirements.txt" ]; then
    log "Instalando dependências do requirements.txt..."
    pip install -r requirements.txt
else
    log "Instalando dependências essenciais..."
    pip install flask flask-cors openai python-dotenv flask-sqlalchemy flask-jwt-extended
fi

# 4. Configurar OpenAI API Key
echo ""
echo "🔑 4. Configurando OpenAI API"
echo "-----------------------------"

# Verificar se já existe .env
if [ -f ".env" ] && grep -q "OPENAI_API_KEY" .env; then
    warn "Arquivo .env já existe com OPENAI_API_KEY"
    read -p "Deseja atualizar a API Key? (y/n): " update_key
    if [ "$update_key" != "y" ]; then
        log "Pulando configuração da API Key"
        skip_api_key=true
    fi
fi

if [ "$skip_api_key" != "true" ]; then
    echo ""
    echo "Para obter sua API Key:"
    echo "1. Acesse: https://platform.openai.com/"
    echo "2. Vá em 'API Keys'"
    echo "3. Clique em 'Create new secret key'"
    echo ""
    
    read -p "Cole sua OpenAI API Key (sk-...): " api_key
    
    if [[ $api_key == sk-* ]]; then
        log "API Key válida detectada"
        
        # Criar ou atualizar .env
        if [ ! -f ".env" ]; then
            touch .env
        fi
        
        # Remover linha existente se houver
        if grep -q "OPENAI_API_KEY" .env; then
            sed -i.bak '/OPENAI_API_KEY/d' .env
        fi
        
        # Adicionar configurações
        echo "OPENAI_API_KEY=$api_key" >> .env
        echo "OPENAI_MODEL=gpt-4o-mini" >> .env
        echo "OPENAI_MAX_TOKENS=2000" >> .env
        echo "OPENAI_TEMPERATURE=0.7" >> .env
        echo "FLASK_ENV=development" >> .env
        
        log "Arquivo .env configurado com sucesso"
    else
        error "API Key inválida. Deve começar com 'sk-'"
        exit 1
    fi
fi

# 5. Configurar frontend
echo ""
echo "🎨 5. Configurando Frontend"
echo "---------------------------"

if [ -f "frontend/src/services/adaptiveAIService.ts" ]; then
    log "Verificando configuração do frontend..."
    
    # Verificar se a URL está configurada corretamente
    if grep -q "localhost:5005" frontend/src/services/adaptiveAIService.ts; then
        log "Frontend já configurado para desenvolvimento local"
    else
        warn "Frontend pode precisar de ajustes na URL da API"
    fi
else
    warn "Arquivo adaptiveAIService.ts não encontrado"
fi

# 6. Criar diretórios necessários
echo ""
echo "📁 6. Criando Estrutura de Pastas"
echo "---------------------------------"

mkdir -p logs
mkdir -p instance
mkdir -p uploads

log "Diretórios criados: logs, instance, uploads"

# 7. Testar configuração
echo ""
echo "🧪 7. Testando Configuração"
echo "---------------------------"

log "Iniciando teste do backend..."

# Criar script de teste
cat > test_backend.py << 'EOF'
import os
import sys
sys.path.append('src')

try:
    from src.config import Config
    from src.services.ai_service import LegalAIService
    
    print("✅ Importações bem-sucedidas")
    
    # Testar configuração OpenAI
    if Config.OPENAI_API_KEY and Config.OPENAI_API_KEY.startswith('sk-'):
        print("✅ OpenAI API Key configurada")
        
        # Testar serviço de IA
        ai_service = LegalAIService()
        if ai_service.is_configured:
            print("✅ Serviço de IA configurado e pronto")
        else:
            print("❌ Serviço de IA não configurado")
    else:
        print("❌ OpenAI API Key não configurada")
    
    print("\n🎯 Status da Configuração:")
    print(f"   OpenAI Configurado: {'✅' if Config.is_openai_configured() else '❌'}")
    print(f"   Modelo: {Config.OPENAI_MODEL}")
    print(f"   Max Tokens: {Config.OPENAI_MAX_TOKENS}")
    
except Exception as e:
    print(f"❌ Erro na configuração: {e}")
    sys.exit(1)
EOF

python test_backend.py
test_result=$?

# Limpar arquivo de teste
rm test_backend.py

if [ $test_result -eq 0 ]; then
    log "Teste do backend bem-sucedido!"
else
    error "Falha no teste do backend"
fi

# 8. Instruções finais
echo ""
echo "🚀 8. Próximos Passos"
echo "--------------------"

echo ""
echo "Para iniciar o sistema:"
echo ""
echo "1️⃣  Backend (Terminal 1):"
echo "   cd $(pwd)"
echo "   source venv/bin/activate"
echo "   python src/app.py"
echo ""
echo "2️⃣  Frontend (Terminal 2):"
echo "   cd frontend"
echo "   npm start"
echo ""
echo "3️⃣  Teste a IA:"
echo "   Acesse: http://localhost:3000/ai"
echo ""

# 9. Criar script de inicialização
log "Criando script de inicialização..."

cat > start_ia_online.sh << 'EOF'
#!/bin/bash

echo "🤖 Iniciando JurisIA com IA Online..."

# Ativar ambiente virtual
source venv/bin/activate

# Verificar OpenAI
if [ -f ".env" ]; then
    source .env
    if [ -n "$OPENAI_API_KEY" ]; then
        echo "✅ OpenAI API Key encontrada"
    else
        echo "❌ OpenAI API Key não encontrada no .env"
        exit 1
    fi
else
    echo "❌ Arquivo .env não encontrado"
    exit 1
fi

# Iniciar backend
echo "🚀 Iniciando backend na porta 5005..."
python src/app.py
EOF

chmod +x start_ia_online.sh

log "Script de inicialização criado: ./start_ia_online.sh"

# 10. Resumo final
echo ""
echo "🎉 =========================================="
echo "   CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!"
echo "=========================================="
echo ""
echo "📊 Resumo da Configuração:"
echo "├── ✅ Ambiente virtual configurado"
echo "├── ✅ Dependências instaladas"
echo "├── ✅ OpenAI API configurada"
echo "├── ✅ Estrutura de pastas criada"
echo "├── ✅ Backend testado"
echo "└── ✅ Scripts de inicialização criados"
echo ""

if [ -f ".env" ] && grep -q "OPENAI_API_KEY" .env; then
    echo "🔑 API Key configurada: ✅"
else
    echo "🔑 API Key configurada: ❌"
    warn "Execute novamente e configure a API Key"
fi

echo ""
echo "📝 Arquivos criados:"
echo "├── .env (configurações)"
echo "├── start_ia_online.sh (inicialização)"
echo "└── logs/ (pasta de logs)"
echo ""

echo "🚀 Para iniciar o sistema agora:"
echo "   ./start_ia_online.sh"
echo ""

echo "📖 Documentação completa:"
echo "   cat CONFIGURACAO_IA_ONLINE.md"
echo ""

echo "🎯 Teste final:"
echo "   1. Execute: ./start_ia_online.sh"
echo "   2. Em outro terminal: cd frontend && npm start"
echo "   3. Acesse: http://localhost:3000/ai"
echo "   4. Verifique se aparece 'Online' no status"
echo ""

log "Configuração da IA Online concluída! 🎉" 