from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy import or_, and_, func, desc, asc, text
from sqlalchemy.orm import joinedload
from extensions import db
from models.wiki import (
    WikiArticle, WikiCategory, WikiTag, WikiRevision, 
    WikiComment, WikiBookmark, WikiLike, WikiSearchLog,
    wiki_article_tags
)
from models.user import User
import logging
import re
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class WikiService:
    def __init__(self):
        self.search_stopwords = {
            'o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas',
            'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 'nos', 'nas',
            'para', 'por', 'com', 'sem', 'sobre', 'sob', 'entre', 'contra',
            'e', 'ou', 'mas', 'se', 'que', 'quando', 'onde', 'como', 'porque'
        }
    
    # === GESTÃO DE ARTIGOS ===
    
    def create_article(self, user_id: int, data: Dict[str, Any]) -> WikiArticle:
        """Cria um novo artigo na wiki"""
        try:
            # Gerar slug único
            slug = self._generate_slug(data['title'])
            
            article = WikiArticle(
                title=data['title'],
                slug=slug,
                excerpt=data.get('excerpt', ''),
                content=data['content'],
                category_id=data.get('category_id'),
                author_id=user_id,
                status=data.get('status', 'draft'),
                is_featured=data.get('is_featured', False),
                is_public=data.get('is_public', True),
                keywords=data.get('keywords', ''),
                legal_areas=data.get('legal_areas', [])
            )
            
            db.session.add(article)
            db.session.flush()  # Para obter o ID
            
            # Processar tags
            if 'tags' in data:
                self._process_article_tags(article, data['tags'])
            
            # Criar primeira revisão
            self._create_revision(article, user_id, "Criação inicial do artigo")
            
            db.session.commit()
            
            logger.info(f"Artigo '{article.title}' criado pelo usuário {user_id}")
            return article
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao criar artigo: {str(e)}")
            raise
    
    def update_article(self, article_id: int, user_id: int, data: Dict[str, Any]) -> WikiArticle:
        """Atualiza um artigo existente"""
        try:
            article = WikiArticle.query.get(article_id)
            if not article:
                raise ValueError("Artigo não encontrado")
            
            # Verificar permissões (autor ou admin)
            if article.author_id != user_id:
                # Implementar verificação de permissão admin
                pass
            
            # Backup dos dados originais para revisão
            original_title = article.title
            original_content = article.content
            
            # Atualizar campos
            if 'title' in data and data['title'] != article.title:
                article.title = data['title']
                article.slug = self._generate_slug(data['title'])
            
            if 'excerpt' in data:
                article.excerpt = data['excerpt']
            
            if 'content' in data:
                article.content = data['content']
            
            if 'category_id' in data:
                article.category_id = data['category_id']
            
            if 'status' in data:
                article.status = data['status']
                if data['status'] == 'published' and not article.published_at:
                    article.published_at = datetime.utcnow()
            
            if 'is_featured' in data:
                article.is_featured = data['is_featured']
            
            if 'is_public' in data:
                article.is_public = data['is_public']
            
            if 'keywords' in data:
                article.keywords = data['keywords']
            
            if 'legal_areas' in data:
                article.legal_areas = data['legal_areas']
            
            # Processar tags
            if 'tags' in data:
                self._process_article_tags(article, data['tags'])
            
            # Incrementar versão e criar revisão
            article.version += 1
            article.updated_at = datetime.utcnow()
            
            change_summary = data.get('change_summary', 'Atualização do artigo')
            self._create_revision(article, user_id, change_summary)
            
            db.session.commit()
            
            logger.info(f"Artigo '{article.title}' atualizado pelo usuário {user_id}")
            return article
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao atualizar artigo: {str(e)}")
            raise
    
    def delete_article(self, article_id: int, user_id: int) -> bool:
        """Remove um artigo (soft delete)"""
        try:
            article = WikiArticle.query.get(article_id)
            if not article:
                return False
            
            # Verificar permissões
            if article.author_id != user_id:
                # Implementar verificação de permissão admin
                pass
            
            article.status = 'archived'
            article.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Artigo '{article.title}' arquivado pelo usuário {user_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao arquivar artigo: {str(e)}")
            return False
    
    def get_article(self, article_id: int, user_id: Optional[int] = None) -> Optional[WikiArticle]:
        """Busca um artigo por ID"""
        try:
            article = WikiArticle.query.options(
                joinedload(WikiArticle.category),
                joinedload(WikiArticle.author),
                joinedload(WikiArticle.tags)
            ).get(article_id)
            
            if article and user_id:
                # Incrementar contador de visualizações
                article.increment_view_count()
            
            return article
            
        except Exception as e:
            logger.error(f"Erro ao buscar artigo: {str(e)}")
            return None
    
    def get_article_by_slug(self, slug: str, user_id: Optional[int] = None) -> Optional[WikiArticle]:
        """Busca um artigo por slug"""
        try:
            article = WikiArticle.query.options(
                joinedload(WikiArticle.category),
                joinedload(WikiArticle.author),
                joinedload(WikiArticle.tags)
            ).filter_by(slug=slug).first()
            
            if article and user_id:
                article.increment_view_count()
            
            return article
            
        except Exception as e:
            logger.error(f"Erro ao buscar artigo por slug: {str(e)}")
            return None
    
    def search_articles(self, query: str, filters: Dict[str, Any] = None, 
                       page: int = 1, per_page: int = 20, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Busca artigos com filtros avançados"""
        try:
            # Log da busca
            if user_id:
                search_log = WikiSearchLog(
                    user_id=user_id,
                    query=query
                )
                db.session.add(search_log)
            
            # Query base
            base_query = WikiArticle.query.options(
                joinedload(WikiArticle.category),
                joinedload(WikiArticle.author),
                joinedload(WikiArticle.tags)
            ).filter(WikiArticle.status == 'published')
            
            # Busca por texto
            if query:
                search_terms = self._process_search_query(query)
                search_conditions = []
                
                for term in search_terms:
                    search_conditions.append(
                        or_(
                            WikiArticle.title.ilike(f'%{term}%'),
                            WikiArticle.content.ilike(f'%{term}%'),
                            WikiArticle.keywords.ilike(f'%{term}%'),
                            WikiArticle.excerpt.ilike(f'%{term}%')
                        )
                    )
                
                if search_conditions:
                    base_query = base_query.filter(and_(*search_conditions))
            
            # Aplicar filtros
            if filters:
                if 'category_id' in filters:
                    base_query = base_query.filter(WikiArticle.category_id == filters['category_id'])
                
                if 'tags' in filters:
                    tag_ids = filters['tags']
                    base_query = base_query.join(wiki_article_tags).filter(
                        wiki_article_tags.c.tag_id.in_(tag_ids)
                    )
                
                if 'author_id' in filters:
                    base_query = base_query.filter(WikiArticle.author_id == filters['author_id'])
                
                if 'legal_areas' in filters:
                    legal_areas = filters['legal_areas']
                    for area in legal_areas:
                        base_query = base_query.filter(
                            WikiArticle.legal_areas.contains([area])
                        )
                
                if 'is_featured' in filters:
                    base_query = base_query.filter(WikiArticle.is_featured == filters['is_featured'])
                
                if 'date_from' in filters:
                    base_query = base_query.filter(WikiArticle.published_at >= filters['date_from'])
                
                if 'date_to' in filters:
                    base_query = base_query.filter(WikiArticle.published_at <= filters['date_to'])
            
            # Ordenação
            sort_by = filters.get('sort_by', 'relevance') if filters else 'relevance'
            
            if sort_by == 'date_desc':
                base_query = base_query.order_by(desc(WikiArticle.published_at))
            elif sort_by == 'date_asc':
                base_query = base_query.order_by(asc(WikiArticle.published_at))
            elif sort_by == 'title':
                base_query = base_query.order_by(asc(WikiArticle.title))
            elif sort_by == 'views':
                base_query = base_query.order_by(desc(WikiArticle.view_count))
            elif sort_by == 'likes':
                base_query = base_query.order_by(desc(WikiArticle.like_count))
            
            # Paginação
            total = base_query.count()
            articles = base_query.offset((page - 1) * per_page).limit(per_page).all()
            
            # Atualizar log de busca com contagem de resultados
            if user_id and search_log:
                search_log.results_count = total
                db.session.commit()
            
            return {
                'articles': [article.to_dict(include_content=False) for article in articles],
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page,
                'has_next': page * per_page < total,
                'has_prev': page > 1
            }
            
        except Exception as e:
            logger.error(f"Erro na busca de artigos: {str(e)}")
            raise
    
    def get_featured_articles(self, limit: int = 5) -> List[WikiArticle]:
        """Busca artigos em destaque"""
        try:
            return WikiArticle.query.options(
                joinedload(WikiArticle.category),
                joinedload(WikiArticle.author)
            ).filter(
                WikiArticle.status == 'published',
                WikiArticle.is_featured == True
            ).order_by(desc(WikiArticle.published_at)).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Erro ao buscar artigos em destaque: {str(e)}")
            return []
    
    def get_popular_articles(self, limit: int = 10, days: int = 30) -> List[WikiArticle]:
        """Busca artigos mais populares"""
        try:
            date_limit = datetime.utcnow() - timedelta(days=days)
            
            return WikiArticle.query.options(
                joinedload(WikiArticle.category),
                joinedload(WikiArticle.author)
            ).filter(
                WikiArticle.status == 'published',
                WikiArticle.published_at >= date_limit
            ).order_by(
                desc(WikiArticle.view_count),
                desc(WikiArticle.like_count)
            ).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Erro ao buscar artigos populares: {str(e)}")
            return []
    
    def get_recent_articles(self, limit: int = 10) -> List[WikiArticle]:
        """Busca artigos mais recentes"""
        try:
            return WikiArticle.query.options(
                joinedload(WikiArticle.category),
                joinedload(WikiArticle.author)
            ).filter(
                WikiArticle.status == 'published'
            ).order_by(desc(WikiArticle.published_at)).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Erro ao buscar artigos recentes: {str(e)}")
            return []
    
    # === GESTÃO DE CATEGORIAS ===
    
    def create_category(self, data: Dict[str, Any]) -> WikiCategory:
        """Cria uma nova categoria"""
        try:
            slug = self._generate_slug(data['name'])
            
            category = WikiCategory(
                name=data['name'],
                slug=slug,
                description=data.get('description', ''),
                color=data.get('color', '#1890ff'),
                icon=data.get('icon', ''),
                parent_id=data.get('parent_id'),
                sort_order=data.get('sort_order', 0)
            )
            
            db.session.add(category)
            db.session.commit()
            
            logger.info(f"Categoria '{category.name}' criada")
            return category
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao criar categoria: {str(e)}")
            raise
    
    def get_categories_tree(self) -> List[Dict[str, Any]]:
        """Busca categorias organizadas em árvore"""
        try:
            categories = WikiCategory.query.filter_by(
                is_active=True
            ).order_by(WikiCategory.sort_order, WikiCategory.name).all()
            
            # Organizar em árvore
            tree = []
            category_map = {cat.id: cat.to_dict() for cat in categories}
            
            for category in categories:
                cat_dict = category_map[category.id]
                if category.parent_id:
                    parent = category_map.get(category.parent_id)
                    if parent:
                        if 'children' not in parent:
                            parent['children'] = []
                        parent['children'].append(cat_dict)
                else:
                    tree.append(cat_dict)
            
            return tree
            
        except Exception as e:
            logger.error(f"Erro ao buscar árvore de categorias: {str(e)}")
            return []
    
    # === GESTÃO DE TAGS ===
    
    def create_tag(self, name: str, description: str = '') -> WikiTag:
        """Cria uma nova tag"""
        try:
            slug = self._generate_slug(name)
            
            # Verificar se já existe
            existing = WikiTag.query.filter_by(slug=slug).first()
            if existing:
                return existing
            
            tag = WikiTag(
                name=name,
                slug=slug,
                description=description
            )
            
            db.session.add(tag)
            db.session.commit()
            
            return tag
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao criar tag: {str(e)}")
            raise
    
    def get_popular_tags(self, limit: int = 20) -> List[WikiTag]:
        """Busca tags mais populares"""
        try:
            return WikiTag.query.order_by(
                desc(WikiTag.usage_count)
            ).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Erro ao buscar tags populares: {str(e)}")
            return []
    
    # === COMENTÁRIOS ===
    
    def add_comment(self, article_id: int, user_id: int, content: str, parent_id: Optional[int] = None) -> WikiComment:
        """Adiciona comentário a um artigo"""
        try:
            comment = WikiComment(
                article_id=article_id,
                parent_id=parent_id,
                content=content,
                author_id=user_id
            )
            
            db.session.add(comment)
            
            # Atualizar contador de comentários do artigo
            article = WikiArticle.query.get(article_id)
            if article:
                article.comment_count += 1
            
            db.session.commit()
            
            logger.info(f"Comentário adicionado ao artigo {article_id} pelo usuário {user_id}")
            return comment
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao adicionar comentário: {str(e)}")
            raise
    
    def get_article_comments(self, article_id: int) -> List[WikiComment]:
        """Busca comentários de um artigo"""
        try:
            return WikiComment.query.options(
                joinedload(WikiComment.author)
            ).filter(
                WikiComment.article_id == article_id,
                WikiComment.is_deleted == False,
                WikiComment.is_approved == True,
                WikiComment.parent_id == None  # Apenas comentários raiz
            ).order_by(WikiComment.created_at).all()
            
        except Exception as e:
            logger.error(f"Erro ao buscar comentários: {str(e)}")
            return []
    
    # === BOOKMARKS E LIKES ===
    
    def toggle_bookmark(self, user_id: int, article_id: int, notes: str = '') -> Dict[str, Any]:
        """Adiciona ou remove bookmark"""
        try:
            existing = WikiBookmark.query.filter_by(
                user_id=user_id,
                article_id=article_id
            ).first()
            
            if existing:
                db.session.delete(existing)
                bookmarked = False
            else:
                bookmark = WikiBookmark(
                    user_id=user_id,
                    article_id=article_id,
                    notes=notes
                )
                db.session.add(bookmark)
                bookmarked = True
            
            db.session.commit()
            
            return {'bookmarked': bookmarked}
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao alternar bookmark: {str(e)}")
            raise
    
    def toggle_like(self, user_id: int, article_id: int) -> Dict[str, Any]:
        """Adiciona ou remove curtida"""
        try:
            existing = WikiLike.query.filter_by(
                user_id=user_id,
                article_id=article_id
            ).first()
            
            article = WikiArticle.query.get(article_id)
            if not article:
                raise ValueError("Artigo não encontrado")
            
            if existing:
                db.session.delete(existing)
                article.remove_like()
                liked = False
            else:
                like = WikiLike(
                    user_id=user_id,
                    article_id=article_id
                )
                db.session.add(like)
                article.add_like()
                liked = True
            
            db.session.commit()
            
            return {'liked': liked, 'like_count': article.like_count}
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao alternar curtida: {str(e)}")
            raise
    
    def get_user_bookmarks(self, user_id: int, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Busca bookmarks do usuário"""
        try:
            query = WikiBookmark.query.options(
                joinedload(WikiBookmark.article).joinedload(WikiArticle.category),
                joinedload(WikiBookmark.article).joinedload(WikiArticle.author)
            ).filter(WikiBookmark.user_id == user_id)
            
            total = query.count()
            bookmarks = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'bookmarks': [bookmark.to_dict() for bookmark in bookmarks],
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar bookmarks: {str(e)}")
            return {'bookmarks': [], 'total': 0}
    
    # === MÉTODOS AUXILIARES ===
    
    def _generate_slug(self, title: str) -> str:
        """Gera slug único a partir do título"""
        import unicodedata
        import re
        
        # Normalizar e remover acentos
        slug = unicodedata.normalize('NFKD', title)
        slug = slug.encode('ascii', 'ignore').decode('ascii')
        
        # Converter para minúsculas e substituir espaços
        slug = re.sub(r'[^\w\s-]', '', slug.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        slug = slug.strip('-')
        
        # Verificar unicidade
        base_slug = slug
        counter = 1
        
        while WikiArticle.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def _process_search_query(self, query: str) -> List[str]:
        """Processa query de busca removendo stopwords"""
        words = re.findall(r'\w+', query.lower())
        return [word for word in words if word not in self.search_stopwords and len(word) > 2]
    
    def _process_article_tags(self, article: WikiArticle, tag_names: List[str]):
        """Processa tags do artigo"""
        # Limpar tags existentes
        article.tags.clear()
        
        for tag_name in tag_names:
            tag_name = tag_name.strip()
            if not tag_name:
                continue
            
            # Buscar ou criar tag
            tag = WikiTag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = self.create_tag(tag_name)
            
            # Incrementar contador de uso
            tag.usage_count += 1
            
            # Associar ao artigo
            article.tags.append(tag)
    
    def _create_revision(self, article: WikiArticle, user_id: int, change_summary: str):
        """Cria revisão do artigo"""
        revision = WikiRevision(
            article_id=article.id,
            version=article.version,
            title=article.title,
            content=article.content,
            change_summary=change_summary,
            author_id=user_id
        )
        
        db.session.add(revision)

# Instância global do serviço
wiki_service = WikiService() 