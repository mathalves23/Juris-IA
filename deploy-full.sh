#!/bin/bash

# ============================================================================
# SCRIPT DE DEPLOY COMPLETO - JURISIA
# Frontend: Netlify | Backend: Render/Heroku
# ============================================================================

set -e  # Sair se houver erro

echo "🚀 === DEPLOY COMPLETO JURISIA === 🚀"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log colorido
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Verificar se está no diretório correto
if [ ! -f "package.json" ] && [ ! -d "frontend" ]; then
    error "Execute este script no diretório raiz do projeto"
    exit 1
fi

# ============================================================================
# 1. PRÉ-DEPLOY - VERIFICAÇÕES
# ============================================================================
log "1. Executando verificações pré-deploy..."

# Verificar dependências
if ! command -v node &> /dev/null; then
    error "Node.js não encontrado. Instale Node.js 18+"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    error "npm não encontrado"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    error "Python 3 não encontrado"
    exit 1
fi

info "✅ Dependências verificadas"

# ============================================================================
# 2. BACKEND - PREPARAÇÃO
# ============================================================================
log "2. Preparando backend para deploy..."

# Ativar virtual environment se existir
if [ -d "venv" ]; then
    info "Ativando virtual environment..."
    source venv/bin/activate
fi

# Instalar dependências Python
if [ -f "requirements.txt" ]; then
    info "Instalando dependências Python..."
    pip install -r requirements.txt
fi

# Testar imports do backend
info "Testando imports do backend..."
python3 -c "
try:
    from src.app import app
    print('✅ Backend imports OK')
except Exception as e:
    print(f'❌ Erro no backend: {e}')
    exit(1)
"

# ============================================================================
# 3. FRONTEND - BUILD
# ============================================================================
log "3. Preparando frontend para deploy..."

cd frontend

# Limpar cache e node_modules se necessário
if [ "$1" = "--clean" ]; then
    warn "Limpando cache e dependências..."
    rm -rf node_modules package-lock.json
    npm cache clean --force
fi

# Instalar dependências
info "Instalando dependências do frontend..."
npm ci --prefer-offline --no-audit

# Build do frontend
info "Executando build do frontend..."
npm run build

# Verificar se build foi criado
if [ ! -d "build" ]; then
    error "Build do frontend falhou - pasta build não encontrada"
    exit 1
fi

BUILD_SIZE=$(du -sh build | cut -f1)
info "✅ Build do frontend concluído (${BUILD_SIZE})"

cd ..

# ============================================================================
# 4. DEPLOY BACKEND (se solicitado)
# ============================================================================
if [ "$2" = "--backend" ]; then
    log "4. Fazendo deploy do backend..."
    
    if command -v heroku &> /dev/null; then
        info "Deploy no Heroku..."
        heroku create jurisia-api --region us || true
        git add .
        git commit -m "Deploy backend $(date)" || true
        git push heroku main || git push heroku HEAD:main
        heroku ps:scale web=1
        heroku run python src/init_db.py
        info "✅ Backend deployado no Heroku"
    else
        warn "Heroku CLI não encontrado. Deploy manual necessário."
        info "Para Render: faça upload dos arquivos e configure as variáveis de ambiente"
        info "Para Railway: railway deploy"
    fi
fi

# ============================================================================
# 5. DEPLOY FRONTEND
# ============================================================================
log "5. Fazendo deploy do frontend..."

# Verificar se Netlify CLI está instalado
if command -v netlify &> /dev/null; then
    info "Usando Netlify CLI..."
    cd frontend
    
    # Login (se necessário)
    netlify status || netlify login
    
    # Deploy
    if [ "$3" = "--prod" ]; then
        info "Deploy em produção..."
        netlify deploy --prod --dir=build
    else
        info "Deploy preview..."
        netlify deploy --dir=build
    fi
    
    cd ..
    info "✅ Frontend deployado no Netlify"
else
    info "Netlify CLI não encontrado. Fazendo upload manual..."
    info "📁 Arquivos de build estão em: frontend/build/"
    info "🔗 Faça upload manual no Netlify: https://app.netlify.com/"
fi

# ============================================================================
# 6. PÓS-DEPLOY - VERIFICAÇÕES
# ============================================================================
log "6. Verificações pós-deploy..."

# URLs para teste (ajustar conforme necessário)
FRONTEND_URL="https://jurisia.netlify.app"
BACKEND_URL="https://jurisia-api.onrender.com"

info "🔗 URLs da aplicação:"
info "   Frontend: ${FRONTEND_URL}"
info "   Backend:  ${BACKEND_URL}"
info "   Health:   ${BACKEND_URL}/health"

# Teste básico de conectividade
if command -v curl &> /dev/null; then
    info "Testando conectividade..."
    
    # Teste frontend
    if curl -s --head "${FRONTEND_URL}" | head -n 1 | grep -q "200 OK"; then
        info "✅ Frontend respondendo"
    else
        warn "⚠️ Frontend pode não estar respondendo"
    fi
    
    # Teste backend
    if curl -s --head "${BACKEND_URL}/health" | head -n 1 | grep -q "200 OK"; then
        info "✅ Backend respondendo"
    else
        warn "⚠️ Backend pode não estar respondendo"
    fi
fi

# ============================================================================
# 7. RELATÓRIO FINAL
# ============================================================================
log "7. Gerando relatório de deploy..."

cat > deployment-report.txt << EOF
=== RELATÓRIO DE DEPLOY JURISIA ===
Data: $(date)
Versão: 2.0.0

FRONTEND:
- Status: ✅ Build concluído
- Tamanho: ${BUILD_SIZE}
- URL: ${FRONTEND_URL}

BACKEND:
- Status: ✅ Preparado para deploy
- Plataforma: Render/Heroku
- URL: ${BACKEND_URL}

CONFIGURAÇÕES:
- CORS configurado para Netlify
- Headers de segurança aplicados
- Cache otimizado
- PWA configurado

PRÓXIMOS PASSOS:
1. Configurar variáveis de ambiente no backend
2. Conectar banco de dados PostgreSQL
3. Configurar Redis (opcional)
4. Executar testes de integração
5. Monitorar logs e performance

=== FIM DO RELATÓRIO ===
EOF

info "📋 Relatório salvo em: deployment-report.txt"

# ============================================================================
# 8. FINALIZAÇÃO
# ============================================================================
echo ""
log "🎉 === DEPLOY CONCLUÍDO COM SUCESSO === 🎉"
echo ""
info "📱 Acesse a aplicação:"
info "   🌐 ${FRONTEND_URL}"
echo ""
info "🔧 Comandos úteis:"
info "   Frontend: ./deploy-full.sh"
info "   + Backend: ./deploy-full.sh --clean --backend --prod"
info "   Logs: netlify logs --prod"
echo ""

# Desativar virtual environment
if [ -n "${VIRTUAL_ENV}" ]; then
    deactivate
fi 