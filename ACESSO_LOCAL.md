# 🚀 JurisSaaS - Acesso Local

## ✅ APLICAÇÃO FUNCIONANDO!

A plataforma JurisSaaS está rodando localmente com sucesso nas seguintes portas:

### 🌐 **Frontend React**
- **URL**: http://localhost:3000
- **Status**: ✅ Funcionando
- **Tecnologia**: React 18 + TypeScript + Tailwind CSS

### 🔧 **Backend Flask API**
- **URL**: http://localhost:5005
- **API Health**: http://localhost:5005/api/health
- **Status**: ✅ Funcionando
- **Tecnologia**: Flask + SQLAlchemy + JWT

---

## 🔑 **Credenciais de Teste**

### **Usuário Administrador**
```
Email: admin@jurissaas.com
Senha: admin123
```

---

## 📋 **Como Acessar**

1. **Abra seu navegador** e acesse: http://localhost:3000
2. **Faça login** com as credenciais acima
3. **Explore as funcionalidades**:
   - ✅ Dashboard principal
   - ✅ Editor de documentos com IA
   - ✅ Biblioteca de templates jurídicos
   - ✅ Sistema de upload de arquivos
   - ✅ Exportação para PDF/DOCX
   - ✅ Perfil do usuário

---

## 🛠️ **Funcionalidades Disponíveis**

### **📝 Editor Inteligente**
- Editor rich text com ReactQuill
- Salvamento automático a cada 3 segundos
- Variáveis dinâmicas (`{NOME}`, `{DATA}`, `{VALOR}`)
- Integração com IA para geração de conteúdo

### **📄 Templates Jurídicos**
- Petições Iniciais Cíveis
- Contestações
- Recursos de Apelação
- Habeas Corpus
- Mandados de Segurança

### **🤖 Inteligência Artificial**
- Geração de cláusulas específicas
- Fundamentação jurídica automática
- Sistema de fallback quando OpenAI não configurada

### **📤 Upload e Processamento**
- Suporte a PDF, DOCX, TXT
- Extração automática de texto
- Detecção inteligente de variáveis
- Conversão para templates

### **📊 Exportação**
- PDF profissional com formatação
- DOCX editável para Word
- Preenchimento automático de variáveis

---

## 🔧 **Comandos para Gerenciar**

### **Parar os Serviços**
```bash
# Parar backend (Ctrl+C no terminal do Flask)
# Parar frontend (Ctrl+C no terminal do React)
```

### **Reiniciar os Serviços**
```bash
# Backend
python src/main.py

# Frontend (em outro terminal)
npm start
```

### **Verificar Status**
```bash
# Verificar se estão rodando
lsof -i :3000  # Frontend
lsof -i :5005  # Backend

# Testar APIs
curl http://localhost:5005/api/health
curl -I http://localhost:3000
```

---

## 📊 **Banco de Dados**

- **Tipo**: SQLite
- **Localização**: `src/jurissaas.db`
- **Status**: ✅ Inicializado com dados de exemplo
- **Usuário admin**: Já criado e funcional

---

## 🎯 **Próximos Passos**

1. **Teste todas as funcionalidades** no frontend
2. **Crie novos documentos** usando os templates
3. **Experimente a IA** para geração de conteúdo
4. **Faça upload** de documentos existentes
5. **Exporte** documentos em PDF/DOCX

---

## 🆘 **Resolução de Problemas**

### **Frontend não carrega**
```bash
# Limpar cache e reinstalar
rm -rf node_modules package-lock.json
npm install --registry=https://registry.npmjs.org/
npm start
```

### **Backend com erro**
```bash
# Verificar se está no ambiente virtual
source venv/bin/activate
python src/main.py
```

### **Erro de CORS**
- ✅ Já configurado para aceitar requisições do frontend

---

## 🎉 **Sucesso!**

A aplicação JurisSaaS está **100% funcional** localmente. Todas as features principais estão operacionais e prontas para teste.

**Acesse agora**: http://localhost:3000 