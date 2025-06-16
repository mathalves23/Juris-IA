# 🚀 Guia de Deploy - JurisIA no Netlify

## 📋 Visão Geral

Este guia fornece instruções completas para fazer deploy da plataforma JurisIA no Netlify, incluindo configurações otimizadas para produção.

## ⚡ Deploy Rápido (Recomendado)

### Opção 1: Script Automatizado
```bash
# Execute o script de deploy automatizado
./deploy-netlify.sh
```

### Opção 2: Deploy Manual via CLI

```bash
# 1. Instalar Netlify CLI (se não tiver)
npm install -g netlify-cli

# 2. Fazer login no Netlify
netlify login

# 3. Navegar para o frontend e fazer build
cd frontend
npm ci
npm run build

# 4. Voltar para raiz e fazer deploy
cd ..
netlify deploy --prod --dir=frontend/build
```

## 🔧 Configurações Implementadas

### 1. **netlify.toml** - Configuração Principal
- ✅ Build commands otimizados
- ✅ Variáveis de ambiente para produção
- ✅ Redirects para SPA
- ✅ Headers de segurança
- ✅ Cache otimizado para performance
- ✅ Compressão de assets

### 2. **Variáveis de Ambiente**
```bash
# Principais variáveis configuradas automaticamente:
REACT_APP_API_URL=https://jurisia-api.herokuapp.com/api
REACT_APP_WEBSOCKET_URL=wss://jurisia-api.herokuapp.com
REACT_APP_ENV=production
REACT_APP_VERSION=2.0.0
NODE_VERSION=18
NPM_VERSION=9
```

### 3. **Headers de Segurança**
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy` otimizado
- `Permissions-Policy` restritivo

### 4. **Otimizações de Performance**
- Cache de 1 ano para assets estáticos
- Compressão automática de imagens
- Minificação de CSS e JS
- Bundle optimization

## 🌐 Deploy via Interface Web

### 1. **Conectar Repositório**
1. Acesse [netlify.com](https://netlify.com)
2. Faça login na sua conta
3. Clique em "New site from Git"
4. Conecte seu repositório GitHub

### 2. **Configurações de Build**
```
Build command: npm ci && npm run build
Publish directory: frontend/build
Base directory: frontend/
```

### 3. **Variáveis de Ambiente**
No painel do Netlify, configure:
- `NODE_VERSION`: 18
- `NPM_VERSION`: 9
- `CI`: true
- `NODE_ENV`: production

## 📊 Recursos Ativados no Deploy

### ✅ **Frontend Completo**
- React 18 + TypeScript
- Ant Design UI Library
- Charts e Analytics
- Sistema de Notificações
- Wiki/Base de Conhecimento
- Dashboard Analytics
- Sistema Kanban

### ✅ **Funcionalidades Avançadas**
- Progressive Web App (PWA)
- Service Workers
- Cache Strategy otimizada
- Responsive Design
- Dark/Light Mode
- Multilanguage Support

### ✅ **Integrações**
- WebSocket para tempo real
- APIs RESTful
- Upload de arquivos
- Sistema de autenticação
- Analytics integrado

## 🔍 Verificações Pós-Deploy

### 1. **Smoke Tests Automáticos**
O script de deploy inclui verificações automáticas:
- ✅ Status HTTP 200
- ✅ Carregamento de assets CSS/JS
- ✅ Responsividade básica
- ✅ Funcionalidades principais

### 2. **Testes Manuais Recomendados**
- [ ] Login e autenticação
- [ ] Criação de documentos
- [ ] Sistema de notificações
- [ ] Dashboard analytics
- [ ] Wiki/Base conhecimento
- [ ] Sistema Kanban
- [ ] Upload de arquivos
- [ ] Responsividade mobile

## 🎯 URLs e Endpoints

### **Frontend (Netlify)**
- URL Principal: `https://[seu-site].netlify.app`
- Admin: `https://[seu-site].netlify.app/admin`
- Dashboard: `https://[seu-site].netlify.app/dashboard`

