from flask_socketio import emit, join_room, leave_room, disconnect
from flask_jwt_extended import decode_token
from extensions import socketio
from models.user import User
from models.notification import Notification
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Dicionário para rastrear usuários conectados
connected_users = {}

@socketio.on('connect')
def handle_connect(auth):
    """Conecta usuário ao WebSocket"""
    try:
        # Verificar token JWT
        if not auth or 'token' not in auth:
            logger.warning("Conexão WebSocket sem token")
            disconnect()
            return False
        
        token = auth['token']
        try:
            # Decodificar token
            decoded_token = decode_token(token)
            user_id = decoded_token.get('sub')
            
            if not user_id:
                logger.warning("Token inválido na conexão WebSocket")
                disconnect()
                return False
                
            # Verificar se usuário existe
            user = User.query.get(user_id)
            if not user:
                logger.warning(f"Usuário {user_id} não encontrado")
                disconnect()
                return False
            
            # Adicionar usuário à sala pessoal
            join_room(f'user_{user_id}')
            
            # Registrar usuário conectado
            connected_users[request.sid] = {
                'user_id': user_id,
                'username': user.nome,
                'email': user.email,
                'connected_at': datetime.utcnow().isoformat(),
                'rooms': [f'user_{user_id}']
            }
            
            logger.info(f"Usuário {user.nome} conectado via WebSocket (ID: {user_id})")
            
            # Enviar contagem de notificações não lidas
            unread_count = Notification.get_unread_count(user_id)
            emit('unread_count_updated', {'count': unread_count})
            
            # Notificar outros usuários sobre a conexão (opcional)
            emit('user_connected', {
                'user_id': user_id,
                'username': user.nome,
                'timestamp': datetime.utcnow().isoformat()
            }, broadcast=True, include_self=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao decodificar token: {str(e)}")
            disconnect()
            return False
            
    except Exception as e:
        logger.error(f"Erro na conexão WebSocket: {str(e)}")
        disconnect()
        return False

@socketio.on('disconnect')
def handle_disconnect():
    """Desconecta usuário do WebSocket"""
    try:
        if request.sid in connected_users:
            user_info = connected_users[request.sid]
            user_id = user_info['user_id']
            username = user_info['username']
            
            # Remover usuário da lista de conectados
            del connected_users[request.sid]
            
            logger.info(f"Usuário {username} desconectado do WebSocket (ID: {user_id})")
            
            # Notificar outros usuários sobre a desconexão (opcional)
            emit('user_disconnected', {
                'user_id': user_id,
                'username': username,
                'timestamp': datetime.utcnow().isoformat()
            }, broadcast=True, include_self=False)
            
    except Exception as e:
        logger.error(f"Erro na desconexão WebSocket: {str(e)}")

@socketio.on('join_room')
def handle_join_room(data):
    """Permite usuário entrar em uma sala específica"""
    try:
        if request.sid not in connected_users:
            return False
        
        room = data.get('room')
        if not room:
            return False
        
        user_info = connected_users[request.sid]
        user_id = user_info['user_id']
        
        # Verificar permissões (implementar lógica de autorização)
        if not _can_join_room(user_id, room):
            emit('error', {'message': 'Sem permissão para entrar na sala'})
            return False
        
        join_room(room)
        
        # Atualizar lista de salas do usuário
        if room not in user_info['rooms']:
            user_info['rooms'].append(room)
        
        logger.info(f"Usuário {user_info['username']} entrou na sala {room}")
        
        # Notificar outros usuários na sala
        emit('user_joined_room', {
            'user_id': user_id,
            'username': user_info['username'],
            'room': room,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room, include_self=False)
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao entrar na sala: {str(e)}")
        return False

@socketio.on('leave_room')
def handle_leave_room(data):
    """Permite usuário sair de uma sala específica"""
    try:
        if request.sid not in connected_users:
            return False
        
        room = data.get('room')
        if not room:
            return False
        
        user_info = connected_users[request.sid]
        user_id = user_info['user_id']
        
        leave_room(room)
        
        # Remover sala da lista do usuário
        if room in user_info['rooms']:
            user_info['rooms'].remove(room)
        
        logger.info(f"Usuário {user_info['username']} saiu da sala {room}")
        
        # Notificar outros usuários na sala
        emit('user_left_room', {
            'user_id': user_id,
            'username': user_info['username'],
            'room': room,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room, include_self=False)
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao sair da sala: {str(e)}")
        return False

@socketio.on('send_message')
def handle_send_message(data):
    """Envia mensagem para uma sala específica"""
    try:
        if request.sid not in connected_users:
            return False
        
        user_info = connected_users[request.sid]
        user_id = user_info['user_id']
        room = data.get('room')
        message = data.get('message')
        
        if not room or not message:
            return False
        
        # Verificar se usuário está na sala
        if room not in user_info['rooms']:
            emit('error', {'message': 'Usuário não está na sala'})
            return False
        
        # Criar objeto de mensagem
        message_data = {
            'id': f"msg_{datetime.utcnow().timestamp()}",
            'user_id': user_id,
            'username': user_info['username'],
            'message': message,
            'room': room,
            'timestamp': datetime.utcnow().isoformat(),
            'type': data.get('type', 'text')
        }
        
        # Enviar mensagem para a sala
        emit('message_received', message_data, room=room)
        
        logger.info(f"Mensagem enviada por {user_info['username']} na sala {room}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {str(e)}")
        return False

@socketio.on('typing_start')
def handle_typing_start(data):
    """Indica que usuário começou a digitar"""
    try:
        if request.sid not in connected_users:
            return False
        
        user_info = connected_users[request.sid]
        room = data.get('room')
        
        if not room or room not in user_info['rooms']:
            return False
        
        emit('user_typing', {
            'user_id': user_info['user_id'],
            'username': user_info['username'],
            'room': room,
            'typing': True
        }, room=room, include_self=False)
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao indicar digitação: {str(e)}")
        return False

@socketio.on('typing_stop')
def handle_typing_stop(data):
    """Indica que usuário parou de digitar"""
    try:
        if request.sid not in connected_users:
            return False
        
        user_info = connected_users[request.sid]
        room = data.get('room')
        
        if not room or room not in user_info['rooms']:
            return False
        
        emit('user_typing', {
            'user_id': user_info['user_id'],
            'username': user_info['username'],
            'room': room,
            'typing': False
        }, room=room, include_self=False)
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao parar indicação de digitação: {str(e)}")
        return False

@socketio.on('document_editing')
def handle_document_editing(data):
    """Sincroniza edição colaborativa de documentos"""
    try:
        if request.sid not in connected_users:
            return False
        
        user_info = connected_users[request.sid]
        document_id = data.get('document_id')
        operation = data.get('operation')
        
        if not document_id or not operation:
            return False
        
        # Sala específica para o documento
        room = f'document_{document_id}'
        
        # Verificar permissões de edição (implementar lógica)
        if not _can_edit_document(user_info['user_id'], document_id):
            emit('error', {'message': 'Sem permissão para editar documento'})
            return False
        
        # Aplicar operação e sincronizar com outros usuários
        sync_data = {
            'document_id': document_id,
            'operation': operation,
            'user_id': user_info['user_id'],
            'username': user_info['username'],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        emit('document_synced', sync_data, room=room, include_self=False)
        
        return True
        
    except Exception as e:
        logger.error(f"Erro na edição colaborativa: {str(e)}")
        return False

@socketio.on('cursor_position')
def handle_cursor_position(data):
    """Sincroniza posição do cursor em edição colaborativa"""
    try:
        if request.sid not in connected_users:
            return False
        
        user_info = connected_users[request.sid]
        document_id = data.get('document_id')
        position = data.get('position')
        
        if not document_id or position is None:
            return False
        
        room = f'document_{document_id}'
        
        cursor_data = {
            'document_id': document_id,
            'user_id': user_info['user_id'],
            'username': user_info['username'],
            'position': position,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        emit('cursor_updated', cursor_data, room=room, include_self=False)
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao sincronizar cursor: {str(e)}")
        return False

@socketio.on('get_online_users')
def handle_get_online_users():
    """Retorna lista de usuários online"""
    try:
        online_users = []
        for sid, user_info in connected_users.items():
            online_users.append({
                'user_id': user_info['user_id'],
                'username': user_info['username'],
                'connected_at': user_info['connected_at']
            })
        
        emit('online_users', {'users': online_users})
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao buscar usuários online: {str(e)}")
        return False

def _can_join_room(user_id: int, room: str) -> bool:
    """Verifica se usuário pode entrar na sala"""
    try:
        # Sala pessoal - sempre permitida
        if room == f'user_{user_id}':
            return True
        
        # Salas de documento - verificar permissões
        if room.startswith('document_'):
            document_id = room.replace('document_', '')
            return _can_edit_document(user_id, document_id)
        
        # Salas de projeto - verificar participação
        if room.startswith('project_'):
            project_id = room.replace('project_', '')
            return _can_access_project(user_id, project_id)
        
        # Por padrão, não permitir
        return False
        
    except Exception as e:
        logger.error(f"Erro ao verificar permissão de sala: {str(e)}")
        return False

def _can_edit_document(user_id: int, document_id: str) -> bool:
    """Verifica se usuário pode editar documento"""
    try:
        # Implementar lógica de verificação de permissões
        # Por enquanto, permitir para todos os usuários autenticados
        return True
        
    except Exception as e:
        logger.error(f"Erro ao verificar permissão de documento: {str(e)}")
        return False

def _can_access_project(user_id: int, project_id: str) -> bool:
    """Verifica se usuário pode acessar projeto"""
    try:
        # Implementar lógica de verificação de participação em projeto
        return True
        
    except Exception as e:
        logger.error(f"Erro ao verificar acesso ao projeto: {str(e)}")
        return False

# Função para enviar notificação via WebSocket
def send_notification_to_user(user_id: int, notification_data: dict):
    """Envia notificação para usuário específico via WebSocket"""
    try:
        socketio.emit(
            'new_notification',
            notification_data,
            room=f'user_{user_id}'
        )
        logger.info(f"Notificação enviada via WebSocket para usuário {user_id}")
        
    except Exception as e:
        logger.error(f"Erro ao enviar notificação via WebSocket: {str(e)}")

# Função para broadcast de sistema
def broadcast_system_message(message: str, type: str = 'info'):
    """Envia mensagem de sistema para todos os usuários conectados"""
    try:
        socketio.emit('system_message', {
            'message': message,
            'type': type,
            'timestamp': datetime.utcnow().isoformat()
        }, broadcast=True)
        
        logger.info(f"Mensagem de sistema enviada: {message}")
        
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem de sistema: {str(e)}")

# Função para obter estatísticas de usuários online
def get_online_stats():
    """Retorna estatísticas de usuários online"""
    try:
        total_connected = len(connected_users)
        unique_users = len(set(user_info['user_id'] for user_info in connected_users.values()))
        
        return {
            'total_connections': total_connected,
            'unique_users': unique_users,
            'connected_users': list(connected_users.values())
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {str(e)}")
        return {'total_connections': 0, 'unique_users': 0, 'connected_users': []} 