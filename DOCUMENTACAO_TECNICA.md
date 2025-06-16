# 📚 DOCUMENTAÇÃO TÉCNICA - LEGALAI

## 🏗️ Arquitetura da Aplicação

### Visão Geral
A aplicação LegalAI segue uma arquitetura **cliente-servidor** com separação clara entre frontend e backend:

```
┌─────────────────┐    HTTP/REST    ┌─────────────────┐
│   Frontend      │ ◄──────────────► │    Backend      │
│   React/TS      │                 │   Flask/Python  │
│   Port: 3000    │                 │   Port: 5001    │
└─────────────────┘                 └─────────────────┘
                                            │
                                            ▼
                                    ┌─────────────────┐
                                    │   Database      │
                                    │   SQLite        │
                                    │   legalai.db    │
                                    └─────────────────┘
```

## 🔧 Backend (Flask/Python)

### Estrutura de Diretórios
```
src/
├── main.py                 # Ponto de entrada da aplicação
├── config.py              # Configurações da aplicação
├── auth.py                # Autenticação personalizada
├── init_db_simple.py      # Inicialização do banco
├── extensions.py          # Extensões Flask (SQLAlchemy, JWT, etc.)
├── models/                # Modelos do banco de dados
│   ├── user.py           # Modelo de usuário
│   ├── document.py       # Modelo de documento
│   ├── template.py       # Modelo de template
│   └── subscription.py   # Modelo de assinatura
└── routes/               # Rotas da API
    ├── auth.py          # Rotas de autenticação
    ├── documents.py     # CRUD de documentos
    ├── templates.py     # CRUD de templates
    ├── ai.py           # Integração com IA
    ├── upload.py       # Upload de arquivos
    └── export_simple.py # Exportação de documentos
```

### Principais Endpoints

#### Autenticação
```
POST /api/auth/login      # Login do usuário
POST /api/auth/register   # Registro de usuário
POST /api/auth/refresh    # Renovar token
GET  /api/auth/me         # Dados do usuário logado
PUT  /api/auth/me         # Atualizar perfil
```

#### Documentos
```
GET    /api/documents     # Listar documentos
POST   /api/documents     # Criar documento
GET    /api/documents/:id # Obter documento
PUT    /api/documents/:id # Atualizar documento
DELETE /api/documents/:id # Excluir documento
```

#### Templates
```
GET    /api/templates     # Listar templates
POST   /api/templates     # Criar template
GET    /api/templates/:id # Obter template
PUT    /api/templates/:id # Atualizar template
DELETE /api/templates/:id # Excluir template
```

### Configuração do Banco

#### Modelos Principais

**User (Usuário)**
```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    foto_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

**Document (Documento)**
```python
class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    conteudo = db.Column(db.Text)
    status = db.Column(db.String(50), default='rascunho')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    template_id = db.Column(db.Integer, db.ForeignKey('template.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
```

**Template (Modelo)**
```python
class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(100))
    publico = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### Sistema de Autenticação

#### JWT Configuration
```python
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
```

#### Hash de Senhas
```python
def verify_password_custom(password, hash_str):
    # Método personalizado para verificação de senhas
    test_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), b'salt', 100000)
    return test_hash.hex() == hash_str
```

## ⚛️ Frontend (React/TypeScript)

### Estrutura de Diretórios
```
src/
├── App.tsx                # Componente principal
├── index.tsx             # Ponto de entrada
├── components/           # Componentes reutilizáveis
│   ├── Layout.tsx       # Layout principal
│   ├── Loading.tsx      # Estados de carregamento
│   ├── Modal.tsx        # Modais
│   ├── Toast.tsx        # Notificações
│   └── Onboarding.tsx   # Tutorial inicial
├── contexts/            # Contexts do React
│   ├── AuthContext.tsx  # Contexto de autenticação
│   └── ToastContext.tsx # Contexto de notificações
├── hooks/               # Hooks personalizados
│   └── useAutoSave.ts   # Auto-save de documentos
├── pages/               # Páginas da aplicação
│   ├── Login.tsx        # Página de login
│   ├── Register.tsx     # Página de registro
│   ├── Profile.tsx      # Perfil do usuário
│   ├── dashboard/       # Dashboard
│   ├── documents/       # Gestão de documentos
│   └── templates/       # Gestão de templates
└── services/            # Serviços e API
    └── api.ts          # Cliente HTTP
```

### Principais Componentes

#### AuthContext
```typescript
interface AuthContextType {
  user: User | null;
  subscription: Subscription | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  updateUser: (userData: Partial<User>) => Promise<void>;
}
```

#### ToastContext
```typescript
interface ToastContextType {
  showToast: (message: string, type: ToastType) => void;
}

type ToastType = 'success' | 'error' | 'warning' | 'info';
```

#### useAutoSave Hook
```typescript
const useAutoSave = (
  data: any,
  saveFunction: (data: any) => Promise<void>,
  delay: number = 3000
) => {
  // Implementação do auto-save com debounce
};
```

### Roteamento
```typescript
<Routes>
  <Route path="/login" element={<Login />} />
  <Route path="/register" element={<Register />} />
  <Route path="/" element={<ProtectedLayout />}>
    <Route index element={<Dashboard />} />
    <Route path="documents" element={<DocumentsList />} />
    <Route path="documents/:id/edit" element={<DocumentEditor />} />
    <Route path="templates" element={<TemplatesList />} />
    <Route path="templates/:id/edit" element={<TemplateEditor />} />
    <Route path="profile" element={<Profile />} />
  </Route>
</Routes>
```

## 🎨 Sistema de Design

### Paleta de Cores
```css
:root {
  --primary-blue: #3B82F6;
  --success-green: #10B981;
  --error-red: #EF4444;
  --warning-yellow: #F59E0B;
  --gray-50: #F9FAFB;
  --gray-100: #F3F4F6;
  --gray-900: #111827;
}
```

### Componentes Base

#### Button
```typescript
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'danger';
  size: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
}
```

#### Modal
```typescript
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  size: 'sm' | 'md' | 'lg' | 'xl';
  children: React.ReactNode;
}
```

## 🔧 Configuração de Desenvolvimento

### Variáveis de Ambiente (.env)
```bash
# Flask
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///legalai.db

# JWT
JWT_SECRET_KEY=your_jwt_secret_here

# OpenAI (opcional)
OPENAI_API_KEY=your_openai_key_here

# Upload
MAX_CONTENT_LENGTH=16777216  # 16MB
UPLOAD_FOLDER=uploads

# CORS
CORS_ORIGINS=http://localhost:3000
```

### Dependências Python (requirements.txt)
```
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-JWT-Extended==4.5.3
Flask-CORS==4.0.0
python-dotenv==1.0.0
Werkzeug==2.3.7
python-docx==0.8.11
PyPDF2==3.0.1
reportlab==4.0.4
weasyprint==60.0
```

### Dependências Node.js (package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.15.0",
    "typescript": "^5.2.2",
    "@types/react": "^18.2.22",
    "@types/react-dom": "^18.2.7"
  },
  "devDependencies": {
    "tailwindcss": "^3.3.3",
    "autoprefixer": "^10.4.15",
    "postcss": "^8.4.29"
  }
}
```

## 🚀 Deploy e Produção

### Checklist de Deploy
- [ ] Configurar banco de produção (PostgreSQL/MySQL)
- [ ] Configurar variáveis de ambiente de produção
- [ ] Implementar HTTPS
- [ ] Configurar CORS para domínio de produção
- [ ] Implementar rate limiting
- [ ] Configurar logs de produção
- [ ] Implementar backup automático do banco
- [ ] Configurar monitoramento (Sentry, etc.)

### Docker (Futuro)
```dockerfile
# Dockerfile para produção
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5001

