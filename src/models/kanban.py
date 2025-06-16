from src.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Index, CheckConstraint
import json

class KanbanBoard(db.Model):
    __tablename__ = 'kanban_boards'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Proprietário e equipe
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    team_ids = db.Column(db.JSON)  # Lista de IDs dos membros da equipe
    
    # Configurações
    is_public = db.Column(db.Boolean, default=False)
    is_template = db.Column(db.Boolean, default=False)
    template_category = db.Column(db.String(50))  # 'litigation', 'contracts', 'corporate', etc.
    
    # Personalização
    background_color = db.Column(db.String(7), default='#1890ff')
    background_image = db.Column(db.Text)  # URL da imagem de fundo
    
    # Configurações avançadas
    settings = db.Column(db.JSON, default=lambda: {
        'allow_comments': True,
        'allow_attachments': True,
        'auto_archive_completed': False,
        'email_notifications': True,
        'due_date_reminders': True,
        'time_tracking': False
    })
    
    # Metadados
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    archived_at = db.Column(db.DateTime)
    
    # Relacionamentos
    owner = db.relationship('User', backref='owned_boards')
    lists = db.relationship('KanbanList', backref='board', cascade='all, delete-orphan', order_by='KanbanList.position')
    
    def to_dict(self, include_lists=True):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'owner_id': self.owner_id,
            'owner': {
                'id': self.owner.id,
                'name': self.owner.nome,
                'email': self.owner.email
            } if self.owner else None,
            'team_ids': self.team_ids or [],
            'is_public': self.is_public,
            'is_template': self.is_template,
            'template_category': self.template_category,
            'background_color': self.background_color,
            'background_image': self.background_image,
            'settings': self.settings,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'archived_at': self.archived_at.isoformat() if self.archived_at else None,
            'lists': [lst.to_dict() for lst in self.lists] if include_lists and self.lists else []
        }


