# 🤖 Configuração da IA Online - JurisIA

## 📋 Visão Geral

Este guia explica como configurar o **modo online** da IA jurídica, que utiliza a **OpenAI GPT-4** para funcionalidades avançadas de:
- ✅ Geração de documentos jurídicos
- ✅ Revisão e análise de contratos
- ✅ Resumo inteligente de textos
- ✅ Análise de conformidade legal

---

## 🎯 Pré-requisitos

### 1. Conta OpenAI
- Acesse: https://platform.openai.com/
- Crie uma conta e configure um método de pagamento
- Obtenha sua **API Key** (começará com `sk-`)

### 2. Backend JurisIA
- Python 3.8+
- Flask já configurado no projeto
- Variáveis de ambiente configuráveis

---

## 🔧 Configuração Passo a Passo

### **Etapa 1: Configurar OpenAI API Key**

#### 1.1 Obter a API Key
1. Faça login em https://platform.openai.com/
2. Vá em **API Keys** no menu lateral
3. Clique em **"Create new secret key"**
4. Copie a chave (formato: `sk-proj-...` ou `sk-...`)

#### 1.2 Configurar no Ambiente Local

**Opção A: Arquivo `.env`**
```bash
# Criar arquivo .env na raiz do projeto
echo "OPENAI_API_KEY=sk-sua-chave-aqui" >> .env
echo "OPENAI_MODEL=gpt-4o-mini" >> .env
echo "OPENAI_MAX_TOKENS=2000" >> .env
echo "OPENAI_TEMPERATURE=0.7" >> .env
```

**Opção B: Variáveis de Sistema**
```bash
# Linux/Mac
export OPENAI_API_KEY="sk-sua-chave-aqui"
export OPENAI_MODEL="gpt-4o-mini"

# Windows
set OPENAI_API_KEY=sk-sua-chave-aqui
set OPENAI_MODEL=gpt-4o-mini
```

### **Etapa 2: Iniciar o Backend**

#### 2.1 Instalar Dependências
```bash
# Navegar para a pasta do projeto
cd /Users/mdearaujo/Documents/Projetos/git/Juris-IA

# Ativar ambiente virtual (se existir)
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt
```

#### 2.2 Executar o Backend
```bash
# Opção 1: Executar diretamente
python src/app.py

# Opção 2: Usar Flask
export FLASK_APP=src/app.py
flask run --host=0.0.0.0 --port=5005

# Opção 3: Script de inicialização
./start_application.sh
```

**Resultado esperado:**
```
✅ OpenAI configurado e pronto para uso
 * Running on http://0.0.0.0:5005
 * Debug mode: on
```

### **Etapa 3: Configurar Frontend**

#### 3.1 Atualizar URL da API
Edite o arquivo `frontend/src/services/adaptiveAIService.ts`:

```typescript
// Linha ~8-12
const apiClient = axios.create({
  baseURL: process.env.NODE_ENV === 'production' 
    ? 'https://sua-api-url.com/api'  // URL de produção
    : 'http://localhost:5005/api',   // URL local
  timeout: API_TIMEOUT,
  // ...
});
```

#### 3.2 Testar Conectividade
```bash
# No terminal
curl -X POST http://localhost:5005/api/ai/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Teste de conexão"}'
```

**Resposta esperada:**
```json
{
  "success": true,
  "generated_text": "Texto gerado pela IA...",
  "confidence": 0.95,
  "metadata": {
    "model": "gpt-4o-mini",
    "tokens_used": 150
  }
}
```

---

## 🚀 Deploy em Produção

### **Opção 1: Railway/Render**

#### 1.1 Configurar Variáveis de Ambiente
```bash
# No painel do Railway/Render
OPENAI_API_KEY=sk-sua-chave-aqui
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7
FLASK_ENV=production
DATABASE_URL=sua-url-postgresql
```

#### 1.2 Fazer Deploy
```bash
# Commit e push das mudanças
git add .
git commit -m "feat: Configura IA online com OpenAI"
git push origin main
```

### **Opção 2: Heroku**

#### 2.1 Criar App
```bash
heroku create jurisia-api
heroku config:set OPENAI_API_KEY=sk-sua-chave-aqui
heroku config:set OPENAI_MODEL=gpt-4o-mini
```

#### 2.2 Deploy
```bash
git push heroku main
```

### **Opção 3: DigitalOcean/AWS**

#### 3.1 Configurar Servidor
```bash
# SSH no servidor
ssh usuario@seu-servidor.com

# Clonar projeto
git clone https://github.com/mathalves23/Juris-IA.git
cd Juris-IA

# Configurar ambiente
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar variáveis
export OPENAI_API_KEY="sk-sua-chave-aqui"
export FLASK_ENV="production"
```

#### 3.2 Configurar Nginx
```nginx
# /etc/nginx/sites-available/jurisia-api
server {
    listen 80;
    server_name api.jurisia.com;
    
    location / {
        proxy_pass http://127.0.0.1:5005;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🔧 Configurações Avançadas

### **Modelos Disponíveis**
```bash
# Econômico (recomendado)
OPENAI_MODEL=gpt-4o-mini

