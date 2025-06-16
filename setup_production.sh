#!/bin/bash

# Script de configuração do ambiente de produção para o Editor IA JurisSaaS
# Este script automatiza a configuração inicial do servidor de produção

echo "Iniciando configuração do ambiente de produção para o Editor IA JurisSaaS..."

# Verificar se está sendo executado como root
if [ "$EUID" -ne 0 ]; then
  echo "Este script deve ser executado como root (sudo)."
  exit 1
fi

# Atualizar pacotes do sistema
echo "Atualizando pacotes do sistema..."
apt update && apt upgrade -y

# Instalar dependências necessárias
echo "Instalando dependências do sistema..."
apt install -y python3-pip python3-venv mysql-server nginx certbot python3-certbot-nginx \
    nodejs npm curl git fail2ban ufw

# Configurar firewall
echo "Configurando firewall..."
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable

# Configurar MySQL
echo "Configurando MySQL..."
mysql_secure_installation

# Criar banco de dados e usuário
echo "Criando banco de dados para o Editor IA..."
read -p "Digite o nome do banco de dados [jurissaas_editor]: " DB_NAME
DB_NAME=${DB_NAME:-jurissaas_editor}

read -p "Digite o nome do usuário do banco de dados [jurissaas_user]: " DB_USER
DB_USER=${DB_USER:-jurissaas_user}

read -s -p "Digite a senha para o usuário do banco de dados: " DB_PASSWORD
echo ""

# Criar banco de dados e usuário
mysql -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -e "CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';"
mysql -e "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

echo "Banco de dados $DB_NAME e usuário $DB_USER criados com sucesso."

# Configurar diretório da aplicação
echo "Configurando diretório da aplicação..."
read -p "Digite o caminho para o diretório da aplicação [/var/www/jurissaas]: " APP_DIR
APP_DIR=${APP_DIR:-/var/www/jurissaas}

# Criar diretório da aplicação
mkdir -p $APP_DIR
mkdir -p $APP_DIR/backend
mkdir -p $APP_DIR/frontend

# Configurar permissões
echo "Configurando permissões..."
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR

# Configurar domínio
echo "Configurando domínio..."
read -p "Digite o domínio para a aplicação (ex: app.jurissaas.com.br): " DOMAIN

# Configurar Nginx
echo "Configurando Nginx..."
cat > /etc/nginx/sites-available/jurissaas << EOF
server {
    listen 80;
    server_name $DOMAIN;

    # Redirecionar HTTP para HTTPS
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name $DOMAIN;

    # Certificados SSL serão configurados pelo Certbot

    # Configurações SSL recomendadas
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;

    # Frontend
    location / {
        root $APP_DIR/frontend/build;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Ativar configuração do Nginx
ln -sf /etc/nginx/sites-available/jurissaas /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# Obter certificados SSL com Certbot
echo "Obtendo certificados SSL com Certbot..."
certbot --nginx -d $DOMAIN

# Configurar serviço systemd para o backend
echo "Configurando serviço systemd para o backend..."
cat > /etc/systemd/system/jurissaas-backend.service << EOF
[Unit]
Description=JurisSaaS Editor IA Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/backend/venv/bin"
ExecStart=$APP_DIR/backend/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:5000 src.main:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Configurar script de backup
echo "Configurando script de backup..."
cat > /usr/local/bin/backup-jurissaas.sh << EOF
#!/bin/bash
BACKUP_DIR="/var/backups/jurissaas"
MYSQL_USER="$DB_USER"
MYSQL_PASSWORD="$DB_PASSWORD"
MYSQL_DATABASE="$DB_NAME"
DATE=\$(date +"%Y-%m-%d_%H-%M-%S")

# Criar diretório de backup se não existir
mkdir -p \$BACKUP_DIR

# Backup do banco de dados
mysqldump -u \$MYSQL_USER -p\$MYSQL_PASSWORD \$MYSQL_DATABASE | gzip > \$BACKUP_DIR/db_backup_\$DATE.sql.gz

# Manter apenas os últimos 7 backups
find \$BACKUP_DIR -name "db_backup_*.sql.gz" -type f -mtime +7 -delete
EOF

chmod +x /usr/local/bin/backup-jurissaas.sh

# Configurar cron job para backup diário
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup-jurissaas.sh") | crontab -

# Configurar fail2ban
echo "Configurando fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

echo "Configuração do ambiente de produção concluída com sucesso!"
echo ""
echo "Próximos passos:"
echo "1. Clone o repositório do projeto para $APP_DIR"
echo "2. Configure as variáveis de ambiente no arquivo .env"
echo "3. Execute o deploy do backend e frontend"
echo "4. Inicie o serviço do backend: systemctl enable jurissaas-backend && systemctl start jurissaas-backend"
echo ""
echo "Domínio configurado: $DOMAIN"
echo "Diretório da aplicação: $APP_DIR"
echo "Banco de dados: $DB_NAME"
echo ""
echo "Lembre-se de configurar as variáveis de ambiente no arquivo .env do backend!"
