from src.extensions import db
from datetime import datetime

class Publication(db.Model):
    __tablename__ = 'publications'
    
    id = db.Column(db.Integer, primary_key=True)
    processo_id = db.Column(db.Integer, db.ForeignKey('processes.id'), nullable=False)
    tribunal = db.Column(db.String(50), nullable=False)
    data_publicacao = db.Column(db.Date, nullable=False)
    texto = db.Column(db.Text, nullable=False)
    texto_ocr = db.Column(db.Text)  # Texto extraído por OCR
    status_leitura = db.Column(db.Enum('Não Lida', 'Lida', 'Processada', name='reading_status'), default='Não Lida')
    data_captura = db.Column(db.DateTime, default=datetime.utcnow)
    tipo_andamento = db.Column(db.String(100))  # Tipo identificado pelo parser
    prazo_identificado = db.Column(db.Integer)  # Prazo em dias
    termo_inicial = db.Column(db.Date)  # Data inicial do prazo
    url_original = db.Column(db.String(500))  # URL da publicação original
    hash_content = db.Column(db.String(64))  # Hash do conteúdo para evitar duplicatas
    
    # Campos para controle de automação
    processamento_automatico = db.Column(db.Boolean, default=True)
    tarefa_gerada = db.Column(db.Boolean, default=False)
    tarefa_id = db.Column(db.Integer, db.ForeignKey('kanban_cards.id'), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'processo_id': self.processo_id,
            'processo_numero': self.processo.numero if self.processo else None,
            'tribunal': self.tribunal,
            'data_publicacao': self.data_publicacao.isoformat() if self.data_publicacao else None,
            'texto': self.texto,
            'texto_ocr': self.texto_ocr,
            'status_leitura': self.status_leitura,
            'data_captura': self.data_captura.isoformat() if self.data_captura else None,
            'tipo_andamento': self.tipo_andamento,
            'prazo_identificado': self.prazo_identificado,
            'termo_inicial': self.termo_inicial.isoformat() if self.termo_inicial else None,
            'url_original': self.url_original,
            'processamento_automatico': self.processamento_automatico,
            'tarefa_gerada': self.tarefa_gerada,
            'tarefa_id': self.tarefa_id
        } 