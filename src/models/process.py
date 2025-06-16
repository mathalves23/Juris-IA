from src.extensions import db
from datetime import datetime
from sqlalchemy.types import DECIMAL

class Process(db.Model):
    __tablename__ = 'processes'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(25), unique=True, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    tribunal = db.Column(db.String(50), nullable=False)
    vara = db.Column(db.String(100))
    comarca = db.Column(db.String(100))
    area = db.Column(db.String(50), nullable=False)
    valor_causa = db.Column(DECIMAL(15, 2))
    data_distribuicao = db.Column(db.Date)
    status = db.Column(db.Enum('Ativo', 'Arquivado', 'Encerrado', name='process_status'), default='Ativo')
    parte_contraria = db.Column(db.String(100))
    descricao = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'numero': self.numero,
            'cliente_id': self.cliente_id,
            'tribunal': self.tribunal,
            'vara': self.vara,
            'comarca': self.comarca,
            'area': self.area,
            'valor_causa': float(self.valor_causa) if self.valor_causa else None,
            'data_distribuicao': self.data_distribuicao.isoformat() if self.data_distribuicao else None,
            'status': self.status,
            'parte_contraria': self.parte_contraria,
            'descricao': self.descricao,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'usuario_id': self.usuario_id
        } 