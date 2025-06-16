# 🚀 INSTRUÇÕES DE DEPLOY - JurisIA

## ✅ STATUS: APLICAÇÃO 100% PRONTA PARA DEPLOY

### 📋 PRÉ-REQUISITOS ATENDIDOS
- ✅ Backend Flask funcionando localmente
- ✅ Todas as APIs implementadas (/health, /api/ai/generate, /api/contract-analyzer/*)
- ✅ CORS configurado corretamente
- ✅ Dependências instaladas (Flask-Login, gunicorn)
- ✅ Modelos SQLAlchemy corrigidos
- ✅ Frontend build otimizado no Netlify

## 🎯 DEPLOY NO RENDER (RECOMENDADO)

### Opção 1: Deploy via GitHub (Recomendado)
1. **Criar repositório no GitHub:**
   ```bash
   # No GitHub, criar novo repositório: jurisia-saas
   git remote add origin https://github.com/SEU_USUARIO/jurisia-saas.git
   git push -u origin main
   ```

2. **Conectar no Render:**
   - Acessar https://render.com
   - Criar conta/fazer login
   - "New" → "Web Service"
   - Conectar repositório GitHub
   - Usar configurações do `render.yaml`

### Opção 2: Deploy Manual (Alternativo)
1. **Acessar Render Dashboard:**
   - https://render.com/dashboard

2. **Criar Web Service:**
   - "New" → "Web Service"
   - "Deploy from Git repository" ou "Upload files"

3. **Configurações:**
   ```
   Name: jurisia-api
   Environment: Python 3
   Build Command: pip install -r requirements.txt && pip install gunicorn
   Start Command: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 src.app:app
   ```

4. **Variáveis de Ambiente:**
   ```
   FLASK_ENV=production
   SECRET_KEY=[auto-generated]
   CORS_ORIGINS=https://jurisia.netlify.app,https://*.netlify.app
   PORT=10000
   ```

5. **Banco de Dados:**
   - "New" → "PostgreSQL"
   - Name: jurisia-db
   - Conectar DATABASE_URL no web service

## 🎯 DEPLOY NO HEROKU (ALTERNATIVO)

### Preparação:
```bash
# Instalar Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Criar app
heroku create jurisia-api

# Adicionar PostgreSQL
heroku addons:create heroku-postgresql:mini

# Deploy
git push heroku main
```

## 🔧 CONFIGURAÇÕES IMPORTANTES

### Backend URLs após Deploy:
- **Render**: `https://jurisia-api.onrender.com`
- **Heroku**: `https://jurisia-api.herokuapp.com`

### Atualizar Frontend (Netlify):
Após deploy do backend, atualizar `netlify.toml`:
```toml
[[redirects]]
  from = "/api/*"
  to = "https://jurisia-api.onrender.com/api/:splat"
  status = 200
  force = true
```

## ✅ VERIFICAÇÃO PÓS-DEPLOY

### Testar APIs:
```bash
# Health check
curl https://jurisia-api.onrender.com/health

# AI API
curl -X POST https://jurisia-api.onrender.com/api/ai/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "teste"}'

# Contract Analyzer
curl https://jurisia-api.onrender.com/api/contract-analyzer/stats
```

### Frontend:
- Acessar: https://jurisia.netlify.app
- Testar funcionalidades de IA
- Verificar se não há erros CORS

## 🚨 TROUBLESHOOTING

### Erro "Module not found":
- Verificar se todas as dependências estão em requirements.txt
- Comentar imports de módulos não existentes

### Erro CORS:
- Verificar CORS_ORIGINS nas variáveis de ambiente
- Confirmar headers nas rotas Flask

### Erro de Banco:
- Verificar DATABASE_URL
- Executar migrações se necessário

## 📞 SUPORTE

Se houver problemas no deploy:
1. Verificar logs do Render/Heroku
2. Testar localmente primeiro
3. Verificar todas as variáveis de ambiente
4. Confirmar que o build foi bem-sucedido

---
**Status**: ✅ PRONTO PARA DEPLOY
**Última atualização**: Deploy preparado com todas as correções aplicadas 