class KanbanList(db.Model):
    __tablename__ = 'kanban_lists'
    
    id = db.Column(db.Integer, primary_key=True)
    board_id = db.Column(db.Integer, db.ForeignKey('kanban_boards.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    
    # Configurações da lista
    color = db.Column(db.String(7), default='#f0f0f0')
    is_collapsed = db.Column(db.Boolean, default=False)
    limit_cards = db.Column(db.Integer)  # Limite WIP (Work in Progress)
    
    # Automação
    auto_actions = db.Column(db.JSON, default=lambda: {
        'move_completed_to': None,  # ID da lista para mover cards completos
        'auto_assign': None,  # ID do usuário para auto-atribuição
        'due_date_offset': None  # Dias para adicionar à data de vencimento
    })
    
    # Metadados
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    cards = db.relationship('KanbanCard', backref='list', cascade='all, delete-orphan', order_by='KanbanCard.position')
    
    def to_dict(self, include_cards=True):
        return {
            'id': self.id,
            'board_id': self.board_id,
            'title': self.title,
            'position': self.position,
            'color': self.color,
            'is_collapsed': self.is_collapsed,
            'limit_cards': self.limit_cards,
            'auto_actions': self.auto_actions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'cards': [card.to_dict() for card in self.cards] if include_cards and self.cards else [],
            'card_count': len(self.cards) if self.cards else 0
        }


class KanbanCard(db.Model):
    __tablename__ = 'kanban_cards'
    
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('kanban_lists.id'), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    position = db.Column(db.Integer, nullable=False)
    
    # Assignees
    assigned_to = db.Column(db.JSON)  # Lista de IDs dos usuários atribuídos
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Prioridade e status
    priority = db.Column(db.Enum('low', 'medium', 'high', 'urgent', name='card_priority'), default='medium')
    status = db.Column(db.Enum('active', 'completed', 'archived', name='card_status'), default='active')
    
    # Datas
    due_date = db.Column(db.DateTime)
    start_date = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Metadados jurídicos
    case_number = db.Column(db.String(100))  # Número do processo
    client_name = db.Column(db.String(200))  # Nome do cliente
    matter_type = db.Column(db.String(100))  # Tipo de questão jurídica
    court = db.Column(db.String(200))  # Tribunal
    
    # Labels e tags
    labels = db.Column(db.JSON)  # Lista de labels {id, name, color}
    tags = db.Column(db.JSON)   # Lista de tags livres
    
    # Estimativas e tracking
    estimated_hours = db.Column(db.Float)
    spent_hours = db.Column(db.Float, default=0)
    billable_hours = db.Column(db.Float, default=0)
    
    # Checklist
    checklist = db.Column(db.JSON)  # Lista de itens {id, text, checked, assignee}
    
    # Anexos e referências
    attachments = db.Column(db.JSON)  # Lista de anexos {id, name, url, type, size}
    linked_documents = db.Column(db.JSON)  # IDs de documentos linkados
    
    # Metadados
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    creator = db.relationship('User', backref='created_cards')
    comments = db.relationship('KanbanComment', backref='card', cascade='all, delete-orphan', order_by='KanbanComment.created_at')
    time_entries = db.relationship('KanbanTimeEntry', backref='card', cascade='all, delete-orphan')
    
    def to_dict(self, include_details=True):
        return {
            'id': self.id,
            'list_id': self.list_id,
            'title': self.title,
            'description': self.description,
            'position': self.position,
            'assigned_to': self.assigned_to or [],
            'created_by': self.created_by,
            'creator': {
                'id': self.creator.id,
                'name': self.creator.nome,
                'email': self.creator.email
            } if self.creator else None,
            'priority': self.priority,
            'status': self.status,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'case_number': self.case_number,
            'client_name': self.client_name,
            'matter_type': self.matter_type,
            'court': self.court,
            'labels': self.labels or [],
            'tags': self.tags or [],
            'estimated_hours': self.estimated_hours,
            'spent_hours': self.spent_hours,
            'billable_hours': self.billable_hours,
            'checklist': self.checklist or [],
            'attachments': self.attachments or [],
            'linked_documents': self.linked_documents or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'comments': [comment.to_dict() for comment in self.comments] if include_details and self.comments else [],
            'comment_count': len(self.comments) if self.comments else 0,
            'time_entries': [entry.to_dict() for entry in self.time_entries] if include_details and self.time_entries else []
        }
    
    def is_overdue(self):
        """Verifica se o card está atrasado"""
        if not self.due_date or self.status == 'completed':
            return False
        return datetime.utcnow() > self.due_date
    
    def completion_percentage(self):
        """Calcula porcentagem de conclusão baseada no checklist"""
        if not self.checklist:
            return 0
        
        completed_items = sum(1 for item in self.checklist if item.get('checked', False))
        total_items = len(self.checklist)
        
        return (completed_items / total_items) * 100 if total_items > 0 else 0


class KanbanComment(db.Model):
    __tablename__ = 'kanban_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('kanban_cards.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    # Tipo de comentário
    comment_type = db.Column(db.Enum('comment', 'activity', 'system', name='comment_type'), default='comment')
    
    # Menções
    mentions = db.Column(db.JSON)  # Lista de IDs de usuários mencionados
    
    # Metadados
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    edited_at = db.Column(db.DateTime)
    
    # Relacionamentos
    author = db.relationship('User', backref='kanban_comments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'card_id': self.card_id,
            'author_id': self.author_id,
            'author': {
                'id': self.author.id,
                'name': self.author.nome,
                'email': self.author.email
            } if self.author else None,
            'content': self.content,
            'comment_type': self.comment_type,
            'mentions': self.mentions or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'edited_at': self.edited_at.isoformat() if self.edited_at else None
        }


class KanbanTimeEntry(db.Model):
    __tablename__ = 'kanban_time_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('kanban_cards.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Tempo
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer)  # Duração em minutos
    
    # Detalhes
    description = db.Column(db.Text)
    is_billable = db.Column(db.Boolean, default=True)
    hourly_rate = db.Column(db.Float)  # Taxa por hora
    
    # Status
    is_running = db.Column(db.Boolean, default=False)  # Timer ativo
    
    # Metadados
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    user = db.relationship('User', backref='time_entries')
    
    def to_dict(self):
        return {
            'id': self.id,
            'card_id': self.card_id,
            'user_id': self.user_id,
            'user': {
                'id': self.user.id,
                'name': self.user.nome,
                'email': self.user.email
            } if self.user else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_minutes': self.duration_minutes,
            'description': self.description,
            'is_billable': self.is_billable,
            'hourly_rate': self.hourly_rate,
            'is_running': self.is_running,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def calculate_duration(self):
        """Calcula duração em minutos"""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return 0
    
    def calculate_cost(self):
        """Calcula custo baseado na duração e taxa"""
        if self.duration_minutes and self.hourly_rate and self.is_billable:
            hours = self.duration_minutes / 60
            return hours * self.hourly_rate
        return 0


class KanbanLabel(db.Model):
    __tablename__ = 'kanban_labels'
    
    id = db.Column(db.Integer, primary_key=True)
    board_id = db.Column(db.Integer, db.ForeignKey('kanban_boards.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(7), nullable=False)
    description = db.Column(db.Text)
    
    # Metadados
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    board = db.relationship('KanbanBoard', backref='labels')
    
    def to_dict(self):
        return {
            'id': self.id,
            'board_id': self.board_id,
            'name': self.name,
            'color': self.color,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class KanbanActivity(db.Model):
    __tablename__ = 'kanban_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    board_id = db.Column(db.Integer, db.ForeignKey('kanban_boards.id'), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('kanban_cards.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Atividade
    action = db.Column(db.String(50), nullable=False)  # 'created', 'moved', 'updated', 'commented', etc.
    entity_type = db.Column(db.String(20), nullable=False)  # 'board', 'list', 'card', 'comment'
    entity_id = db.Column(db.Integer)
    
    # Detalhes da mudança
    old_value = db.Column(db.JSON)
    new_value = db.Column(db.JSON)
    description = db.Column(db.Text)
    
    # Metadados
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    board = db.relationship('KanbanBoard', backref='activities')
    card = db.relationship('KanbanCard', backref='activities')
    user = db.relationship('User', backref='kanban_activities')
    
    def to_dict(self):
        return {
            'id': self.id,
            'board_id': self.board_id,
            'card_id': self.card_id,
            'user_id': self.user_id,
            'user': {
                'id': self.user.id,
                'name': self.user.nome,
                'email': self.user.email
            } if self.user else None,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# Índices para performance
Index('idx_kanban_board_owner', KanbanBoard.owner_id)
Index('idx_kanban_list_board_position', KanbanList.board_id, KanbanList.position)
Index('idx_kanban_card_list_position', KanbanCard.list_id, KanbanCard.position)
Index('idx_kanban_card_assigned', KanbanCard.assigned_to)
Index('idx_kanban_card_due_date', KanbanCard.due_date)
Index('idx_kanban_activity_board_created', KanbanActivity.board_id, KanbanActivity.created_at)
Index('idx_kanban_time_entry_card_user', KanbanTimeEntry.card_id, KanbanTimeEntry.user_id) 