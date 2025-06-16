#!/bin/bash

# Script de configuração do ambiente de desenvolvimento para o Editor IA JurisSaaS
# Este script configura o ambiente de desenvolvimento local para o MVP do Editor IA

echo "Iniciando configuração do ambiente de desenvolvimento para o Editor IA JurisSaaS..."

# Verificar se está no diretório correto
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
  echo "Erro: Execute este script no diretório raiz do projeto (onde estão as pastas backend e frontend)"
  exit 1
fi

# Configurar backend
echo "Configurando o ambiente backend..."
cd backend

# Criar ambiente virtual Python
echo "Criando ambiente virtual Python..."
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
echo "Instalando dependências do backend..."
pip install -r requirements.txt

# Criar arquivo .env de exemplo se não existir
if [ ! -f ".env" ]; then
  echo "Criando arquivo .env de exemplo..."
  cat > .env << EOF
# Configurações do Banco de Dados
DB_USERNAME=root
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=jurissaas_editor

# Configurações JWT
JWT_SECRET_KEY=dev_secret_key_change_in_production
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000

# Configurações da API OpenAI
OPENAI_API_KEY=sk-dummy-key-for-development

# Configurações do Servidor
FLASK_ENV=development
FLASK_APP=src/main.py
EOF
  echo "Arquivo .env criado. Edite-o com suas configurações."
fi

# Inicializar banco de dados
echo "Inicializando banco de dados..."
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Voltar para o diretório raiz
cd ..

# Configurar frontend
echo "Configurando o ambiente frontend..."
cd frontend

# Instalar dependências
echo "Instalando dependências do frontend..."
npm install

# Criar arquivo .env para frontend se não existir
if [ ! -f ".env" ]; then
  echo "Criando arquivo .env para o frontend..."
  cat > .env << EOF
REACT_APP_API_URL=http://localhost:5000/api
EOF
  echo "Arquivo .env do frontend criado."
fi

# Voltar para o diretório raiz
cd ..

echo "Configuração do ambiente de desenvolvimento concluída!"
echo ""
echo "Para iniciar o backend:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  flask run"
echo ""
echo "Para iniciar o frontend:"
echo "  cd frontend"
echo "  npm start"
echo ""
echo "Acesse o aplicativo em: http://localhost:3000"