CMD ["gunicorn", "--bind", "0.0.0.0:5001", "src.main:app"]
```

## 🧪 Testes

### Estrutura de Testes (Futuro)
```
tests/
├── backend/
│   ├── test_auth.py
│   ├── test_documents.py
│   └── test_templates.py
└── frontend/
    ├── components/
    ├── pages/
    └── hooks/
```

### Exemplo de Teste Backend
```python
def test_login_success():
    response = client.post('/api/auth/login', json={
        'email': 'admin@legalai.com',
        'password': 'admin123'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json
```

## 📊 Monitoramento e Logs

### Estrutura de Logs
```
logs/
├── application.log    # Log geral da aplicação
├── backend.log       # Logs específicos do Flask
├── frontend.log      # Logs do React (desenvolvimento)
└── error.log         # Logs de erro
```

### Health Check
```python
@app.route('/api/health')
def health_check():
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'database': 'connected'
    }
```

## 🔒 Segurança

### Medidas Implementadas
- **JWT Tokens** para autenticação
- **Hash de senhas** com salt
- **CORS** configurado
- **Validação de entrada** em todas as rotas
- **Rate limiting** (recomendado para produção)
- **HTTPS** (obrigatório em produção)

### Boas Práticas
- Nunca commitar chaves secretas
- Usar variáveis de ambiente para configurações sensíveis
- Implementar logs de auditoria
- Validar e sanitizar todas as entradas
- Implementar timeout em requests

## 🎯 Performance

### Otimizações Frontend
- **Code splitting** com React.lazy()
- **Memoização** de componentes pesados
- **Debounce** em campos de busca
- **Virtual scrolling** para listas grandes
- **Image optimization** para uploads

### Otimizações Backend
- **Indexação** adequada no banco
- **Paginação** em listagens
- **Cache** de queries frequentes
- **Compressão** de respostas
- **Connection pooling** para banco

---

**Esta documentação deve ser atualizada conforme a aplicação evolui.** 

## 🤖 Sistema de IA Jurídica Especializada

### Interface AdvancedAIFeatures
```typescript
interface AdvancedAIFeatures {
  // Análise semântica de contratos
  contractAnalysis: {
    riskAssessment: number;
    missingClauses: string[];
    recommendedClauses: ClauseRecommendation[];
    legalCompliance: ComplianceScore;
  };
  
  // Geração automática de documentos
  documentGeneration: {
    templateBasedGeneration: boolean;
    contextAwareGeneration: boolean;
    legalPrecedentIntegration: boolean;
  };
  
  // Pesquisa jurisprudencial
  jurisprudenceSearch: {
    caseSearch: boolean;
    precedentAnalysis: boolean;
    legalTrendAnalysis: boolean;
  };
}
``` 