# Avançado
OPENAI_MODEL=gpt-4o

# Premium
OPENAI_MODEL=gpt-4-turbo
```

### **Otimização de Custos**
```bash
# Limitar tokens para reduzir custos
OPENAI_MAX_TOKENS=1500        # Padrão: 2000
OPENAI_TEMPERATURE=0.5        # Mais determinístico

# Rate limiting
RATE_LIMIT_REQUESTS=50        # Máx 50 requests/hora
RATE_LIMIT_PERIOD=3600
```

### **Configuração de Cache**
```bash
# Redis para cache de respostas
REDIS_URL=redis://localhost:6379/0
CACHE_TYPE=redis
CACHE_DEFAULT_TIMEOUT=3600    # 1 hora
```

---

## 🧪 Testes e Validação

### **1. Teste de Conectividade**
```bash
# Frontend - verificar status
curl http://localhost:3000/ai

# Backend - teste direto
curl -X POST http://localhost:5005/api/ai/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Criar contrato de locação", "document_type": "contrato"}'
```

### **2. Monitoramento de Uso**
```bash
# Ver logs da OpenAI
tail -f logs/app.log | grep "OpenAI"

# Verificar status do serviço
curl http://localhost:5005/health
```

### **3. Testes de Funcionalidade**
Acesse: http://localhost:3000/ai

**Testes a realizar:**
- ✅ Chat interativo
- ✅ Revisão de documento
- ✅ Resumo de texto
- ✅ Indicadores de status (Online/Offline)

---

## 📊 Monitoramento e Custos

### **Custos da OpenAI (GPT-4o-mini)**
- **Input**: $0.15 por 1M tokens
- **Output**: $0.60 per 1M tokens
- **Estimativa**: ~$0.001-0.005 por solicitação típica

### **Monitoramento de Uso**
1. **OpenAI Dashboard**: https://platform.openai.com/usage
2. **Logs do Backend**: Verificar `logs/app.log`
3. **Métricas do Frontend**: Status em tempo real

### **Alertas de Custo**
```bash
# Configurar limite de gastos na OpenAI
# Recomendado: $50-100/mês para uso moderado
```

---

## 🔒 Segurança

### **Proteção da API Key**
```bash
# NUNCA committar no Git
echo "OPENAI_API_KEY=*" >> .gitignore

# Usar secrets manager em produção
# Railway: Environment Variables
# Heroku: Config Vars
# AWS: Parameter Store
```

### **Rate Limiting**
```python
# Já configurado no backend
RATE_LIMIT_REQUESTS = 100    # requests por hora
MAX_LOGIN_ATTEMPTS = 5       # tentativas de login
```

---

## 🚨 Solução de Problemas

### **Erro: "OpenAI não configurado"**
```bash
# Verificar API key
echo $OPENAI_API_KEY

# Testar conectividade
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### **Erro: "Quota exceeded"**
```bash
# Verificar limite na OpenAI
# Adicionar método de pagamento
# Configurar alertas de uso
```

### **Erro: "CORS"**
```bash
# Backend já configurado com CORS permissivo
# Verificar se o backend está rodando na porta 5005
```

### **Frontend não conecta**
```bash
# Verificar URL da API
# frontend/src/services/adaptiveAIService.ts
# Linha ~8: baseURL deve apontar para o backend
```

---

## 📱 Teste Final

### **1. Verificar Status**
- ✅ Backend rodando: http://localhost:5005/health
- ✅ Frontend carregando: http://localhost:3000
- ✅ IA página funcionando: http://localhost:3000/ai

### **2. Teste Completo**
1. Acesse `/ai`
2. Digite: "Crie um contrato de prestação de serviços"
3. Verifique se aparece "Online" no status
4. Confirme resposta da IA real (não mock)

### **3. Deploy**
```bash
# Atualizar frontend com URL de produção
# Fazer deploy do backend
# Configurar DNS (se necessário)
# Testar IA online em produção
```

---

## 🎉 Próximos Passos

### **Funcionalidades Avançadas**
- [ ] **Custom Prompts**: Templates específicos por área jurídica
- [ ] **Análise de Sentimentos**: Avaliar tom de documentos
- [ ] **OCR Jurídico**: Extrair texto de PDFs escaneados
- [ ] **Jurisprudência**: Integração com bases de dados legais

### **Otimizações**
- [ ] **Cache Inteligente**: Armazenar respostas similares
- [ ] **Streaming**: Respostas em tempo real
- [ ] **Modelos Locais**: LLaMA/Mistral para reduzir custos
- [ ] **Fine-tuning**: Treinar modelo específico para direito brasileiro

---

## 📞 Suporte

**Documentação OpenAI**: https://platform.openai.com/docs
**Status OpenAI**: https://status.openai.com/
**Comunidade**: https://community.openai.com/

**Em caso de problemas:**
1. Verificar logs: `tail -f logs/app.log`
2. Testar API diretamente com curl
3. Verificar quota e billing na OpenAI
4. Consultar documentação técnica

---

**🚀 Sua IA Jurídica está pronta para revolucionar a advocacia!** 