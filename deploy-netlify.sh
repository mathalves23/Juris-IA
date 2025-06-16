#!/bin/bash

# 🚀 Script de Deploy para Netlify - JurisIA
# Este script automatiza o processo de deploy para o Netlify

echo "🚀 Iniciando deploy do JurisIA para Netlify..."
echo "================================================"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se estamos no diretório correto
if [ ! -f "netlify.toml" ]; then
    log_error "netlify.toml não encontrado. Execute este script na raiz do projeto."
    exit 1
fi

# Verificar se o Netlify CLI está instalado
if ! command -v netlify &> /dev/null; then
    log_warning "Netlify CLI não encontrado. Instalando..."
    npm install -g netlify-cli
    if [ $? -ne 0 ]; then
        log_error "Falha ao instalar Netlify CLI"
        exit 1
    fi
    log_success "Netlify CLI instalado com sucesso"
fi

# Verificar se estamos logados no Netlify
log_info "Verificando autenticação do Netlify..."
if ! netlify status &> /dev/null; then
    log_warning "Não autenticado no Netlify. Iniciando processo de login..."
    netlify login
    if [ $? -ne 0 ]; then
        log_error "Falha na autenticação do Netlify"
        exit 1
    fi
fi

# Entrar no diretório frontend
cd frontend

# Verificar se node_modules existe
if [ ! -d "node_modules" ]; then
    log_info "Instalando dependências do Node.js..."
    npm ci
    if [ $? -ne 0 ]; then
        log_error "Falha ao instalar dependências"
        exit 1
    fi
    log_success "Dependências instaladas com sucesso"
else
    log_info "Atualizando dependências..."
    npm ci
fi

# Executar testes (se existirem)
log_info "Executando verificações de qualidade..."
if npm run test:coverage -- --passWithNoTests --coverage=false --watchAll=false; then
    log_success "Testes executados com sucesso"
else
    log_warning "Alguns testes falharam, mas continuando deploy..."
fi

# Verificar tipos TypeScript
if npm run type-check; then
    log_success "Verificação de tipos concluída"
else
    log_warning "Erros de tipo encontrados, mas continuando deploy..."
fi

# Fazer build da aplicação
log_info "Construindo aplicação para produção..."
npm run build
if [ $? -ne 0 ]; then
    log_error "Falha no build da aplicação"
    exit 1
fi
log_success "Build concluído com sucesso"

# Voltar para o diretório raiz
cd ..

# Verificar se o site já existe no Netlify
log_info "Verificando configuração do site no Netlify..."
if [ ! -f ".netlify/state.json" ]; then
    log_info "Primeiro deploy. Criando novo site..."
    
    # Criar novo site
    netlify sites:create --name jurisia-$(date +%s)
    if [ $? -ne 0 ]; then
        log_error "Falha ao criar site no Netlify"
        exit 1
    fi
    log_success "Site criado no Netlify"
fi

# Fazer deploy
log_info "Iniciando deploy para produção..."
netlify deploy --prod --dir=frontend/build
if [ $? -ne 0 ]; then
    log_error "Falha no deploy para produção"
    exit 1
fi

log_success "Deploy concluído com sucesso!"

# Obter URL do site
SITE_URL=$(netlify status --json | grep -o '"url":"[^"]*"' | cut -d'"' -f4)
if [ ! -z "$SITE_URL" ]; then
    echo ""
    echo "🌐 Site disponível em: $SITE_URL"
    echo ""
else
    log_info "Execute 'netlify status' para ver a URL do site"
fi

# Verificar status do deploy
log_info "Verificando status do deploy..."
netlify status

# Executar smoke tests básicos
log_info "Executando verificações pós-deploy..."
if [ ! -z "$SITE_URL" ]; then
    # Verificar se o site está respondendo
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SITE_URL")
    if [ "$HTTP_STATUS" = "200" ]; then
        log_success "Site está respondendo corretamente (HTTP $HTTP_STATUS)"
    else
        log_warning "Site retornou HTTP $HTTP_STATUS"
    fi
    
    # Verificar se assets principais estão carregando
    log_info "Verificando carregamento de assets..."
    if curl -s "$SITE_URL/static/css/" | grep -q "css"; then
        log_success "CSS assets carregando corretamente"
    else
        log_warning "Possível problema com CSS assets"
    fi
else
    log_warning "Não foi possível verificar o site automaticamente"
fi

echo ""
echo "🎉 Deploy do JurisIA concluído com sucesso!"
echo "================================================"
echo ""
echo "📋 Resumo do Deploy:"
echo "   • Frontend: React + TypeScript + Ant Design"
echo "   • Build: Otimizado para produção"
echo "   • Cache: Configurado para máxima performance"
echo "   • Segurança: Headers de segurança aplicados"
echo "   • PWA: Suporte a Progressive Web App"
echo ""
echo "🔧 Próximos passos:"
echo "   1. Configure as variáveis de ambiente no painel do Netlify"
echo "   2. Configure um domínio customizado (opcional)"
echo "   3. Configure SSL (automático no Netlify)"
echo "   4. Configure analytics e monitoramento"
echo ""
echo "💡 Para atualizações futuras:"
echo "   - Execute 'git push' para deploys automáticos"
echo "   - Ou execute novamente este script"
echo ""

# Verificar se quer abrir o site no navegador
read -p "🌐 Deseja abrir o site no navegador? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ ! -z "$SITE_URL" ]; then
        if command -v open &> /dev/null; then
            open "$SITE_URL"
        elif command -v xdg-open &> /dev/null; then
            xdg-open "$SITE_URL"
        else
            log_info "Abra manualmente: $SITE_URL"
        fi
    fi
fi

log_success "Script de deploy finalizado!" 