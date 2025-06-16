from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc, asc, or_, and_
from src.extensions import db
from src.models.template import (
    Template, TemplateFavorito, TemplateCompartilhamento, 
    TemplateCategoria, TemplateCategory, TemplateVisibility
)
from src.models.user import User
from src.utils.logger import log_request, log_error
import re

bp = Blueprint('templates', __name__, url_prefix='/api/templates')

@bp.route('/health', methods=['GET'])
def health():
    """Health check para o sistema de templates"""
    try:
        template_count = Template.query.count()
        category_count = TemplateCategoria.query.count()
        
        return jsonify({
            'status': 'healthy',
            'service': 'templates',
            'total_templates': template_count,
            'total_categories': category_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('', methods=['GET'])
@jwt_required()
@log_request
def list_templates():
    """Lista templates com filtros avançados"""
    try:
        user_id = get_jwt_identity()
        
        # Parâmetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search', '').strip()
        categoria = request.args.get('categoria', '')
        visibilidade = request.args.get('visibilidade', '')
        ordenar_por = request.args.get('ordenar_por', 'created_at')
        ordem = request.args.get('ordem', 'desc')
        meus_templates = request.args.get('meus_templates', 'false').lower() == 'true'
        favoritos = request.args.get('favoritos', 'false').lower() == 'true'
        tags = request.args.get('tags', '').split(',') if request.args.get('tags') else []
        
        # Query base
        query = Template.query
        
        # Filtro de acesso: só mostrar templates acessíveis
        if meus_templates:
            query = query.filter(Template.user_id == user_id)
        else:
            # Templates públicos ou do usuário ou compartilhados
            access_filter = or_(
                Template.user_id == user_id,  # Seus templates
                Template.visibilidade == TemplateVisibility.PUBLIC,  # Públicos
                and_(
                    Template.visibilidade == TemplateVisibility.MARKETPLACE,
                    Template.aprovado == True
                ),  # Marketplace aprovados
                Template.id.in_(  # Compartilhados especificamente
                    db.session.query(TemplateCompartilhamento.template_id)
                    .filter(TemplateCompartilhamento.user_id == user_id)
                    .subquery()
                )
            )
            query = query.filter(access_filter)
        
        # Filtro de favoritos
        if favoritos:
            query = query.join(TemplateFavorito).filter(
                TemplateFavorito.user_id == user_id
            )
        
        # Filtro de busca
        if search:
            search_filter = or_(
                Template.titulo.ilike(f'%{search}%'),
                Template.descricao.ilike(f'%{search}%'),
                Template.conteudo.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)
        
        # Filtro de categoria
        if categoria:
            try:
                categoria_enum = TemplateCategory(categoria)
                query = query.filter(Template.categoria == categoria_enum)
            except ValueError:
                pass
        
        # Filtro de visibilidade
        if visibilidade:
            try:
                visibilidade_enum = TemplateVisibility(visibilidade)
                query = query.filter(Template.visibilidade == visibilidade_enum)
            except ValueError:
                pass
        
        # Filtro de tags
        if tags:
            for tag in tags:
                if tag.strip():
                    query = query.filter(Template.tags.contains([tag.strip()]))
        
        # Apenas templates ativos
        query = query.filter(Template.ativo == True)
        
        # Ordenação
        order_by_field = getattr(Template, ordenar_por, Template.created_at)
        if ordem == 'asc':
            query = query.order_by(asc(order_by_field))
        else:
            query = query.order_by(desc(order_by_field))
        
        # Paginação
        templates = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Converter para dict
        templates_data = [
            template.to_dict(user_id=user_id) 
            for template in templates.items
        ]
        
        return jsonify({
            'templates': templates_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': templates.total,
                'pages': templates.pages,
                'has_next': templates.has_next,
                'has_prev': templates.has_prev
            },
            'filters': {
                'search': search,
                'categoria': categoria,
                'visibilidade': visibilidade,
                'meus_templates': meus_templates,
                'favoritos': favoritos,
                'tags': tags
            }
        })
        
    except Exception as e:
        log_error(f"Erro ao listar templates: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('', methods=['POST'])
@jwt_required()
@log_request
def create_template():
    """Cria novo template"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validação
        if not data.get('titulo'):
            return jsonify({'error': 'Título é obrigatório'}), 400
        
        if not data.get('conteudo'):
            return jsonify({'error': 'Conteúdo é obrigatório'}), 400
        
        # Validar categoria
        categoria = TemplateCategory.OUTROS
        if data.get('categoria'):
            try:
                categoria = TemplateCategory(data['categoria'])
            except ValueError:
                return jsonify({'error': 'Categoria inválida'}), 400
        
        # Validar visibilidade
        visibilidade = TemplateVisibility.PRIVATE
        if data.get('visibilidade'):
            try:
                visibilidade = TemplateVisibility(data['visibilidade'])
            except ValueError:
                return jsonify({'error': 'Visibilidade inválida'}), 400
        
        # Processar tags
        tags = []
        if data.get('tags'):
            if isinstance(data['tags'], list):
                tags = [tag.strip() for tag in data['tags'] if tag.strip()]
            elif isinstance(data['tags'], str):
                tags = [tag.strip() for tag in data['tags'].split(',') if tag.strip()]
        
        # Processar variáveis
        variaveis = []
        if data.get('variaveis'):
            variaveis = data['variaveis'] if isinstance(data['variaveis'], list) else []
        
        # Criar template
        template = Template(
            titulo=data['titulo'],
            conteudo=data['conteudo'],
            user_id=user_id,
            categoria=categoria,
            descricao=data.get('descricao', ''),
            visibilidade=visibilidade,
            tags=tags,
            variaveis=variaveis,
            versao=data.get('versao', '1.0')
        )
        
        db.session.add(template)
        db.session.commit()
        
        current_app.logger.info(f"Template criado: {template.id} por usuário {user_id}")
        
        return jsonify({
            'message': 'Template criado com sucesso',
            'template': template.to_dict(user_id=user_id)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        log_error(f"Erro ao criar template: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('/<int:template_id>', methods=['GET'])
@jwt_required()
@log_request
def get_template(template_id):
    """Obtém template específico"""
    try:
        user_id = get_jwt_identity()
        
        template = Template.query.get_or_404(template_id)
        
        # Verificar permissão de acesso
        if not template.pode_acessar(user_id):
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Incrementar contador de uso
        template.incrementar_uso()
        
        return jsonify({
            'template': template.to_dict(user_id=user_id)
        })
        
    except Exception as e:
        log_error(f"Erro ao obter template {template_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('/<int:template_id>', methods=['PUT'])
@jwt_required()
@log_request
def update_template(template_id):
    """Atualiza template"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        template = Template.query.get_or_404(template_id)
        
        # Verificar permissão (só o criador pode editar)
        if template.user_id != user_id:
            # Verificar se tem permissão de edição via compartilhamento
            compartilhamento = TemplateCompartilhamento.query.filter_by(
                template_id=template_id,
                user_id=user_id,
                permissao='edicao'
            ).first()
            
            if not compartilhamento:
                return jsonify({'error': 'Acesso negado'}), 403
        
        # Atualizar campos
        if 'titulo' in data:
            template.titulo = data['titulo']
        
        if 'descricao' in data:
            template.descricao = data['descricao']
        
        if 'conteudo' in data:
            template.conteudo = data['conteudo']
        
        if 'categoria' in data:
            try:
                template.categoria = TemplateCategory(data['categoria'])
            except ValueError:
                return jsonify({'error': 'Categoria inválida'}), 400
        
        if 'visibilidade' in data:
            try:
                template.visibilidade = TemplateVisibility(data['visibilidade'])
            except ValueError:
                return jsonify({'error': 'Visibilidade inválida'}), 400
        
        if 'tags' in data:
            tags = []
            if isinstance(data['tags'], list):
                tags = [tag.strip() for tag in data['tags'] if tag.strip()]
            elif isinstance(data['tags'], str):
                tags = [tag.strip() for tag in data['tags'].split(',') if tag.strip()]
            template.tags = tags
        
        if 'variaveis' in data:
            template.variaveis = data['variaveis'] if isinstance(data['variaveis'], list) else []
        
        if 'versao' in data:
            template.versao = data['versao']
        
        db.session.commit()
        
        current_app.logger.info(f"Template {template_id} atualizado por usuário {user_id}")
        
        return jsonify({
            'message': 'Template atualizado com sucesso',
            'template': template.to_dict(user_id=user_id)
        })
        
    except Exception as e:
        db.session.rollback()
        log_error(f"Erro ao atualizar template {template_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('/<int:template_id>', methods=['DELETE'])
@jwt_required()
@log_request
def delete_template(template_id):
    """Deleta template"""
    try:
        user_id = get_jwt_identity()
        
        template = Template.query.get_or_404(template_id)
        
        # Verificar permissão (só o criador pode deletar)
        if template.user_id != user_id:
            return jsonify({'error': 'Acesso negado'}), 403
        
        db.session.delete(template)
        db.session.commit()
        
        current_app.logger.info(f"Template {template_id} deletado por usuário {user_id}")
        
        return jsonify({'message': 'Template deletado com sucesso'})
        
    except Exception as e:
        db.session.rollback()
        log_error(f"Erro ao deletar template {template_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('/<int:template_id>/favoritar', methods=['POST'])
@jwt_required()
@log_request
def toggle_favorite(template_id):
    """Adiciona/remove template dos favoritos"""
    try:
        user_id = get_jwt_identity()
        
        template = Template.query.get_or_404(template_id)
        
        # Verificar acesso
        if not template.pode_acessar(user_id):
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Verificar se já está favoritado
        favorito = TemplateFavorito.query.filter_by(
            template_id=template_id,
            user_id=user_id
        ).first()
        
        if favorito:
            # Remover dos favoritos
            db.session.delete(favorito)
            template.favoritos_count = max(0, template.favoritos_count - 1)
            is_favorited = False
            message = 'Template removido dos favoritos'
        else:
            # Adicionar aos favoritos
            favorito = TemplateFavorito(
                template_id=template_id,
                user_id=user_id
            )
            db.session.add(favorito)
            template.favoritos_count += 1
            is_favorited = True
            message = 'Template adicionado aos favoritos'
        
        db.session.commit()
        
        return jsonify({
            'message': message,
            'favoritado': is_favorited,
            'favoritos_count': template.favoritos_count
        })
        
    except Exception as e:
        db.session.rollback()
        log_error(f"Erro ao favoritar template {template_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('/<int:template_id>/compartilhar', methods=['POST'])
@jwt_required()
@log_request
def share_template(template_id):
    """Compartilha template com outros usuários"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        template = Template.query.get_or_404(template_id)
        
        # Verificar permissão (só o criador pode compartilhar)
        if template.user_id != user_id:
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Validar dados
        email_usuario = data.get('email')
        permissao = data.get('permissao', 'leitura')
        
        if not email_usuario:
            return jsonify({'error': 'Email do usuário é obrigatório'}), 400
        
        if permissao not in ['leitura', 'edicao']:
            return jsonify({'error': 'Permissão inválida'}), 400
        
        # Encontrar usuário
        usuario = User.query.filter_by(email=email_usuario).first()
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Verificar se já está compartilhado
        compartilhamento = TemplateCompartilhamento.query.filter_by(
            template_id=template_id,
            user_id=usuario.id
        ).first()
        
        if compartilhamento:
            # Atualizar permissão
            compartilhamento.permissao = permissao
            message = 'Permissões atualizadas'
        else:
            # Criar novo compartilhamento
            compartilhamento = TemplateCompartilhamento(
                template_id=template_id,
                user_id=usuario.id,
                compartilhado_por=user_id,
                permissao=permissao
            )
            db.session.add(compartilhamento)
            message = 'Template compartilhado com sucesso'
        
        db.session.commit()
        
        return jsonify({
            'message': message,
            'compartilhamento': {
                'usuario_email': usuario.email,
                'usuario_nome': usuario.nome,
                'permissao': permissao
            }
        })
        
    except Exception as e:
        db.session.rollback()
        log_error(f"Erro ao compartilhar template {template_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('/<int:template_id>/compartilhamentos', methods=['GET'])
@jwt_required()
@log_request
def list_template_shares(template_id):
    """Lista compartilhamentos do template"""
    try:
        user_id = get_jwt_identity()
        
        template = Template.query.get_or_404(template_id)
        
        # Verificar permissão (só o criador pode ver compartilhamentos)
        if template.user_id != user_id:
            return jsonify({'error': 'Acesso negado'}), 403
        
        compartilhamentos = TemplateCompartilhamento.query.filter_by(
            template_id=template_id
        ).all()
        
        compartilhamentos_data = []
        for comp in compartilhamentos:
            usuario = User.query.get(comp.user_id)
            compartilhamentos_data.append({
                'id': comp.id,
                'usuario_email': usuario.email,
                'usuario_nome': usuario.nome,
                'permissao': comp.permissao,
                'created_at': comp.created_at.isoformat()
            })
        
        return jsonify({
            'compartilhamentos': compartilhamentos_data
        })
        
    except Exception as e:
        log_error(f"Erro ao listar compartilhamentos do template {template_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('/categorias', methods=['GET'])
@log_request
def list_categories():
    """Lista categorias de templates"""
    try:
        # Categorias padrão do enum
        categorias_enum = [
            {
                'value': cat.value,
                'name': cat.name,
                'label': cat.value.replace('_', ' ').title()
            }
            for cat in TemplateCategory
        ]
        
        # Categorias customizadas do banco
        categorias_custom = TemplateCategoria.query.filter_by(ativo=True).order_by(
            TemplateCategoria.ordem
        ).all()
        
        categorias_custom_data = [cat.to_dict() for cat in categorias_custom]
        
        return jsonify({
            'categorias_padrao': categorias_enum,
            'categorias_customizadas': categorias_custom_data
        })
        
    except Exception as e:
        log_error(f"Erro ao listar categorias: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('/marketplace', methods=['GET'])
@log_request
def marketplace():
    """Lista templates do marketplace público"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)
        search = request.args.get('search', '').strip()
        categoria = request.args.get('categoria', '')
        
        # Query base para marketplace
        query = Template.query.filter(
            Template.visibilidade == TemplateVisibility.MARKETPLACE,
            Template.aprovado == True,
            Template.ativo == True
        )
        
        # Filtros
        if search:
            search_filter = or_(
                Template.titulo.ilike(f'%{search}%'),
                Template.descricao.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)
        
        if categoria:
            try:
                categoria_enum = TemplateCategory(categoria)
                query = query.filter(Template.categoria == categoria_enum)
            except ValueError:
                pass
        
        # Ordenar por popularidade (uso + favoritos)
        query = query.order_by(
            desc(Template.uso_count + Template.favoritos_count)
        )
        
        # Paginação
        templates = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Converter para dict (sem user_id para marketplace público)
        templates_data = [
            template.to_dict() 
            for template in templates.items
        ]
        
        return jsonify({
            'templates': templates_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': templates.total,
                'pages': templates.pages,
                'has_next': templates.has_next,
                'has_prev': templates.has_prev
            }
        })
        
    except Exception as e:
        log_error(f"Erro ao listar marketplace: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
