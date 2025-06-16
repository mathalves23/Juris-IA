from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc, asc, or_, and_
from src.extensions import db
from src.models.document import (
    Document, DocumentColaborador, DocumentComentario, 
    DocumentHistorico, DocumentStatus, DocumentType, PermissionType
)
from src.models.template import Template
from src.models.user import User
from src.utils.logger import log_request, log_error
import json

bp = Blueprint('documents', __name__, url_prefix='/api/documents')

@bp.route('/health', methods=['GET'])
def health():
    """Health check para o sistema de documentos"""
    try:
        document_count = Document.query.count()
        collaboration_count = DocumentColaborador.query.count()
        
        return jsonify({
            'status': 'healthy',
            'service': 'documents',
            'total_documents': document_count,
            'total_collaborations': collaboration_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('', methods=['GET'])
@jwt_required()
@log_request
def list_documents():
    """Lista documentos com filtros avançados"""
    try:
        user_id = get_jwt_identity()
        
        # Parâmetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '')
        tipo = request.args.get('tipo', '')
        ordenar_por = request.args.get('ordenar_por', 'updated_at')
        ordem = request.args.get('ordem', 'desc')
        meus_documentos = request.args.get('meus_documentos', 'false').lower() == 'true'
        colaborativos = request.args.get('colaborativos', 'false').lower() == 'true'
        template_id = request.args.get('template_id', type=int)
        
        # Query base
        query = Document.query
        
        # Filtro de acesso
        if meus_documentos:
            query = query.filter(Document.user_id == user_id)
        elif colaborativos:
            # Documentos onde o usuário é colaborador
            query = query.join(DocumentColaborador).filter(
                DocumentColaborador.user_id == user_id
            )
        else:
            # Documentos próprios, colaborativos ou públicos
            access_filter = or_(
                Document.user_id == user_id,  # Próprios
                Document.publico == True,     # Públicos
                Document.id.in_(              # Colaborativos
                    db.session.query(DocumentColaborador.document_id)
                    .filter(DocumentColaborador.user_id == user_id)
                    .subquery()
                )
            )
            query = query.filter(access_filter)
        
        # Filtros adicionais
        if search:
            search_filter = or_(
                Document.titulo.ilike(f'%{search}%'),
                Document.descricao.ilike(f'%{search}%'),
                Document.conteudo.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)
        
        if status:
            try:
                status_enum = DocumentStatus(status)
                query = query.filter(Document.status == status_enum)
            except ValueError:
                pass
        
        if tipo:
            try:
                tipo_enum = DocumentType(tipo)
                query = query.filter(Document.tipo == tipo_enum)
            except ValueError:
                pass
        
        if template_id:
            query = query.filter(Document.template_id == template_id)
        
        # Ordenação
        order_by_field = getattr(Document, ordenar_por, Document.updated_at)
        if ordem == 'asc':
            query = query.order_by(asc(order_by_field))
        else:
            query = query.order_by(desc(order_by_field))
        
        # Paginação
        documents = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Converter para dict
        documents_data = [
            doc.to_dict(user_id=user_id, incluir_conteudo=False) 
            for doc in documents.items
        ]
        
        return jsonify({
            'documents': documents_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': documents.total,
                'pages': documents.pages,
                'has_next': documents.has_next,
                'has_prev': documents.has_prev
            },
            'filters': {
                'search': search,
                'status': status,
                'tipo': tipo,
                'meus_documentos': meus_documentos,
                'colaborativos': colaborativos,
                'template_id': template_id
            }
        })
        
    except Exception as e:
        log_error(f"Erro ao listar documentos: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('', methods=['POST'])
@jwt_required()
@log_request
def create_document():
    """Cria novo documento"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validação
        if not data.get('titulo'):
            return jsonify({'error': 'Título é obrigatório'}), 400
        
        if not data.get('conteudo'):
            return jsonify({'error': 'Conteúdo é obrigatório'}), 400
        
        # Validar tipo
        tipo = DocumentType.RICH_TEXT
        if data.get('tipo'):
            try:
                tipo = DocumentType(data['tipo'])
            except ValueError:
                return jsonify({'error': 'Tipo inválido'}), 400
        
        # Validar status
        status = DocumentStatus.RASCUNHO
        if data.get('status'):
            try:
                status = DocumentStatus(data['status'])
            except ValueError:
                return jsonify({'error': 'Status inválido'}), 400
        
        # Processar tags
        tags = []
        if data.get('tags'):
            if isinstance(data['tags'], list):
                tags = [tag.strip() for tag in data['tags'] if tag.strip()]
            elif isinstance(data['tags'], str):
                tags = [tag.strip() for tag in data['tags'].split(',') if tag.strip()]
        
        # Criar documento
        document = Document(
            titulo=data['titulo'],
            conteudo=data['conteudo'],
            user_id=user_id,
            descricao=data.get('descricao', ''),
            tipo=tipo,
            status=status,
            template_id=data.get('template_id'),
            colaborativo=data.get('colaborativo', False),
            publico=data.get('publico', False),
            tags=tags,
            conteudo_delta=data.get('conteudo_delta')
        )
        
        db.session.add(document)
        db.session.commit()
        
        current_app.logger.info(f"Documento criado: {document.id} por usuário {user_id}")
        
        return jsonify({
            'message': 'Documento criado com sucesso',
            'document': document.to_dict(user_id=user_id)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        log_error(f"Erro ao criar documento: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('/<int:document_id>', methods=['GET'])
@jwt_required()
@log_request
def get_document(document_id):
    """Obtém documento específico"""
    try:
        user_id = get_jwt_identity()
        
        document = Document.query.get_or_404(document_id)
        
        # Verificar permissão de acesso
        if not document.pode_acessar(user_id):
            return jsonify({'error': 'Acesso negado'}), 403
        
        return jsonify({
            'document': document.to_dict(user_id=user_id)
        })
        
    except Exception as e:
        log_error(f"Erro ao obter documento {document_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('/<int:document_id>', methods=['PUT'])
@jwt_required()
@log_request
def update_document(document_id):
    """Atualiza documento"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        document = Document.query.get_or_404(document_id)
        
        # Verificar permissão de edição
        if not document.pode_editar(user_id):
            return jsonify({'error': 'Acesso negado para edição'}), 403
        
        # Verificar se está bloqueado para edição por outro usuário
        if document.bloqueado_para_edicao and document.bloqueado_por_user_id != user_id:
            bloqueado_por = User.query.get(document.bloqueado_por_user_id)
            return jsonify({
                'error': f'Documento está sendo editado por {bloqueado_por.nome if bloqueado_por else "outro usuário"}'
            }), 423  # Locked
        
        # Salvar conteúdo anterior para histórico
        conteudo_anterior = document.conteudo
        
        # Atualizar campos
        if 'titulo' in data:
            document.titulo = data['titulo']
        
        if 'descricao' in data:
            document.descricao = data['descricao']
        
        if 'conteudo' in data:
            document.conteudo = data['conteudo']
        
        if 'conteudo_delta' in data:
            document.conteudo_delta = data['conteudo_delta']
        
        if 'status' in data:
            try:
                document.status = DocumentStatus(data['status'])
            except ValueError:
                return jsonify({'error': 'Status inválido'}), 400
        
        if 'tipo' in data:
            try:
                document.tipo = DocumentType(data['tipo'])
            except ValueError:
                return jsonify({'error': 'Tipo inválido'}), 400
        
        if 'tags' in data:
            tags = []
            if isinstance(data['tags'], list):
                tags = [tag.strip() for tag in data['tags'] if tag.strip()]
            elif isinstance(data['tags'], str):
                tags = [tag.strip() for tag in data['tags'].split(',') if tag.strip()]
            document.tags = tags
        
        if 'colaborativo' in data:
            document.colaborativo = data['colaborativo']
        
        if 'publico' in data:
            document.publico = data['publico']
        
        # Criar nova versão se o conteúdo mudou significativamente
        if 'conteudo' in data and data['conteudo'] != conteudo_anterior:
            document.criar_nova_versao(
                user_id=user_id,
                conteudo_novo=data['conteudo'],
                comentario=data.get('comentario_versao', 'Edição do documento')
            )
        
        db.session.commit()
        
        current_app.logger.info(f"Documento {document_id} atualizado por usuário {user_id}")
        
        return jsonify({
            'message': 'Documento atualizado com sucesso',
            'document': document.to_dict(user_id=user_id)
        })
        
    except Exception as e:
        db.session.rollback()
        log_error(f"Erro ao atualizar documento {document_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('/<int:document_id>', methods=['DELETE'])
@jwt_required()
@log_request
def delete_document(document_id):
    """Deleta documento"""
    try:
        user_id = get_jwt_identity()
        
        document = Document.query.get_or_404(document_id)
        
        # Verificar permissão (só o criador pode deletar)
        if document.user_id != user_id:
            return jsonify({'error': 'Acesso negado'}), 403
        
        db.session.delete(document)
        db.session.commit()
        
        current_app.logger.info(f"Documento {document_id} deletado por usuário {user_id}")
        
        return jsonify({'message': 'Documento deletado com sucesso'})
        
    except Exception as e:
        db.session.rollback()
        log_error(f"Erro ao deletar documento {document_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('/<int:document_id>/bloquear', methods=['POST'])
@jwt_required()
@log_request
def lock_document(document_id):
    """Bloqueia documento para edição"""
    try:
        user_id = get_jwt_identity()
        
        document = Document.query.get_or_404(document_id)
        
        if document.bloquear_para_edicao(user_id):
            return jsonify({
                'message': 'Documento bloqueado para edição',
                'bloqueado_por': user_id
            })
        else:
            return jsonify({'error': 'Não foi possível bloquear o documento'}), 403
        
    except Exception as e:
        log_error(f"Erro ao bloquear documento {document_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('/<int:document_id>/desbloquear', methods=['POST'])
@jwt_required()
@log_request
def unlock_document(document_id):
    """Desbloqueia documento para edição"""
    try:
        user_id = get_jwt_identity()
        
        document = Document.query.get_or_404(document_id)
        
        if document.desbloquear_edicao(user_id):
            return jsonify({'message': 'Documento desbloqueado para edição'})
        else:
            return jsonify({'error': 'Não foi possível desbloquear o documento'}), 403
        
    except Exception as e:
        log_error(f"Erro ao desbloquear documento {document_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('/<int:document_id>/colaboradores', methods=['GET'])
@jwt_required()
@log_request
def list_collaborators(document_id):
    """Lista colaboradores do documento"""
    try:
        user_id = get_jwt_identity()
        
        document = Document.query.get_or_404(document_id)
        
        # Verificar permissão
        if not document.pode_acessar(user_id):
            return jsonify({'error': 'Acesso negado'}), 403
        
        colaboradores = DocumentColaborador.query.filter_by(
            document_id=document_id
        ).all()
        
        colaboradores_data = []
        for colab in colaboradores:
            usuario = User.query.get(colab.user_id)
            colaboradores_data.append({
                'id': colab.id,
                'usuario_id': colab.user_id,
                'usuario_nome': usuario.nome if usuario else None,
                'usuario_email': usuario.email if usuario else None,
                'permissao': colab.permissao.value,
                'created_at': colab.created_at.isoformat()
            })
        
        return jsonify({
            'colaboradores': colaboradores_data
        })
        
    except Exception as e:
        log_error(f"Erro ao listar colaboradores do documento {document_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('/<int:document_id>/colaboradores', methods=['POST'])
@jwt_required()
@log_request
def add_collaborator(document_id):
    """Adiciona colaborador ao documento"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        document = Document.query.get_or_404(document_id)
        
        # Verificar permissão (só o criador ou admin pode adicionar colaboradores)
        if document.user_id != user_id:
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Validar dados
        email_usuario = data.get('email')
        permissao = data.get('permissao', 'leitura')
        
        if not email_usuario:
            return jsonify({'error': 'Email do usuário é obrigatório'}), 400
        
        try:
            permissao_enum = PermissionType(permissao)
        except ValueError:
            return jsonify({'error': 'Permissão inválida'}), 400
        
        # Encontrar usuário
        usuario = User.query.filter_by(email=email_usuario).first()
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Verificar se já é colaborador
        colaborador_existente = DocumentColaborador.query.filter_by(
            document_id=document_id,
            user_id=usuario.id
        ).first()
        
        if colaborador_existente:
            # Atualizar permissão
            colaborador_existente.permissao = permissao_enum
            message = 'Permissões do colaborador atualizadas'
        else:
            # Criar novo colaborador
            colaborador = DocumentColaborador(
                document_id=document_id,
                user_id=usuario.id,
                permissao=permissao_enum,
                convidado_por=user_id
            )
            db.session.add(colaborador)
            message = 'Colaborador adicionado com sucesso'
        
        db.session.commit()
        
        return jsonify({
            'message': message,
            'colaborador': {
                'usuario_email': usuario.email,
                'usuario_nome': usuario.nome,
                'permissao': permissao
            }
        })
        
    except Exception as e:
        db.session.rollback()
        log_error(f"Erro ao adicionar colaborador ao documento {document_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('/<int:document_id>/comentarios', methods=['GET'])
@jwt_required()
@log_request
def list_comments(document_id):
    """Lista comentários do documento"""
    try:
        user_id = get_jwt_identity()
        
        document = Document.query.get_or_404(document_id)
        
        # Verificar permissão
        if not document.pode_acessar(user_id):
            return jsonify({'error': 'Acesso negado'}), 403
        
        comentarios = DocumentComentario.query.filter_by(
            document_id=document_id,
            comentario_pai_id=None  # Apenas comentários principais
        ).order_by(DocumentComentario.created_at.desc()).all()
        
        comentarios_data = []
        for comentario in comentarios:
            usuario = User.query.get(comentario.user_id)
            
            # Buscar respostas
            respostas = DocumentComentario.query.filter_by(
                comentario_pai_id=comentario.id
            ).order_by(DocumentComentario.created_at.asc()).all()
            
            respostas_data = []
            for resposta in respostas:
                usuario_resposta = User.query.get(resposta.user_id)
                respostas_data.append({
                    'id': resposta.id,
                    'comentario': resposta.comentario,
                    'usuario_nome': usuario_resposta.nome if usuario_resposta else None,
                    'created_at': resposta.created_at.isoformat(),
                    'updated_at': resposta.updated_at.isoformat()
                })
            
            comentarios_data.append({
                'id': comentario.id,
                'comentario': comentario.comentario,
                'posicao_inicio': comentario.posicao_inicio,
                'posicao_fim': comentario.posicao_fim,
                'resolvido': comentario.resolvido,
                'usuario_nome': usuario.nome if usuario else None,
                'created_at': comentario.created_at.isoformat(),
                'updated_at': comentario.updated_at.isoformat(),
                'respostas': respostas_data
            })
        
        return jsonify({
            'comentarios': comentarios_data
        })
        
    except Exception as e:
        log_error(f"Erro ao listar comentários do documento {document_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('/<int:document_id>/comentarios', methods=['POST'])
@jwt_required()
@log_request
def add_comment(document_id):
    """Adiciona comentário ao documento"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        document = Document.query.get_or_404(document_id)
        
        # Verificar permissão
        if not document.pode_acessar(user_id):
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Validar dados
        comentario_texto = data.get('comentario')
        if not comentario_texto:
            return jsonify({'error': 'Comentário é obrigatório'}), 400
        
        # Criar comentário
        comentario = DocumentComentario(
            document_id=document_id,
            user_id=user_id,
            comentario=comentario_texto,
            posicao_inicio=data.get('posicao_inicio'),
            posicao_fim=data.get('posicao_fim'),
            comentario_pai_id=data.get('comentario_pai_id')
        )
        
        db.session.add(comentario)
        db.session.commit()
        
        return jsonify({
            'message': 'Comentário adicionado com sucesso',
            'comentario': {
                'id': comentario.id,
                'comentario': comentario.comentario,
                'created_at': comentario.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        log_error(f"Erro ao adicionar comentário ao documento {document_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('/<int:document_id>/historico', methods=['GET'])
@jwt_required()
@log_request
def get_history(document_id):
    """Obtém histórico de versões do documento"""
    try:
        user_id = get_jwt_identity()
        
        document = Document.query.get_or_404(document_id)
        
        # Verificar permissão
        if not document.pode_acessar(user_id):
            return jsonify({'error': 'Acesso negado'}), 403
        
        limit = min(request.args.get('limit', 50, type=int), 100)
        
        historico = DocumentHistorico.query.filter_by(
            document_id=document_id
        ).order_by(DocumentHistorico.created_at.desc()).limit(limit).all()
        
        historico_data = []
        for item in historico:
            usuario = User.query.get(item.user_id)
            historico_data.append({
                'id': item.id,
                'versao_anterior': item.versao_anterior,
                'comentario': item.comentario,
                'tipo_mudanca': item.tipo_mudanca,
                'usuario_nome': usuario.nome if usuario else None,
                'created_at': item.created_at.isoformat(),
                'tem_conteudo': bool(item.conteudo_anterior and item.conteudo_novo)
            })
        
        return jsonify({
            'historico': historico_data
        })
        
    except Exception as e:
        log_error(f"Erro ao obter histórico do documento {document_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('/criar-de-template/<int:template_id>', methods=['POST'])
@jwt_required()
@log_request
def create_from_template(template_id):
    """Cria documento a partir de template"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        template = Template.query.get_or_404(template_id)
        
        # Verificar acesso ao template
        if not template.pode_acessar(user_id):
            return jsonify({'error': 'Acesso negado ao template'}), 403
        
        # Validação
        if not data.get('titulo'):
            return jsonify({'error': 'Título é obrigatório'}), 400
        
        # Processar conteúdo do template (substituir variáveis se fornecidas)
        conteudo = template.conteudo
        variaveis = data.get('variaveis', {})
        
        if variaveis and isinstance(variaveis, dict):
            for variavel, valor in variaveis.items():
                conteudo = conteudo.replace(f'{{{{{variavel}}}}}', str(valor))
        
        # Criar documento
        document = Document(
            titulo=data['titulo'],
            conteudo=conteudo,
            user_id=user_id,
            template_id=template_id,
            descricao=data.get('descricao', ''),
            tipo=DocumentType.RICH_TEXT,
            status=DocumentStatus.RASCUNHO
        )
        
        db.session.add(document)
        
        # Incrementar uso do template
        template.incrementar_uso()
        
        db.session.commit()
        
        current_app.logger.info(f"Documento criado do template {template_id} por usuário {user_id}")
        
        return jsonify({
            'message': 'Documento criado a partir do template',
            'document': document.to_dict(user_id=user_id)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        log_error(f"Erro ao criar documento do template {template_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
