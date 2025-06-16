from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.extensions import db
from src.models.kanban import KanbanBoard, KanbanList, KanbanCard, ChecklistItem, Tag, CardHistory
from src.models.notification import Notification
from datetime import datetime

kanban_bp = Blueprint('kanban', __name__)

# Rotas para Quadros Kanban
@kanban_bp.route('/kanban/boards', methods=['GET'])
@jwt_required()
def get_boards():
    """Listar quadros do usuário"""
    try:
        user_id = get_jwt_identity()
        boards = KanbanBoard.query.filter_by(criado_por=user_id, status='Ativo').all()
        
        return jsonify({
            'boards': [board.to_dict() for board in boards]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@kanban_bp.route('/kanban/boards', methods=['POST'])
@jwt_required()
def create_board():
    """Criar novo quadro Kanban"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('nome'):
            return jsonify({'error': 'Nome do quadro é obrigatório'}), 400
        
        board = KanbanBoard(
            nome=data['nome'],
            cliente_id=data.get('cliente_id'),
            processo_id=data.get('processo_id'),
            area=data.get('area'),
            criado_por=user_id,
            cor=data.get('cor', '#3B82F6')
        )
        
        db.session.add(board)
        db.session.flush()  # Para obter o ID do board
        
        # Criar listas padrão
        default_lists = [
            {'nome': 'A Fazer', 'ordem': 1, 'cor': '#F3F4F6'},
            {'nome': 'Em Andamento', 'ordem': 2, 'cor': '#DBEAFE'},
            {'nome': 'Concluído', 'ordem': 3, 'cor': '#D1FAE5'}
        ]
        
        for list_data in default_lists:
            lista = KanbanList(
                quadro_id=board.id,
                nome=list_data['nome'],
                ordem=list_data['ordem'],
                cor=list_data['cor']
            )
            db.session.add(lista)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Quadro criado com sucesso',
            'board': board.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@kanban_bp.route('/kanban/boards/<int:board_id>', methods=['GET'])
@jwt_required()
def get_board_details(board_id):
    """Obter detalhes completos de um quadro"""
    try:
        user_id = get_jwt_identity()
        board = KanbanBoard.query.filter_by(id=board_id, criado_por=user_id).first()
        
        if not board:
            return jsonify({'error': 'Quadro não encontrado'}), 404
        
        board_data = board.to_dict()
        board_data['listas'] = [lista.to_dict() for lista in board.listas]
        
        return jsonify({'board': board_data})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@kanban_bp.route('/kanban/boards/<int:board_id>/lists', methods=['POST'])
@jwt_required()
def create_list(board_id):
    """Criar nova lista em um quadro"""
    try:
        user_id = get_jwt_identity()
        board = KanbanBoard.query.filter_by(id=board_id, criado_por=user_id).first()
        
        if not board:
            return jsonify({'error': 'Quadro não encontrado'}), 404
        
        data = request.get_json()
        if not data.get('nome'):
            return jsonify({'error': 'Nome da lista é obrigatório'}), 400
        
        # Calcular próxima ordem
        max_ordem = db.session.query(db.func.max(KanbanList.ordem)).filter_by(quadro_id=board_id).scalar() or 0
        
        lista = KanbanList(
            quadro_id=board_id,
            nome=data['nome'],
            ordem=max_ordem + 1,
            cor=data.get('cor', '#F3F4F6')
        )
        
        db.session.add(lista)
        db.session.commit()
        
        return jsonify({
            'message': 'Lista criada com sucesso',
            'list': lista.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@kanban_bp.route('/kanban/lists/<int:list_id>/cards', methods=['POST'])
@jwt_required()
def create_card(list_id):
    """Criar novo cartão em uma lista"""
    try:
        user_id = get_jwt_identity()
        lista = KanbanList.query.get(list_id)
        
        if not lista or lista.quadro.criado_por != user_id:
            return jsonify({'error': 'Lista não encontrada'}), 404
        
        data = request.get_json()
        if not data.get('titulo'):
            return jsonify({'error': 'Título do cartão é obrigatório'}), 400
        
        # Calcular próxima ordem
        max_ordem = db.session.query(db.func.max(KanbanCard.ordem)).filter_by(lista_id=list_id).scalar() or 0
        
        # Processar data limite se fornecida
        data_limite = None
        if data.get('data_limite'):
            try:
                data_limite = datetime.fromisoformat(data['data_limite'].replace('Z', '+00:00'))
            except:
                pass
        
        card = KanbanCard(
            lista_id=list_id,
            titulo=data['titulo'],
            descricao=data.get('descricao'),
            processo_id=data.get('processo_id'),
            responsavel_id=data.get('responsavel_id'),
            data_limite=data_limite,
            prioridade=data.get('prioridade', 'Média'),
            ordem=max_ordem + 1,
            criado_por=user_id
        )
        
        db.session.add(card)
        db.session.flush()
        
        # Registrar histórico
        history = CardHistory(
            cartao_id=card.id,
            usuario_id=user_id,
            tipo_alteracao='Criação',
            valor_novo=f"Cartão '{card.titulo}' criado"
        )
        db.session.add(history)
        
        # Criar notificação se há responsável
        if card.responsavel_id and card.responsavel_id != user_id:
            notification = Notification(
                usuario_id=card.responsavel_id,
                tipo='Tarefa',
                titulo='Nova tarefa atribuída',
                mensagem=f'Você foi atribuído à tarefa: {card.titulo}',
                link=f'/kanban/cards/{card.id}',
                entidade_tipo='cartao',
                entidade_id=card.id
            )
            db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Cartão criado com sucesso',
            'card': card.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@kanban_bp.route('/kanban/cards/<int:card_id>/move', methods=['PUT'])
@jwt_required()
def move_card(card_id):
    """Mover cartão entre listas"""
    try:
        user_id = get_jwt_identity()
        card = KanbanCard.query.get(card_id)
        
        if not card or card.lista.quadro.criado_por != user_id:
            return jsonify({'error': 'Cartão não encontrado'}), 404
        
        data = request.get_json()
        new_list_id = data.get('lista_id')
        new_order = data.get('ordem')
        
        if not new_list_id:
            return jsonify({'error': 'ID da nova lista é obrigatório'}), 400
        
        # Verificar se a nova lista existe e pertence ao usuário
        new_list = KanbanList.query.get(new_list_id)
        if not new_list or new_list.quadro.criado_por != user_id:
            return jsonify({'error': 'Lista de destino não encontrada'}), 404
        
        old_list_name = card.lista.nome
        new_list_name = new_list.nome
        
        # Atualizar cartão
        card.lista_id = new_list_id
        if new_order is not None:
            card.ordem = new_order
        
        # Registrar histórico
        history = CardHistory(
            cartao_id=card.id,
            usuario_id=user_id,
            tipo_alteracao='Movimentação',
            valor_anterior=old_list_name,
            valor_novo=new_list_name
        )
        db.session.add(history)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Cartão movido com sucesso',
            'card': card.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@kanban_bp.route('/kanban/cards/<int:card_id>', methods=['PUT'])
@jwt_required()
def update_card(card_id):
    """Atualizar cartão"""
    try:
        user_id = get_jwt_identity()
        card = KanbanCard.query.get(card_id)
        
        if not card or card.lista.quadro.criado_por != user_id:
            return jsonify({'error': 'Cartão não encontrado'}), 404
        
        data = request.get_json()
        
        # Campos atualizáveis
        updates = []
        for field in ['titulo', 'descricao', 'prioridade', 'status']:
            if field in data and getattr(card, field) != data[field]:
                updates.append(f"{field}: {getattr(card, field)} → {data[field]}")
                setattr(card, field, data[field])
        
        # Data limite
        if 'data_limite' in data:
            try:
                new_date = datetime.fromisoformat(data['data_limite'].replace('Z', '+00:00')) if data['data_limite'] else None
                if card.data_limite != new_date:
                    updates.append(f"Data limite alterada")
                    card.data_limite = new_date
            except:
                pass
        
        # Responsável
        if 'responsavel_id' in data and card.responsavel_id != data['responsavel_id']:
            old_resp = card.responsavel.nome if card.responsavel else 'Nenhum'
            new_resp_id = data['responsavel_id']
            if new_resp_id:
                from src.models.user import User
                new_resp = User.query.get(new_resp_id)
                new_resp_name = new_resp.nome if new_resp else 'Desconhecido'
            else:
                new_resp_name = 'Nenhum'
            
            updates.append(f"Responsável: {old_resp} → {new_resp_name}")
            card.responsavel_id = new_resp_id
            
            # Notificar novo responsável
            if new_resp_id and new_resp_id != user_id:
                notification = Notification(
                    usuario_id=new_resp_id,
                    tipo='Tarefa',
                    titulo='Tarefa atribuída',
                    mensagem=f'Você foi atribuído à tarefa: {card.titulo}',
                    link=f'/kanban/cards/{card.id}',
                    entidade_tipo='cartao',
                    entidade_id=card.id
                )
                db.session.add(notification)
        
        # Registrar histórico se houve mudanças
        if updates:
            history = CardHistory(
                cartao_id=card.id,
                usuario_id=user_id,
                tipo_alteracao='Edição',
                valor_novo='; '.join(updates)
            )
            db.session.add(history)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Cartão atualizado com sucesso',
            'card': card.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@kanban_bp.route('/kanban/cards/<int:card_id>/checklist', methods=['POST'])
@jwt_required()
def add_checklist_item(card_id):
    """Adicionar item ao checklist do cartão"""
    try:
        user_id = get_jwt_identity()
        card = KanbanCard.query.get(card_id)
        
        if not card or card.lista.quadro.criado_por != user_id:
            return jsonify({'error': 'Cartão não encontrado'}), 404
        
        data = request.get_json()
        if not data.get('descricao'):
            return jsonify({'error': 'Descrição do item é obrigatória'}), 400
        
        # Calcular próxima ordem
        max_ordem = db.session.query(db.func.max(ChecklistItem.ordem)).filter_by(cartao_id=card_id).scalar() or 0
        
        item = ChecklistItem(
            cartao_id=card_id,
            descricao=data['descricao'],
            ordem=max_ordem + 1
        )
        
        db.session.add(item)
        db.session.commit()
        
        return jsonify({
            'message': 'Item adicionado ao checklist',
            'item': item.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@kanban_bp.route('/kanban/cards/<int:card_id>', methods=['GET'])
@jwt_required()
def get_card_details(card_id):
    """Obter detalhes completos de um cartão"""
    try:
        user_id = get_jwt_identity()
        card = KanbanCard.query.get(card_id)
        
        if not card or card.lista.quadro.criado_por != user_id:
            return jsonify({'error': 'Cartão não encontrado'}), 404
        
        card_data = card.to_dict()
        card_data['checklists'] = [item.to_dict() for item in card.checklists]
        card_data['comentarios'] = [comment.to_dict() for comment in card.comentarios]
        card_data['anexos'] = [anexo.to_dict() for anexo in card.anexos]
        card_data['historico'] = [h.to_dict() for h in card.historico]
        
        return jsonify({'card': card_data})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 