# 🚀 Acesso Local - JurisSaaS (Portas Atualizadas)

## 📋 Informações de Acesso

### 🌐 URLs de Acesso
- **Frontend (React)**: http://localhost:3007
- **Backend (Flask API)**: http://localhost:5007
- **Health Check**: http://localhost:5007/api/health

### 🔑 Credenciais de Login
- **Email**: admin@jurissaas.com
- **Senha**: admin123

## 🎯 Portas Configuradas

### ✅ **Novas Portas (Sem Conflito)**
- **Frontend**: `3007` (React Development Server)
- **Backend**: `5007` (Flask API Server)

### 📝 **Comandos para Iniciar**

#### Backend (Flask):
```bash
cd "/Users/mdearaujo/Downloads/Plataforma SaaS Jurídica com Automação e IA para Advogados"
python src/main.py
```

#### Frontend (React):
```bash
cd "/Users/mdearaujo/Downloads/Plataforma SaaS Jurídica com Automação e IA para Advogados"
npm run start:port3007
```

#### Verificar Status:
```bash
# Backend
curl http://localhost:5007/api/health

# Frontend
curl -I http://localhost:3007
```

## 🔧 Configurações Atualizadas

### Backend (`src/main.py`):
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5007, debug=True)
```

### Frontend (`src/services/api.ts`):
```typescript
const api = axios.create({
  baseURL: 'http://localhost:5007/api',
});
```

### Package.json:
```json
"scripts": {
  "start:port3007": "PORT=3007 react-scripts start"
}
```

## ✅ Status dos Serviços

### 🟢 Backend (Flask) - Porta 5007
- ✅ API funcionando corretamente
- ✅ Banco de dados SQLite conectado
- ✅ Autenticação JWT configurada
- ✅ CORS habilitado para localhost:3007

### 🟢 Frontend (React) - Porta 3007
- ✅ Servidor de desenvolvimento ativo
- ✅ Compilação sem erros
- ✅ API endpoints configurados
- ✅ Interface totalmente funcional

## 🎯 Funcionalidades Disponíveis

### 🔐 **Autenticação**
- Login/Logout com JWT
- Gestão de perfil de usuário
- Sistema de assinaturas

### 📝 **Editor de Documentos**
- Editor rich text (ReactQuill)
- Integração com IA para geração de texto
- Sistema de templates
- Versionamento de documentos
- Variáveis dinâmicas

### 📋 **Templates Jurídicos**
- Biblioteca de modelos pré-configurados
- Editor de templates
- Categorização
- Extração automática de variáveis

### 🤖 **Integração IA**
- Geração de texto jurídico
- Sugestões contextuais
- Extração de variáveis
- Assistente inteligente

### 📊 **Gestão de Assinaturas**
- 4 planos disponíveis (Básico, Profissional, Empresarial, Enterprise)
- Controle de limites por plano
- Upgrade/downgrade de planos

### 📁 **Sistema de Arquivos**
- Upload de documentos (PDF, DOCX)
- Processamento automático
- Conversão e análise

### 📄 **Exportação**
- Export para PDF
- Export para DOCX
- Formatação profissional

## 🛠️ Comandos Úteis

### Parar Serviços:
```bash
# Matar processos nas portas específicas
lsof -ti:3007,5007 | xargs kill -9

# Ou matar todos os processos relacionados
pkill -f "react-scripts"
pkill -f "python.*main.py"
```

### Verificar Portas em Uso:
```bash
lsof -i:3007,5007
```

### Logs em Tempo Real:
```bash
# Ver logs do backend
tail -f server.log

# Ver logs do frontend (no terminal onde foi iniciado)
```

## 🚀 Próximos Passos

1. **Acesse**: http://localhost:3007
2. **Faça login** com as credenciais fornecidas
3. **Explore** todas as funcionalidades
4. **Teste** a criação de documentos
5. **Experimente** a integração com IA

## 📞 Suporte

Em caso de problemas:
1. Verifique se ambos os serviços estão rodando
2. Confirme se as portas estão livres
3. Verifique os logs para mensagens de erro
4. Reinicie os serviços se necessário

---

**Status**: ✅ **TOTALMENTE FUNCIONAL NAS NOVAS PORTAS**
**Última atualização**: $(date) 