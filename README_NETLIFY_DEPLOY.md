# 🚀 Deploy do JurisIA no Netlify

## 📋 **Pré-requisitos**

- Conta no GitHub/GitLab/Bitbucket (para conectar o repositório)
- Conta no [Netlify](https://app.netlify.com/)
- Frontend React funcional na pasta `frontend/`

---

## 🔧 **MÉTODO 1: Deploy Automático via Git (Recomendado)**

### **1. Fazer Push do Código para Git**

```bash
# Se ainda não tem repositório Git
git init
git add .
git commit -m "feat: JurisIA completo pronto para deploy"

# Conectar com GitHub (criar repositório primeiro)
git remote add origin https://github.com/SEU_USUARIO/jurisia.git
git branch -M main
git push -u origin main
```

### **2. Criar Site no Netlify**

1. **Acesse:** [https://app.netlify.com/](https://app.netlify.com/)
2. **Clique:** "Add new site" → "Import an existing project"
3. **Escolha:** GitHub/GitLab/Bitbucket
4. **Autorize:** Netlify a acessar seus repositórios
5. **Selecione:** O repositório do JurisIA

### **3. Configurar Build Settings**

Na página de configuração:

```
Site name: jurisia
Branch to deploy: main
Build command: cd frontend && npm run build
Publish directory: frontend/build
```

### **4. Variáveis de Ambiente**

No painel do Netlify, vá em **Site settings** → **Environment variables**:

```
NODE_VERSION = 18
REACT_APP_API_URL = https://sua-api-backend.herokuapp.com
GENERATE_SOURCEMAP = false
CI = false
```

### **5. Deploy Automático**

- Clique **"Deploy site"**
- O Netlify irá automaticamente:
  - Clonar seu repositório
  - Instalar dependências (`npm install`)
  - Executar build (`npm run build`)
  - Publicar os arquivos

---

## 🔧 **MÉTODO 2: Deploy Manual (Drag & Drop)**

### **1. Build Local**

```bash
# Entrar na pasta frontend
cd frontend

# Instalar dependências
npm install

# Fazer build de produção
npm run build
```

### **2. Upload Manual**

1. **Acesse:** [https://app.netlify.com/](https://app.netlify.com/)
2. **Clique:** "Add new site" → "Deploy manually"
3. **Arraste:** A pasta `frontend/build` para a área de upload
4. **Aguarde:** O upload e processamento

---

## ⚙️ **Configurações Avançadas**

### **Custom Domain (Opcional)**

1. **Site settings** → **Domain management**
2. **Add custom domain**
3. Configure DNS do seu domínio:
   ```
   Type: CNAME
   Name: www
   Value: seu-site.netlify.app
   ```

### **HTTPS (Automático)**

- Netlify provisiona SSL automaticamente
- Força redirecionamento HTTPS

### **Branch Previews**

- Habilite em **Site settings** → **Branch deploys**
- Cada branch terá URL de preview automática

---

## 🔍 **URLs Importantes**

### **URLs Padrão do Netlify:**
- **Site Principal:** `https://jurisia.netlify.app`
- **Admin Dashboard:** `https://app.netlify.com/sites/jurisia`
- **Deploy Logs:** `https://app.netlify.com/sites/jurisia/deploys`

### **URLs Customizadas (quando configurar):**
- **Domínio Próprio:** `https://www.jurisia.com.br`
- **API Backend:** `https://api.jurisia.com.br`

---

## 🚨 **Solução de Problemas Comuns**

### **Erro: "Build failed"**

```bash
# Testar build localmente primeiro
cd frontend
npm install
npm run build

# Se funcionar local, verificar:
# 1. Versão do Node.js no Netlify (deve ser 18+)
# 2. Variáveis de ambiente
# 3. Dependências no package.json
```

### **Erro: "Page not found" em rotas**

- Verifique se o arquivo `_redirects` existe em `frontend/public/`
- Ou se `netlify.toml` tem a configuração de SPA

### **Erro: "API calls failing"**

- Verifique `REACT_APP_API_URL` nas variáveis de ambiente
- Configure CORS no backend para aceitar o domínio do Netlify

---

## 📊 **Otimizações de Performance**

### **1. Build Otimizado**

```json
// package.json - scripts otimizados
{
  "scripts": {
    "build": "react-scripts build && npm run optimize",
    "optimize": "npx terser build/static/js/*.js --compress --mangle"
  }
}
```

### **2. Headers de Cache (já configurado)**

- Assets estáticos: Cache de 1 ano
- HTML: Sem cache (para atualizações)
- Service Worker: Sem cache

### **3. Compressão Automática**

- Netlify comprime automaticamente:
  - Gzip para todos os assets
  - Brotli para navegadores compatíveis

---

## 🔧 **Comandos Úteis**

### **Netlify CLI (Opcional)**

```bash
# Instalar CLI
npm install -g netlify-cli

# Login
netlify login

# Deploy direto da CLI
cd frontend
npm run build
netlify deploy --prod --dir=build
```

### **Verificar Build Local**

```bash
# Simular ambiente de produção
cd frontend
npm run build
npx serve -s build -p 3000
```

---

## 🎯 **Checklist de Deploy**

- [ ] Código commitado no Git
- [ ] Build local funcionando (`npm run build`)
- [ ] Variáveis de ambiente configuradas
- [ ] Arquivo `netlify.toml` na raiz
- [ ] Arquivo `_redirects` em `public/`
- [ ] Domain/subdomain configurado
- [ ] SSL habilitado
- [ ] API backend funcionando
- [ ] CORS configurado no backend

---

## 🌐 **Estrutura Final no Netlify**

```
jurisia.netlify.app/
├── /                    # Dashboard principal
├── /login              # Página de login  
├── /clientes           # Gestão de clientes
├── /processos          # Gestão de processos
├── /kanban             # Sistema Kanban
├── /wiki               # Memória operacional
├── /documentos         # Editor IA
├── /templates          # Templates
├── /notificacoes       # Central de notificações
├── /relatorios         # Dashboard e relatórios
└── /configuracoes      # Configurações
```

---

## 🎉 **Próximos Passos Após Deploy**

1. **Testar todas as funcionalidades**
2. **Configurar monitoramento (opcional)**
3. **Configurar analytics (opcional)**
4. **Documentar URLs para equipe**
5. **Configurar backup automático**

**Seu JurisIA estará disponível em: `https://jurisia.netlify.app`** 🚀 