#!/usr/bin/env python3
import os
import sys
import logging
from datetime import datetime

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from flask import Flask, request
from flask_socketio import SocketIO
from flask_cors import CORS
from config import Config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/websocket.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_websocket_app():
    """Cria aplicação Flask para WebSocket"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # CORS para permitir conexões do frontend
    CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)
    
    # Configurar SocketIO
    socketio = SocketIO(
        app,
        cors_allowed_origins=Config.CORS_ORIGINS,
        async_mode='threading',
        logger=True,
        engineio_logger=True,
        ping_timeout=60,
        ping_interval=25
    )
    
    # Registrar eventos WebSocket
    from websocket.events import (
        handle_connect,
        handle_disconnect,
        handle_join_room,
        handle_leave_room,
        handle_send_message,
        handle_typing_start,
        handle_typing_stop,
        handle_document_editing,
        handle_cursor_position,
        handle_get_online_users
    )
    
    # Eventos básicos
    @socketio.on('connect')
    def on_connect(auth):
        return handle_connect(auth)
    
    @socketio.on('disconnect')
    def on_disconnect():
        return handle_disconnect()
    
    @socketio.on('join_room')
    def on_join_room(data):
        return handle_join_room(data)
    
    @socketio.on('leave_room')
    def on_leave_room(data):
        return handle_leave_room(data)
    
    @socketio.on('send_message')
    def on_send_message(data):
        return handle_send_message(data)
    
    @socketio.on('typing_start')
    def on_typing_start(data):
        return handle_typing_start(data)
    
    @socketio.on('typing_stop')
    def on_typing_stop(data):
        return handle_typing_stop(data)
    
    @socketio.on('document_editing')
    def on_document_editing(data):
        return handle_document_editing(data)
    
    @socketio.on('cursor_position')
    def on_cursor_position(data):
        return handle_cursor_position(data)
    
    @socketio.on('get_online_users')
    def on_get_online_users():
        return handle_get_online_users()
    
    # Eventos de notificação
    @socketio.on('mark_notification_read')
    def on_mark_notification_read(data):
        """Marca notificação como lida via WebSocket"""
        try:
            notification_id = data.get('notification_id')
            if notification_id:
                # Implementar lógica para marcar como lida
                socketio.emit('notification_marked_read', {
                    'notification_id': notification_id,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=request.sid)
                
        except Exception as e:
            logger.error(f"Erro ao marcar notificação como lida: {str(e)}")
    
    # Eventos de colaboração
    @socketio.on('start_collaboration')
    def on_start_collaboration(data):
        """Inicia sessão de colaboração em documento"""
        try:
            document_id = data.get('document_id')
            if document_id:
                room = f'document_{document_id}'
                
                # Entrar na sala do documento
                from flask_socketio import join_room
                join_room(room)
                
                # Notificar outros usuários
                socketio.emit('collaboration_started', {
                    'document_id': document_id,
                    'user_id': data.get('user_id'),
                    'timestamp': datetime.utcnow().isoformat()
                }, room=room, include_self=False)
                
        except Exception as e:
            logger.error(f"Erro ao iniciar colaboração: {str(e)}")
    
    @socketio.on('end_collaboration')
    def on_end_collaboration(data):
        """Termina sessão de colaboração"""
        try:
            document_id = data.get('document_id')
            if document_id:
                room = f'document_{document_id}'
                
                # Sair da sala do documento
                from flask_socketio import leave_room
                leave_room(room)
                
                # Notificar outros usuários
                socketio.emit('collaboration_ended', {
                    'document_id': document_id,
                    'user_id': data.get('user_id'),
                    'timestamp': datetime.utcnow().isoformat()
                }, room=room, include_self=False)
                
        except Exception as e:
            logger.error(f"Erro ao terminar colaboração: {str(e)}")
    
    # Eventos de sistema
    @socketio.on('ping')
    def on_ping():
        """Responde ao ping para manter conexão ativa"""
        socketio.emit('pong', {'timestamp': datetime.utcnow().isoformat()})
    
    @socketio.on('heartbeat')
    def on_heartbeat():
        """Heartbeat para monitorar conexão"""
        socketio.emit('heartbeat_response', {
            'timestamp': datetime.utcnow().isoformat(),
            'server_time': datetime.utcnow().isoformat()
        })
    
    # Manipuladores de erro
    @socketio.on_error_default
    def default_error_handler(e):
        logger.error(f"Erro WebSocket: {str(e)}")
        socketio.emit('error', {
            'message': 'Erro interno do servidor',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    # Rotas HTTP básicas
    @app.route('/health')
    def health_check():
        """Endpoint de health check"""
        return {
            'status': 'healthy',
            'service': 'WebSocket Server',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }
    
    @app.route('/stats')
    def get_stats():
        """Endpoint para estatísticas do WebSocket"""
        try:
            from websocket.events import get_online_stats
            stats = get_online_stats()
            
            return {
                'status': 'success',
                'data': stats,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {str(e)}")
            return {
                'status': 'error',
                'message': 'Erro ao obter estatísticas'
            }, 500
    
    # Evento de inicialização
    @socketio.on('connect')
    def handle_connect_logging():
        """Log de conexões para monitoramento"""
        logger.info(f"Nova conexão WebSocket: {request.sid}")
    
    @socketio.on('disconnect')
    def handle_disconnect_logging():
        """Log de desconexões para monitoramento"""
        logger.info(f"Desconexão WebSocket: {request.sid}")
    
    return app, socketio

def main():
    """Função principal para executar o servidor WebSocket"""
    try:
        # Criar diretório de logs se não existir
        os.makedirs('logs', exist_ok=True)
        
        logger.info("Iniciando servidor WebSocket...")
        
        # Criar aplicação
        app, socketio = create_websocket_app()
        
        # Configurações do servidor
        host = os.getenv('WEBSOCKET_HOST', 'localhost')
        port = int(os.getenv('WEBSOCKET_PORT', 5006))
        debug = os.getenv('FLASK_ENV', 'development') == 'development'
        
        logger.info(f"Servidor WebSocket será executado em {host}:{port}")
        logger.info(f"Modo debug: {debug}")
        
        # Executar servidor
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            use_reloader=False,  # Evitar recarregamento automático
            log_output=True
        )
        
    except KeyboardInterrupt:
        logger.info("Servidor WebSocket interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro ao executar servidor WebSocket: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 