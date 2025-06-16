# 🚀 DEPLOY FINAL - JurisIA

## ✅ STATUS ATUAL
- ✅ Código commitado e enviado para GitHub
- ✅ Repositório: https://github.com/mdearaujo_meli/jurisia-saas
- ✅ Backend 100% funcional localmente
- ✅ Todas as configurações prontas

## 🎯 PRÓXIMOS PASSOS - DEPLOY NO RENDER

### 1. Acessar Render Dashboard
- Ir para: https://render.com
- Fazer login/criar conta

### 2. Criar Web Service
1. Clicar em **"New"** → **"Web Service"**
2. Conectar ao GitHub e selecionar: `mdearaujo_meli/jurisia-saas`
3. Configurar:
   ```
   Name: jurisia-api
   Environment: Python 3
   Branch: main
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 src.app:app
   ```

### 3. Configurar Variáveis de Ambiente
```
FLASK_ENV=production
SECRET_KEY=[deixar auto-gerar]
CORS_ORIGINS=https://jurisia.netlify.app,https://*.netlify.app,http://localhost:3000
PORT=10000
```

### 4. Adicionar PostgreSQL (Opcional)
- "New" → "PostgreSQL"
- Name: jurisia-db
- Conectar DATABASE_URL no web service

### 5. Deploy Automático
- O Render fará deploy automático
- URL final: `https://jurisia-api.onrender.com`

## 🔧 ATUALIZAR FRONTEND (NETLIFY)

Após deploy do backend, atualizar `netlify.toml`:
```toml
[[redirects]]
  from = "/api/*"
  to = "https://jurisia-api.onrender.com/api/:splat"
  status = 200
  force = true
```

## ✅ VERIFICAÇÃO FINAL

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

## 🎉 RESULTADO ESPERADO

Após completar estes passos:
- ✅ Backend rodando em: `https://jurisia-api.onrender.com`
- ✅ Frontend rodando em: `https://jurisia.netlify.app`
- ✅ Todas as APIs funcionando
- ✅ CORS resolvido
- ✅ Aplicação 100% funcional

---
**Status**: 🚀 PRONTO PARA DEPLOY FINAL NO RENDER
**Repositório**: https://github.com/mdearaujo_meli/jurisia-saas
**Próximo passo**: Acessar render.com e seguir instruções acima 