# 🤖 IA Online - Configuração Rápida

## 🚀 Início Rápido (5 minutos)

### 1. Execute o Script Automático
```bash
# Na raiz do projeto
./setup_ia_online.sh
```

### 2. Configure sua OpenAI API Key
- Acesse: https://platform.openai.com/api-keys
- Crie uma nova chave
- Cole quando solicitado pelo script

### 3. Inicie o Sistema
```bash
# Terminal 1: Backend
./start_ia_online.sh

# Terminal 2: Frontend  
cd frontend && npm start
```

### 4. Teste a IA
- Acesse: http://localhost:3000/ai
- Verifique se aparece "Online" ✅
- Digite: "Crie um contrato de locação"

---

## 📋 Pré-requisitos

- ✅ Python 3.8+
- ✅ Node.js 16+
- ✅ Conta OpenAI com billing configurado

---

## 🔧 Configuração Manual

### Opção 1: Arquivo .env
```bash
cp env.template .env
# Editar .env e configurar OPENAI_API_KEY
```

### Opção 2: Variáveis de Sistema
```bash
export OPENAI_API_KEY="sk-sua-chave"
export OPENAI_MODEL="gpt-4o-mini"
```

---

## 💡 Modelos Disponíveis

| Modelo | Custo | Uso Recomendado |
|--------|-------|-----------------|
| `gpt-4o-mini` | 💰 Econômico | Desenvolvimento/Testes |
| `gpt-4o` | 💰💰 Moderado | Produção Padrão |
| `gpt-4-turbo` | 💰💰💰 Alto | Alta Precisão |

---

## 🚨 Solução Rápida de Problemas

### ❌ "OpenAI não configurado"
```bash
echo $OPENAI_API_KEY  # Deve mostrar sk-...
```

### ❌ "Falha na comunicação"
```bash
curl http://localhost:5005/health  # Backend deve responder
```

### ❌ Frontend mostra "Offline"
```bash
# Verificar URL da API em:
# frontend/src/services/adaptiveAIService.ts
```

---

## 📊 Custos Estimados

**GPT-4o-mini (Recomendado)**
- ~$0.001-0.005 por pergunta
- ~$10-50/mês uso moderado

**Configurar Limite:**
- Acesse: https://platform.openai.com/usage
- Configure hard limit: $50-100

---

## 🎯 Funcionalidades

### ✅ Chat Interativo
- Geração de documentos jurídicos
- 9 tipos de documentos suportados
- Histórico de conversas

### ✅ Revisão de Documentos  
- Análise de riscos
- Sugestões de melhoria
- Pontuação de qualidade

### ✅ Resumo Inteligente
- Resumo automático
- Referências jurídicas
- Redução de texto

---

## 🔒 Segurança

### Proteção da API Key
- ✅ Nunca committar no Git
- ✅ Usar variáveis de ambiente
- ✅ Configurar rate limits

### Rate Limiting
- 100 requests/hora por usuário
- Configurável no .env

---

## 📱 Deploy em Produção

### Railway/Render
```bash
# Configurar variáveis:
OPENAI_API_KEY=sk-sua-chave
OPENAI_MODEL=gpt-4o-mini
FLASK_ENV=production
```

### Netlify (Frontend)
```bash
# Atualizar URL da API:
# frontend/src/services/adaptiveAIService.ts
baseURL: 'https://sua-api.railway.app/api'
```

---

## 📞 Suporte

- 📖 **Documentação**: `CONFIGURACAO_IA_ONLINE.md`
- 🔧 **Setup Automático**: `./setup_ia_online.sh`
- 🚀 **Iniciar Sistema**: `./start_ia_online.sh`
- 🌐 **OpenAI Docs**: https://platform.openai.com/docs

---

**🎉 Sua IA Jurídica está pronta!** 