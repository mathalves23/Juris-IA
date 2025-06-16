#!/bin/bash

# Script de deploy para o Editor IA JurisSaaS
# Este script automatiza o processo de deploy do backend e frontend em ambiente de produção

echo "Iniciando deploy do Editor IA JurisSaaS..."

# Verificar se está no diretório correto
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
  echo "Erro: Execute este script no diretório raiz do projeto (onde estão as pastas backend e frontend)"
  exit 1
fi

# Verificar variáveis de ambiente
if [ -z "$APP_DIR" ]; then
  read -p "Digite o caminho para o diretório da aplicação em produção [/var/www/jurissaas]: " APP_DIR
  APP_DIR=${APP_DIR:-/var/www/jurissaas}
fi

# Verificar se o diretório de produção existe
if [ ! -d "$APP_DIR" ]; then
  echo "Erro: Diretório de produção $APP_DIR não encontrado."
  echo "Execute primeiro o script setup_production.sh para configurar o ambiente."
  exit 1
fi

echo "Realizando deploy para: $APP_DIR"

# Deploy do Backend
echo "Iniciando deploy do backend..."

# Criar ambiente virtual Python se não existir
if [ ! -d "$APP_DIR/backend/venv" ]; then
  echo "Criando ambiente virtual Python..."
  python3 -m venv $APP_DIR/backend/venv
fi

# Copiar arquivos do backend
echo "Copiando arquivos do backend..."
rsync -av --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' backend/ $APP_DIR/backend/

# Instalar dependências do backend
echo "Instalando dependências do backend..."
source $APP_DIR/backend/venv/bin/activate
pip install -r $APP_DIR/backend/requirements.txt
pip install gunicorn

# Verificar se arquivo .env existe
if [ ! -f "$APP_DIR/backend/.env" ]; then
  echo "ATENÇÃO: Arquivo .env não encontrado no diretório de produção."
  echo "Criando arquivo .env de exemplo..."
  
  # Solicitar informações para o arquivo .env
  read -p "Digite o nome do banco de dados [jurissaas_editor]: " DB_NAME
  DB_NAME=${DB_NAME:-jurissaas_editor}
  
  read -p "Digite o nome do usuário do banco de dados [jurissaas_user]: " DB_USER
  DB_USER=${DB_USER:-jurissaas_user}
  
  read -s -p "Digite a senha do banco de dados: " DB_PASSWORD
  echo ""
  
  read -s -p "Digite a chave secreta para JWT: " JWT_SECRET
  echo ""
  
  read -s -p "Digite a chave da API OpenAI: " OPENAI_KEY
  echo ""
  
  # Criar arquivo .env
  cat > $APP_DIR/backend/.env << EOF
# Configurações do Banco de Dados
DB_USERNAME=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=3306
DB_NAME=$DB_NAME

# Configurações JWT
JWT_SECRET_KEY=$JWT_SECRET
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000

# Configurações da API OpenAI
OPENAI_API_KEY=$OPENAI_KEY

# Configurações do Servidor
FLASK_ENV=production
FLASK_APP=src/main.py
EOF

  echo "Arquivo .env criado com sucesso."
fi

# Executar migrações do banco de dados
echo "Executando migrações do banco de dados..."
cd $APP_DIR/backend
source venv/bin/activate
export FLASK_APP=src/main.py
flask db upgrade

# Voltar para o diretório raiz
cd -

# Deploy do Frontend
echo "Iniciando deploy do frontend..."

# Instalar dependências do frontend
echo "Instalando dependências do frontend..."
cd frontend
npm install

# Criar arquivo .env para o frontend se não existir
if [ ! -f ".env" ]; then
  echo "Criando arquivo .env para o frontend..."
  
  # Solicitar URL da API
  read -p "Digite a URL da API (ex: https://app.jurissaas.com.br/api): " API_URL
  
  # Criar arquivo .env
  cat > .env << EOF
REACT_APP_API_URL=$API_URL
EOF

  echo "Arquivo .env do frontend criado."
fi

# Construir o frontend
echo "Construindo o frontend..."
npm run build

# Copiar arquivos do frontend para o diretório de produção
echo "Copiando arquivos do frontend para produção..."
rsync -av --delete build/ $APP_DIR/frontend/build/

# Voltar para o diretório raiz
cd ..

# Configurar permissões
echo "Configurando permissões..."
sudo chown -R www-data:www-data $APP_DIR
sudo chmod -R 755 $APP_DIR

# Reiniciar serviços
echo "Reiniciando serviços..."
sudo systemctl restart jurissaas-backend
sudo systemctl restart nginx

echo "Deploy concluído com sucesso!"
echo ""
echo "Para verificar o status do backend:"
echo "  sudo systemctl status jurissaas-backend"
echo ""
echo "Para verificar os logs do backend:"
echo "  sudo journalctl -u jurissaas-backend"
echo ""
echo "Para verificar os logs do Nginx:"
echo "  sudo tail -f /var/log/nginx/access.log"
echo "  sudo tail -f /var/log/nginx/error.log"
