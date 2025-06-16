# Guia de Implantação - Editor IA JurisSaaS

Este documento descreve os passos necessários para implantar o MVP do Editor IA em ambiente de produção.

## Requisitos de Infraestrutura

### Backend
- Servidor Linux (Ubuntu 20.04 LTS ou superior)
- Python 3.8+
- MySQL 8.0+
- Nginx como proxy reverso
- Certificado SSL (Let's Encrypt recomendado)

### Frontend
- Node.js 16+
- Servidor web para conteúdo estático (Nginx recomendado)
- Certificado SSL (mesmo do backend)

## Preparação do Ambiente

### 1. Configuração do Servidor

```bash
# Atualizar pacotes
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y python3-pip python3-venv mysql-server nginx certbot python3-certbot-nginx

# Configurar MySQL
sudo mysql_secure_installation
```

### 2. Configuração do Banco de Dados

```bash
# Acessar MySQL
sudo mysql

# Criar banco de dados e usuário
CREATE DATABASE jurissaas_editor;
CREATE USER 'jurissaas_user'@'localhost' IDENTIFIED BY 'senha_segura';
GRANT ALL PRIVILEGES ON jurissaas_editor.* TO 'jurissaas_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## Implantação do Backend

### 1. Clonar o Repositório

```bash
git clone https://github.com/jurissaas/editor-ia.git
cd editor-ia/backend
```

### 2. Configurar Ambiente Virtual

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto backend:

```
# Configurações do Banco de Dados
DB_USERNAME=jurissaas_user
DB_PASSWORD=senha_segura
DB_HOST=localhost
DB_PORT=3306
DB_NAME=jurissaas_editor

# Configurações JWT
JWT_SECRET_KEY=chave_secreta_muito_segura
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000

# Configurações da API OpenAI
OPENAI_API_KEY=sua_chave_api_openai

# Configurações do Servidor
FLASK_ENV=production
FLASK_APP=src/main.py
```

### 4. Inicializar o Banco de Dados

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 5. Configurar Gunicorn como Servidor WSGI

Instale o Gunicorn:

```bash
pip install gunicorn
```

Crie um arquivo de serviço systemd para o backend:

```bash
sudo nano /etc/systemd/system/jurissaas-editor.service
```

Adicione o seguinte conteúdo:

```
[Unit]
Description=JurisSaaS Editor IA Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/caminho/para/editor-ia/backend
Environment="PATH=/caminho/para/editor-ia/backend/venv/bin"
ExecStart=/caminho/para/editor-ia/backend/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:5000 src.main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Ative e inicie o serviço:

```bash
sudo systemctl enable jurissaas-editor
sudo systemctl start jurissaas-editor
```

## Implantação do Frontend

### 1. Preparar o Build de Produção

```bash
cd /caminho/para/editor-ia/frontend
npm install
npm run build
```

### 2. Configurar Nginx para Servir o Frontend

Crie um arquivo de configuração para o Nginx:

```bash
sudo nano /etc/nginx/sites-available/jurissaas-editor
```

Adicione o seguinte conteúdo:

```
server {
    listen 80;
    server_name seu-dominio.com;

    # Redirecionar HTTP para HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name seu-dominio.com;

    ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem;

    # Configurações SSL recomendadas
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;

    # Frontend
    location / {
        root /caminho/para/editor-ia/frontend/build;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Ative a configuração e obtenha certificados SSL:

```bash
sudo ln -s /etc/nginx/sites-available/jurissaas-editor /etc/nginx/sites-enabled/
sudo certbot --nginx -d seu-dominio.com
sudo nginx -t
sudo systemctl reload nginx
```

## Configuração de Backup

### 1. Backup do Banco de Dados

Crie um script de backup:

```bash
sudo nano /usr/local/bin/backup-jurissaas.sh
```

Adicione o seguinte conteúdo:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/jurissaas"
MYSQL_USER="jurissaas_user"
MYSQL_PASSWORD="senha_segura"
MYSQL_DATABASE="jurissaas_editor"
DATE=$(date +"%Y-%m-%d_%H-%M-%S")

# Criar diretório de backup se não existir
mkdir -p $BACKUP_DIR

# Backup do banco de dados
mysqldump -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Manter apenas os últimos 7 backups
find $BACKUP_DIR -name "db_backup_*.sql.gz" -type f -mtime +7 -delete
```

Torne o script executável e configure um cron job:

```bash
sudo chmod +x /usr/local/bin/backup-jurissaas.sh
sudo crontab -e
```

Adicione a seguinte linha para executar o backup diariamente às 2h da manhã:

```
0 2 * * * /usr/local/bin/backup-jurissaas.sh
```

## Monitoramento e Logs

### 1. Logs do Backend

Os logs do backend podem ser visualizados com:

```bash
sudo journalctl -u jurissaas-editor
```

### 2. Logs do Nginx

```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Atualizações

### 1. Atualizar o Backend

```bash
cd /caminho/para/editor-ia/backend
git pull
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade
sudo systemctl restart jurissaas-editor
```

### 2. Atualizar o Frontend

```bash
cd /caminho/para/editor-ia/frontend
git pull
npm install
npm run build
```

## Troubleshooting

### Problema: Backend não inicia

Verifique os logs:
```bash
sudo journalctl -u jurissaas-editor
```

Possíveis soluções:
- Verificar permissões de arquivos
- Confirmar configurações no arquivo .env
- Verificar conectividade com o banco de dados

### Problema: Frontend não carrega

Verifique os logs do Nginx:
```bash
sudo tail -f /var/log/nginx/error.log
```

Possíveis soluções:
- Verificar permissões da pasta build
- Confirmar configuração do Nginx
- Verificar se o build foi gerado corretamente

### Problema: API retorna erros

Verifique os logs do backend e confirme:
- Conectividade com o banco de dados
- Configuração correta da API OpenAI
- Permissões de usuário e grupo para o serviço

## Segurança

Recomendações adicionais de segurança:

1. Configure um firewall (UFW):
```bash
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

2. Atualize regularmente o sistema:
```bash
sudo apt update && sudo apt upgrade -y
```

3. Configure fail2ban para proteção contra ataques de força bruta:
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

4. Realize backups regulares e teste a restauração periodicamente.

5. Monitore regularmente os logs em busca de atividades suspeitas.
