from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.extensions import db
from src.models.client import Client
from src.models.user import User

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/clients', methods=['GET'])
@jwt_required()
def get_clients():
    """Listar clientes do usuário logado"""
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        search = request.args.get('search', '')
        
        query = Client.query.filter_by(usuario_id=user_id, ativo=True)
        
        if search:
            query = query.filter(
                db.or_(
                    Client.nome.contains(search),
                    Client.documento.contains(search),
                    Client.email.contains(search)
                )
            )
        
        clients = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'clients': [client.to_dict() for client in clients.items],
            'pagination': {
                'page': page,
                'pages': clients.pages,
                'per_page': per_page,
                'total': clients.total
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@clients_bp.route('/clients', methods=['POST'])
@jwt_required()
def create_client():
    """Criar novo cliente"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validações básicas
        if not data.get('nome') or not data.get('documento'):
            return jsonify({'error': 'Nome e documento são obrigatórios'}), 400
        
        # Verificar se documento já existe
        existing = Client.query.filter_by(documento=data['documento']).first()
        if existing:
            return jsonify({'error': 'Cliente com este documento já existe'}), 400
        
        client = Client(
            nome=data['nome'],
            documento=data['documento'],
            tipo_pessoa=data.get('tipo_pessoa', 'PF'),
            email=data.get('email'),
            telefone=data.get('telefone'),
            endereco=data.get('endereco'),
            observacoes=data.get('observacoes'),
            usuario_id=user_id
        )
        
        db.session.add(client)
        db.session.commit()
        
        return jsonify({
            'message': 'Cliente criado com sucesso',
            'client': client.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@clients_bp.route('/clients/<int:client_id>', methods=['GET'])
@jwt_required()
def get_client(client_id):
    """Obter detalhes de um cliente específico"""
    try:
        user_id = get_jwt_identity()
        client = Client.query.filter_by(id=client_id, usuario_id=user_id).first()
        
        if not client:
            return jsonify({'error': 'Cliente não encontrado'}), 404
        
        return jsonify({'client': client.to_dict()})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@clients_bp.route('/clients/<int:client_id>', methods=['PUT'])
@jwt_required()
def update_client(client_id):
    """Atualizar cliente"""
    try:
        user_id = get_jwt_identity()
        client = Client.query.filter_by(id=client_id, usuario_id=user_id).first()
        
        if not client:
            return jsonify({'error': 'Cliente não encontrado'}), 404
        
        data = request.get_json()
        
        # Verificar se documento já existe em outro cliente
        if data.get('documento') and data['documento'] != client.documento:
            existing = Client.query.filter_by(documento=data['documento']).first()
            if existing:
                return jsonify({'error': 'Cliente com este documento já existe'}), 400
        
        # Atualizar campos
        for field in ['nome', 'documento', 'tipo_pessoa', 'email', 'telefone', 'endereco', 'observacoes']:
            if field in data:
                setattr(client, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Cliente atualizado com sucesso',
            'client': client.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@clients_bp.route('/clients/<int:client_id>', methods=['DELETE'])
@jwt_required()
def delete_client(client_id):
    """Excluir cliente (soft delete)"""
    try:
        user_id = get_jwt_identity()
        client = Client.query.filter_by(id=client_id, usuario_id=user_id).first()
        
        if not client:
            return jsonify({'error': 'Cliente não encontrado'}), 404
        
        # Verificar se há processos ativos
        if client.processos:
            active_processes = [p for p in client.processos if p.status == 'Ativo']
            if active_processes:
                return jsonify({
                    'error': 'Não é possível excluir cliente com processos ativos',
                    'active_processes': len(active_processes)
                }), 400
        
        client.ativo = False
        db.session.commit()
        
        return jsonify({'message': 'Cliente excluído com sucesso'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@clients_bp.route('/clients/<int:client_id>/processes', methods=['GET'])
@jwt_required()
def get_client_processes(client_id):
    """Listar processos de um cliente"""
    try:
        user_id = get_jwt_identity()
        client = Client.query.filter_by(id=client_id, usuario_id=user_id).first()
        
        if not client:
            return jsonify({'error': 'Cliente não encontrado'}), 404
        
        processes = [processo.to_dict() for processo in client.processos]
        
        return jsonify({
            'client': client.to_dict(),
            'processes': processes
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 