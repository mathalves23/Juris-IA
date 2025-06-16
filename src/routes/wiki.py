from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from src.extensions import db
from src.models.wiki import Wiki, WikiTag
from src.models.notification import Notification
from datetime import datetime
from services.wiki_service import wiki_service
import logging

logger = logging.getLogger(__name__)

wiki_bp = Blueprint('wiki', __name__)

@wiki_bp.route('/wiki', methods=['GET'])
@jwt_required()
def get_wiki_items():
    """Listar itens da wiki com busca e filtros"""
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        search = request.args.get('search', '')
        categoria = request.args.get('categoria', '')
        status = request.args.get('status', 'Publicado')
        
        query = Wiki.query.filter_by(status=status)
        
        if search:
            query = query.filter(
                db.or_(
                    Wiki.titulo.contains(search),
                    Wiki.texto.contains(search)
                )
            )
        
        if categoria:
            query = query.filter(Wiki.categoria == categoria)
        
        # Ordenar por data de criação (mais recente primeiro)
        query = query.order_by(Wiki.data_criacao.desc())
        
        items = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Obter categorias únicas para filtros
        categorias = db.session.query(Wiki.categoria).distinct().all()
        categorias = [cat[0] for cat in categorias]
        
        return jsonify({
            'items': [item.to_dict() for item in items.items],
            'categorias': categorias,
            'pagination': {
                'page': page,
                'pages': items.pages,
                'per_page': per_page,
                'total': items.total
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@wiki_bp.route('/wiki', methods=['POST'])
@jwt_required()
def create_wiki_item():
    """Criar novo item na wiki"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('titulo') or not data.get('texto'):
            return jsonify({'error': 'Título e texto são obrigatórios'}), 400
        
        wiki_item = Wiki(
            titulo=data['titulo'],
            categoria=data.get('categoria', 'Geral'),
            texto=data['texto'],
            autor_id=user_id,
            status=data.get('status', 'Rascunho')
        )
        
        db.session.add(wiki_item)
        db.session.flush()  # Para obter o ID
        
        # Adicionar tags se fornecidas
        tags = data.get('tags', [])
        for tag_text in tags:
            if tag_text.strip():
                tag = WikiTag(wiki_id=wiki_item.id, tag=tag_text.strip())
                db.session.add(tag)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Item da wiki criado com sucesso',
            'item': wiki_item.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@wiki_bp.route('/wiki/<int:item_id>', methods=['GET'])
@jwt_required()
def get_wiki_item(item_id):
    """Obter detalhes de um item específico da wiki"""
    try:
        item = Wiki.query.get(item_id)
        
        if not item:
            return jsonify({'error': 'Item não encontrado'}), 404
        
        # Incrementar contador de visualizações
        item.views += 1
        db.session.commit()
        
        item_data = item.to_dict()
        item_data['comentarios'] = [comment.to_dict() for comment in item.comentarios]
        
        return jsonify({'item': item_data})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@wiki_bp.route('/wiki/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_wiki_item(item_id):
    """Atualizar item da wiki"""
    try:
        user_id = get_jwt_identity()
        item = Wiki.query.get(item_id)
        
        if not item:
            return jsonify({'error': 'Item não encontrado'}), 404
        
        # Verificar se o usuário é o autor (opcional: adicionar permissão de admin)
        if item.autor_id != user_id:
            return jsonify({'error': 'Você não tem permissão para editar este item'}), 403
        
        data = request.get_json()
        
        # Atualizar campos básicos
        if 'titulo' in data:
            item.titulo = data['titulo']
        if 'categoria' in data:
            item.categoria = data['categoria']
        if 'texto' in data:
            item.texto = data['texto']
        if 'status' in data:
            item.status = data['status']
        
        # Incrementar versão se houve alteração de conteúdo
        if 'texto' in data:
            item.versao += 1
        
        # Atualizar tags
        if 'tags' in data:
            # Remover tags existentes
            WikiTag.query.filter_by(wiki_id=item.id).delete()
            
            # Adicionar novas tags
            for tag_text in data['tags']:
                if tag_text.strip():
                    tag = WikiTag(wiki_id=item.id, tag=tag_text.strip())
                    db.session.add(tag)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Item atualizado com sucesso',
            'item': item.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@wiki_bp.route('/wiki/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_wiki_item(item_id):
    """Marcar item como obsoleto"""
    try:
        user_id = get_jwt_identity()
        item = Wiki.query.get(item_id)
        
        if not item:
            return jsonify({'error': 'Item não encontrado'}), 404
        
        # Verificar se o usuário é o autor
        if item.autor_id != user_id:
            return jsonify({'error': 'Você não tem permissão para excluir este item'}), 403
        
        # Marcar como obsoleto ao invés de deletar
        item.status = 'Obsoleto'
        db.session.commit()
        
        return jsonify({'message': 'Item marcado como obsoleto'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@wiki_bp.route('/wiki/search', methods=['GET'])
@jwt_required()
def search_wiki():
    """Busca avançada na wiki"""
    try:
        query_text = request.args.get('q', '')
        categoria = request.args.get('categoria', '')
        tags = request.args.get('tags', '').split(',') if request.args.get('tags') else []
        
        if not query_text and not categoria and not tags:
            return jsonify({'error': 'Pelo menos um parâmetro de busca é necessário'}), 400
        
        query = Wiki.query.filter_by(status='Publicado')
        
        if query_text:
            query = query.filter(
                db.or_(
                    Wiki.titulo.contains(query_text),
                    Wiki.texto.contains(query_text)
                )
            )
        
        if categoria:
            query = query.filter(Wiki.categoria == categoria)
        
        if tags:
            # Buscar por tags
            query = query.join(WikiTag).filter(
                WikiTag.tag.in_([tag.strip() for tag in tags if tag.strip()])
            )
        
        results = query.order_by(Wiki.views.desc()).limit(20).all()
        
        return jsonify({
            'results': [item.to_dict() for item in results],
            'total': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@wiki_bp.route('/wiki/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """Listar todas as categorias da wiki"""
    try:
        categorias = db.session.query(Wiki.categoria, db.func.count(Wiki.id)).filter_by(
            status='Publicado'
        ).group_by(Wiki.categoria).all()
        
        return jsonify({
            'categories': [{'nome': cat[0], 'count': cat[1]} for cat in categorias]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@wiki_bp.route('/wiki/popular', methods=['GET'])
@jwt_required()
def get_popular_items():
    """Obter itens mais visualizados da wiki"""
    try:
        limit = min(request.args.get('limit', 10, type=int), 50)
        
        items = Wiki.query.filter_by(status='Publicado').order_by(
            Wiki.views.desc()
        ).limit(limit).all()
        
        return jsonify({
            'items': [item.to_dict() for item in items]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@wiki_bp.route('/wiki/suggest', methods=['GET'])
@jwt_required()
def suggest_content():
    """Sugerir conteúdo da wiki baseado em contexto"""
    try:
        context = request.args.get('context', '')  # ex: 'processo', 'tarefa'
        entity_id = request.args.get('entity_id', type=int)
        
        if not context:
            return jsonify({'suggestions': []})
        
        # Busca básica por contexto - pode ser expandida com ML
        suggestions = Wiki.query.filter_by(status='Publicado').filter(
            db.or_(
                Wiki.titulo.contains(context),
                Wiki.categoria.contains(context),
                Wiki.texto.contains(context)
            )
        ).order_by(Wiki.views.desc()).limit(5).all()
        
        return jsonify({
            'suggestions': [item.to_dict() for item in suggestions]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@wiki_bp.route('/articles', methods=['GET'])
def get_articles():
    """Lista artigos com filtros e busca"""
    try:
        # Parâmetros de query
        query = request.args.get('q', '')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        # Filtros
        filters = {}
        if request.args.get('category_id'):
            filters['category_id'] = int(request.args.get('category_id'))
        
        if request.args.get('tags'):
            tag_ids = [int(tag_id) for tag_id in request.args.get('tags').split(',')]
            filters['tags'] = tag_ids
        
        if request.args.get('author_id'):
            filters['author_id'] = int(request.args.get('author_id'))
        
        if request.args.get('legal_areas'):
            filters['legal_areas'] = request.args.get('legal_areas').split(',')
        
        if request.args.get('is_featured'):
            filters['is_featured'] = request.args.get('is_featured').lower() == 'true'
        
        if request.args.get('date_from'):
            filters['date_from'] = request.args.get('date_from')
        
        if request.args.get('date_to'):
            filters['date_to'] = request.args.get('date_to')
        
        filters['sort_by'] = request.args.get('sort_by', 'relevance')
        
        # Buscar artigos
        user_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                from flask_jwt_extended import decode_token
                token = auth_header.replace('Bearer ', '')
                decoded = decode_token(token)
                user_id = decoded.get('sub')
            except:
                pass
        
        result = wiki_service.search_articles(
            query=query,
            filters=filters,
            page=page,
            per_page=per_page,
            user_id=user_id
        )
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar artigos: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao listar artigos'
        }), 500

@wiki_bp.route('/articles', methods=['POST'])
@jwt_required()
def create_article():
    """Cria um novo artigo"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validação básica
        if not data.get('title') or not data.get('content'):
            return jsonify({
                'success': False,
                'message': 'Título e conteúdo são obrigatórios'
            }), 400
        
        article = wiki_service.create_article(user_id, data)
        
        return jsonify({
            'success': True,
            'data': article.to_dict(),
            'message': 'Artigo criado com sucesso'
        }), 201
        
    except Exception as e:
        logger.error(f"Erro ao criar artigo: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e) if 'não encontrado' in str(e) else 'Erro ao criar artigo'
        }), 400 if 'não encontrado' in str(e) else 500

@wiki_bp.route('/articles/<int:article_id>', methods=['GET'])
def get_article(article_id):
    """Busca um artigo específico"""
    try:
        user_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                from flask_jwt_extended import decode_token
                token = auth_header.replace('Bearer ', '')
                decoded = decode_token(token)
                user_id = decoded.get('sub')
            except:
                pass
        
        article = wiki_service.get_article(article_id, user_id)
        
        if not article:
            return jsonify({
                'success': False,
                'message': 'Artigo não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'data': article.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar artigo: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar artigo'
        }), 500

@wiki_bp.route('/articles/slug/<slug>', methods=['GET'])
def get_article_by_slug(slug):
    """Busca um artigo por slug"""
    try:
        user_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                from flask_jwt_extended import decode_token
                token = auth_header.replace('Bearer ', '')
                decoded = decode_token(token)
                user_id = decoded.get('sub')
            except:
                pass
        
        article = wiki_service.get_article_by_slug(slug, user_id)
        
        if not article:
            return jsonify({
                'success': False,
                'message': 'Artigo não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'data': article.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar artigo por slug: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar artigo'
        }), 500

@wiki_bp.route('/articles/<int:article_id>', methods=['PUT'])
@jwt_required()
def update_article(article_id):
    """Atualiza um artigo"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        article = wiki_service.update_article(article_id, user_id, data)
        
        return jsonify({
            'success': True,
            'data': article.to_dict(),
            'message': 'Artigo atualizado com sucesso'
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    except Exception as e:
        logger.error(f"Erro ao atualizar artigo: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao atualizar artigo'
        }), 500

@wiki_bp.route('/articles/<int:article_id>', methods=['DELETE'])
@jwt_required()
def delete_article(article_id):
    """Remove um artigo"""
    try:
        user_id = get_jwt_identity()
        
        success = wiki_service.delete_article(article_id, user_id)
        
        if not success:
            return jsonify({
                'success': False,
                'message': 'Artigo não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Artigo removido com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao remover artigo: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao remover artigo'
        }), 500

@wiki_bp.route('/articles/featured', methods=['GET'])
def get_featured_articles():
    """Busca artigos em destaque"""
    try:
        limit = int(request.args.get('limit', 5))
        articles = wiki_service.get_featured_articles(limit)
        
        return jsonify({
            'success': True,
            'data': [article.to_dict(include_content=False) for article in articles]
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar artigos em destaque: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar artigos em destaque'
        }), 500

@wiki_bp.route('/articles/popular', methods=['GET'])
def get_popular_articles():
    """Busca artigos populares"""
    try:
        limit = int(request.args.get('limit', 10))
        days = int(request.args.get('days', 30))
        articles = wiki_service.get_popular_articles(limit, days)
        
        return jsonify({
            'success': True,
            'data': [article.to_dict(include_content=False) for article in articles]
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar artigos populares: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar artigos populares'
        }), 500

@wiki_bp.route('/articles/recent', methods=['GET'])
def get_recent_articles():
    """Busca artigos recentes"""
    try:
        limit = int(request.args.get('limit', 10))
        articles = wiki_service.get_recent_articles(limit)
        
        return jsonify({
            'success': True,
            'data': [article.to_dict(include_content=False) for article in articles]
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar artigos recentes: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar artigos recentes'
        }), 500

@wiki_bp.route('/categories', methods=['GET'])
def get_categories():
    """Lista categorias em árvore"""
    try:
        tree = wiki_service.get_categories_tree()
        
        return jsonify({
            'success': True,
            'data': tree
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar categorias: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar categorias'
        }), 500

@wiki_bp.route('/categories', methods=['POST'])
@jwt_required()
def create_category():
    """Cria uma nova categoria"""
    try:
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({
                'success': False,
                'message': 'Nome da categoria é obrigatório'
            }), 400
        
        category = wiki_service.create_category(data)
        
        return jsonify({
            'success': True,
            'data': category.to_dict(),
            'message': 'Categoria criada com sucesso'
        }), 201
        
    except Exception as e:
        logger.error(f"Erro ao criar categoria: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao criar categoria'
        }), 500

@wiki_bp.route('/tags', methods=['GET'])
def get_tags():
    """Lista tags populares"""
    try:
        limit = int(request.args.get('limit', 20))
        tags = wiki_service.get_popular_tags(limit)
        
        return jsonify({
            'success': True,
            'data': [tag.to_dict() for tag in tags]
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar tags: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar tags'
        }), 500

@wiki_bp.route('/tags', methods=['POST'])
@jwt_required()
def create_tag():
    """Cria uma nova tag"""
    try:
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({
                'success': False,
                'message': 'Nome da tag é obrigatório'
            }), 400
        
        tag = wiki_service.create_tag(data['name'], data.get('description', ''))
        
        return jsonify({
            'success': True,
            'data': tag.to_dict(),
            'message': 'Tag criada com sucesso'
        }), 201
        
    except Exception as e:
        logger.error(f"Erro ao criar tag: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao criar tag'
        }), 500

@wiki_bp.route('/articles/<int:article_id>/comments', methods=['GET'])
def get_article_comments(article_id):
    """Busca comentários de um artigo"""
    try:
        comments = wiki_service.get_article_comments(article_id)
        
        return jsonify({
            'success': True,
            'data': [comment.to_dict() for comment in comments]
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar comentários: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar comentários'
        }), 500

@wiki_bp.route('/articles/<int:article_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(article_id):
    """Adiciona comentário a um artigo"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('content'):
            return jsonify({
                'success': False,
                'message': 'Conteúdo do comentário é obrigatório'
            }), 400
        
        comment = wiki_service.add_comment(
            article_id=article_id,
            user_id=user_id,
            content=data['content'],
            parent_id=data.get('parent_id')
        )
        
        return jsonify({
            'success': True,
            'data': comment.to_dict(),
            'message': 'Comentário adicionado com sucesso'
        }), 201
        
    except Exception as e:
        logger.error(f"Erro ao adicionar comentário: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao adicionar comentário'
        }), 500

@wiki_bp.route('/articles/<int:article_id>/bookmark', methods=['POST'])
@jwt_required()
def toggle_bookmark(article_id):
    """Adiciona ou remove bookmark"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        result = wiki_service.toggle_bookmark(
            user_id=user_id,
            article_id=article_id,
            notes=data.get('notes', '')
        )
        
        return jsonify({
            'success': True,
            'data': result,
            'message': 'Bookmark atualizado com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao alterar bookmark: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao alterar bookmark'
        }), 500

@wiki_bp.route('/articles/<int:article_id>/like', methods=['POST'])
@jwt_required()
def toggle_like(article_id):
    """Adiciona ou remove curtida"""
    try:
        user_id = get_jwt_identity()
        
        result = wiki_service.toggle_like(user_id, article_id)
        
        return jsonify({
            'success': True,
            'data': result,
            'message': 'Curtida atualizada com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao alterar curtida: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao alterar curtida'
        }), 500

@wiki_bp.route('/bookmarks', methods=['GET'])
@jwt_required()
def get_user_bookmarks():
    """Busca bookmarks do usuário"""
    try:
        user_id = get_jwt_identity()
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        result = wiki_service.get_user_bookmarks(user_id, page, per_page)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar bookmarks: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar bookmarks'
        }), 500

@wiki_bp.route('/stats', methods=['GET'])
def get_wiki_stats():
    """Busca estatísticas da wiki"""
    try:
        from models.wiki import WikiArticle, WikiCategory, WikiTag
        from sqlalchemy import func
        
        # Estatísticas básicas
        total_articles = WikiArticle.query.filter_by(status='published').count()
        total_categories = WikiCategory.query.filter_by(is_active=True).count()
        total_tags = WikiTag.query.count()
        
        # Artigos por categoria
        articles_by_category = db.session.query(
            WikiCategory.name,
            func.count(WikiArticle.id).label('count')
        ).join(WikiArticle).filter(
            WikiArticle.status == 'published'
        ).group_by(WikiCategory.name).all()
        
        # Tags mais usadas
        top_tags = db.session.query(
            WikiTag.name,
            WikiTag.usage_count
        ).order_by(WikiTag.usage_count.desc()).limit(10).all()
        
        return jsonify({
            'success': True,
            'data': {
                'totals': {
                    'articles': total_articles,
                    'categories': total_categories,
                    'tags': total_tags
                },
                'articles_by_category': [
                    {'category': cat.name, 'count': cat.count}
                    for cat in articles_by_category
                ],
                'top_tags': [
                    {'name': tag.name, 'usage_count': tag.usage_count}
                    for tag in top_tags
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar estatísticas'
        }), 500

@wiki_bp.route('/search/suggestions', methods=['GET'])
def get_search_suggestions():
    """Busca sugestões de busca"""
    try:
        query = request.args.get('q', '').strip()
        
        if len(query) < 2:
            return jsonify({
                'success': True,
                'data': {'suggestions': []}
            })
        
        # Buscar em títulos de artigos
        articles = WikiArticle.query.filter(
            WikiArticle.title.ilike(f'%{query}%'),
            WikiArticle.status == 'published'
        ).limit(5).all()
        
        # Buscar em tags
        tags = WikiTag.query.filter(
            WikiTag.name.ilike(f'%{query}%')
        ).limit(5).all()
        
        suggestions = []
        
        # Adicionar artigos
        for article in articles:
            suggestions.append({
                'type': 'article',
                'title': article.title,
                'url': f'/wiki/articles/{article.slug}',
                'category': article.category.name if article.category else None
            })
        
        # Adicionar tags
        for tag in tags:
            suggestions.append({
                'type': 'tag',
                'title': f'Tag: {tag.name}',
                'url': f'/wiki/articles?tags={tag.id}',
                'category': 'Tag'
            })
        
        return jsonify({
            'success': True,
            'data': {'suggestions': suggestions}
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar sugestões: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar sugestões'
        }), 500 