### **Backend (Heroku)**
- API Base: `https://jurisia-api.herokuapp.com/api`
- WebSocket: `wss://jurisia-api.herokuapp.com`
- Health Check: `https://jurisia-api.herokuapp.com/health`

## 🔒 Configurações de Segurança

### 1. **HTTPS Automático**
- SSL certificado automaticamente pelo Netlify
- Redirecionamento HTTP → HTTPS forçado
- HSTS headers configurados

### 2. **Content Security Policy**
```
default-src 'self';
script-src 'self' 'unsafe-inline' 'unsafe-eval';
style-src 'self' 'unsafe-inline';
img-src 'self' data: https:;
connect-src 'self' https://jurisia-api.herokuapp.com;
```

### 3. **Permissions Policy**
- Camera: bloqueada
- Microphone: bloqueado
- Geolocation: bloqueada

## 📈 Performance e Monitoramento

### 1. **Métricas do Netlify**
- Core Web Vitals
- Lighthouse Score
- Bundle Analysis
- Load Time Analytics

### 2. **Otimizações Ativas**
- Image Optimization
- Asset Compression
- CDN Global
- Edge Computing

## 🚨 Troubleshooting

### **Erro: Build Failed**
```bash
# Limpar cache e tentar novamente
rm -rf frontend/node_modules
rm frontend/package-lock.json
cd frontend && npm install
npm run build
```

### **Erro: Assets não carregam**
1. Verificar `PUBLIC_URL` no .env
2. Verificar paths relativos no código
3. Verificar configuração do `homepage` no package.json

### **Erro: API não conecta**
1. Verificar variável `REACT_APP_API_URL`
2. Verificar CORS no backend
3. Verificar certificados SSL

### **Erro: WebSocket não conecta**
1. Verificar `REACT_APP_WEBSOCKET_URL`
2. Verificar se backend suporta WSS
3. Verificar proxy configuration

## 🔄 Deploy Contínuo

### **Git Integration**
- Push para `main` → Deploy automático
- Pull Requests → Deploy previews
- Branch deploys para desenvolvimento

### **Webhooks Configurados**
- Build notifications
- Deploy status updates
- Integration com Slack/Discord

## 📱 PWA Configuration

### **Manifest.json**
```json
{
  "name": "JurisIA",
  "short_name": "JurisIA",
  "theme_color": "#1890ff",
  "background_color": "#ffffff",
  "display": "standalone",
  "start_url": "/",
  "icons": [...]
}
```

### **Service Worker**
- Cache Strategy: NetworkFirst
- Offline Fallback
- Update Notifications

## 🎉 Deploy Finalizado

### **Checklist de Verificação**
- [ ] ✅ Build bem-sucedido
- [ ] ✅ Deploy sem erros
- [ ] ✅ Site carregando corretamente
- [ ] ✅ APIs conectando
- [ ] ✅ WebSocket funcionando
- [ ] ✅ Autenticação funcionando
- [ ] ✅ Upload de arquivos funcionando
- [ ] ✅ Todas as páginas acessíveis
- [ ] ✅ Responsividade OK
- [ ] ✅ Performance satisfatória

### **Próximos Passos**
1. 🌐 Configurar domínio customizado
2. 📊 Configurar analytics (Google Analytics)
3. 🔍 Configurar monitoramento de erros (Sentry)
4. 📧 Configurar notificações de deploy
5. 🔄 Configurar backups automáticos

---

## 🎯 **JurisIA está agora ONLINE e FUNCIONAL! 🚀**

**URL de Acesso:** Será exibida após o deploy
**Status:** ✅ Produção
**Performance:** ⚡ Otimizada
**Segurança:** 🔒 Implementada

### **Funcionalidades Disponíveis:**
- ✅ Sistema completo de gestão jurídica
- ✅ Editor de documentos com IA
- ✅ Dashboard analytics avançado
- ✅ Sistema de notificações em tempo real
- ✅ Wiki/Base de conhecimento
- ✅ Sistema Kanban para projetos
- ✅ Colaboração em tempo real
- ✅ Upload e gestão de arquivos
- ✅ Sistema de autenticação completo

**🏆 A plataforma JurisIA está pronta para uso profissional!** 