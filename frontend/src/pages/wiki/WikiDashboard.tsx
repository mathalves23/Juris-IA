import React, { useState, useEffect } from 'react';
import {
  Layout,
  Card,
  Row,
  Col,
  Typography,
  Input,
  Button,
  List,
  Tag,
  Space,
  Statistic,
  Divider,
  Avatar,
  Tabs,
  AutoComplete,
  Badge,
  Tooltip,
  Empty,
  Spin
} from 'antd';
import {
  SearchOutlined,
  BookOutlined,
  TagsOutlined,
  TeamOutlined,
  EyeOutlined,
  HeartOutlined,
  CommentOutlined,
  PlusOutlined,
  StarOutlined,
  ClockCircleOutlined,
  FireOutlined,
  HeartFilled
} from '@ant-design/icons';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import './WikiDashboard.css';

const { Content, Sider } = Layout;
const { Title, Text, Paragraph } = Typography;
const { Search } = Input;
const { TabPane } = Tabs;

interface WikiArticle {
  id: number;
  title: string;
  slug: string;
  excerpt: string;
  category?: {
    id: number;
    name: string;
    color: string;
    icon: string;
  };
  author: {
    id: number;
    name: string;
    email: string;
  };
  tags: Array<{
    id: number;
    name: string;
    color: string;
  }>;
  view_count: number;
  like_count: number;
  comment_count: number;
  created_at: string;
  updated_at: string;
  published_at: string;
}

interface WikiCategory {
  id: number;
  name: string;
  slug: string;
  description: string;
  color: string;
  icon: string;
  children?: WikiCategory[];
}

interface WikiTag {
  id: number;
  name: string;
  usage_count: number;
  color: string;
}

interface WikiStats {
  totals: {
    articles: number;
    categories: number;
    tags: number;
  };
  articles_by_category: Array<{
    category: string;
    count: number;
  }>;
  top_tags: Array<{
    name: string;
    usage_count: number;
  }>;
}

const WikiDashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [featuredArticles, setFeaturedArticles] = useState<WikiArticle[]>([]);
  const [popularArticles, setPopularArticles] = useState<WikiArticle[]>([]);
  const [recentArticles, setRecentArticles] = useState<WikiArticle[]>([]);
  const [categories, setCategories] = useState<WikiCategory[]>([]);
  const [popularTags, setPopularTags] = useState<WikiTag[]>([]);
  const [stats, setStats] = useState<WikiStats | null>(null);
  const [searchValue, setSearchValue] = useState('');
  const [searchSuggestions, setSearchSuggestions] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState('featured');

  const navigate = useNavigate();

  // Carregar dados iniciais
  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      const [
        featuredRes,
        popularRes,
        recentRes,
        categoriesRes,
        tagsRes,
        statsRes
      ] = await Promise.all([
        axios.get('/api/wiki/articles/featured?limit=5'),
        axios.get('/api/wiki/articles/popular?limit=10'),
        axios.get('/api/wiki/articles/recent?limit=10'),
        axios.get('/api/wiki/categories'),
        axios.get('/api/wiki/tags?limit=20'),
        axios.get('/api/wiki/stats')
      ]);

      setFeaturedArticles(featuredRes.data.data || []);
      setPopularArticles(popularRes.data.data || []);
      setRecentArticles(recentRes.data.data || []);
      setCategories(categoriesRes.data.data || []);
      setPopularTags(tagsRes.data.data || []);
      setStats(statsRes.data.data || null);

    } catch (error) {
      console.error('Erro ao carregar dados:', error);
    } finally {
      setLoading(false);
    }
  };

  // Buscar sugestões
  const handleSearch = async (value: string) => {
    if (value.length < 2) {
      setSearchSuggestions([]);
      return;
    }

    try {
      setSearchLoading(true);
      const response = await axios.get(`/api/wiki/search/suggestions?q=${encodeURIComponent(value)}`);
      setSearchSuggestions(response.data.data.suggestions || []);
    } catch (error) {
      console.error('Erro ao buscar sugestões:', error);
    } finally {
      setSearchLoading(false);
    }
  };

  // Executar busca
  const onSearch = (value: string) => {
    if (value.trim()) {
      navigate(`/wiki/search?q=${encodeURIComponent(value.trim())}`);
    }
  };

  // Navegar para artigo
  const goToArticle = (article: WikiArticle) => {
    navigate(`/wiki/articles/${article.slug}`);
  };

  // Navegar para categoria
  const goToCategory = (category: WikiCategory) => {
    navigate(`/wiki/search?category_id=${category.id}`);
  };

  // Navegar para tag
  const goToTag = (tag: WikiTag) => {
    navigate(`/wiki/search?tags=${tag.id}`);
  };

  // Renderizar artigo da lista
  const renderArticleItem = (article: WikiArticle) => (
    <List.Item
      key={article.id}
      className="wiki-article-item"
      onClick={() => goToArticle(article)}
      actions={[
        <Tooltip title="Visualizações">
          <Space>
            <EyeOutlined />
            <Text type="secondary">{article.view_count}</Text>
          </Space>
        </Tooltip>,
        <Tooltip title="Curtidas">
          <Space>
            <HeartOutlined />
            <Text type="secondary">{article.like_count}</Text>
          </Space>
        </Tooltip>,
        <Tooltip title="Comentários">
          <Space>
            <CommentOutlined />
            <Text type="secondary">{article.comment_count}</Text>
          </Space>
        </Tooltip>
      ]}
    >
      <List.Item.Meta
        avatar={
          <Avatar
            style={{ 
              backgroundColor: article.category?.color || '#1890ff',
              fontSize: '18px'
            }}
            icon={article.category?.icon ? article.category.icon : <BookOutlined />}
          />
        }
        title={
          <div className="article-title">
            <Text strong>{article.title}</Text>
            {article.category && (
              <Tag 
                color={article.category.color}
                style={{ marginLeft: '8px' }}
              >
                {article.category.name}
              </Tag>
            )}
          </div>
        }
        description={
          <div>
            <Paragraph ellipsis={{ rows: 2 }} style={{ marginBottom: '8px' }}>
              {article.excerpt}
            </Paragraph>
            <div className="article-meta">
              <Space size="small">
                <Text type="secondary">Por {article.author.name}</Text>
                <Divider type="vertical" />
                <Text type="secondary">
                  {new Date(article.published_at || article.created_at).toLocaleDateString()}
                </Text>
              </Space>
              <div className="article-tags">
                {article.tags.slice(0, 3).map(tag => (
                  <Tag 
                    key={tag.id} 
                    size="small"
                    color={tag.color}
                    onClick={(e) => {
                      e.stopPropagation();
                      goToTag(tag);
                    }}
                  >
                    {tag.name}
                  </Tag>
                ))}
                {article.tags.length > 3 && (
                  <Text type="secondary">+{article.tags.length - 3} mais</Text>
                )}
              </div>
            </div>
          </div>
        }
      />
    </List.Item>
  );

  // Renderizar categoria na árvore
  const renderCategory = (category: WikiCategory, level: number = 0) => (
    <div key={category.id} style={{ marginLeft: level * 16 }}>
      <div
        className="category-item"
        onClick={() => goToCategory(category)}
        style={{ 
          padding: '8px 12px',
          borderRadius: '6px',
          cursor: 'pointer',
          marginBottom: '4px'
        }}
      >
        <Space>
          <span style={{ color: category.color, fontSize: '16px' }}>
            {category.icon || <BookOutlined />}
          </span>
          <Text>{category.name}</Text>
        </Space>
      </div>
      {category.children?.map(child => renderCategory(child, level + 1))}
    </div>
  );

  return (
    <Layout className="wiki-dashboard">
      <Content style={{ padding: '24px' }}>
        {/* Header com busca */}
        <div className="wiki-header">
          <Row gutter={[24, 24]} align="middle">
            <Col xs={24} lg={12}>
              <div>
                <Title level={2} style={{ marginBottom: '8px' }}>
                  📚 Base de Conhecimento
                </Title>
                <Text type="secondary">
                  Explore artigos jurídicos, precedentes e conhecimento especializado
                </Text>
              </div>
            </Col>
            <Col xs={24} lg={12}>
              <div style={{ display: 'flex', gap: '12px' }}>
                <AutoComplete
                  style={{ flex: 1 }}
                  options={searchSuggestions.map(suggestion => ({
                    value: suggestion.title,
                    label: (
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>{suggestion.title}</span>
                        <Tag size="small">{suggestion.category}</Tag>
                      </div>
                    )
                  }))}
                  onSearch={handleSearch}
                  onSelect={onSearch}
                  notFoundContent={searchLoading ? <Spin size="small" /> : null}
                >
                  <Search
                    placeholder="Buscar artigos, temas, precedentes..."
                    enterButton={<SearchOutlined />}
                    size="large"
                    onSearch={onSearch}
                    loading={searchLoading}
                  />
                </AutoComplete>
                <Button 
                  type="primary" 
                  size="large" 
                  icon={<PlusOutlined />}
                  onClick={() => navigate('/wiki/new-article')}
                >
                  Novo Artigo
                </Button>
              </div>
            </Col>
          </Row>
        </div>

        {/* Estatísticas */}
        {stats && (
          <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
            <Col xs={8} sm={6} lg={4}>
              <Card>
                <Statistic
                  title="Artigos"
                  value={stats.totals.articles}
                  prefix={<BookOutlined />}
                />
              </Card>
            </Col>
            <Col xs={8} sm={6} lg={4}>
              <Card>
                <Statistic
                  title="Categorias"
                  value={stats.totals.categories}
                  prefix={<TagsOutlined />}
                />
              </Card>
            </Col>
            <Col xs={8} sm={6} lg={4}>
              <Card>
                <Statistic
                  title="Tags"
                  value={stats.totals.tags}
                  prefix={<TagsOutlined />}
                />
              </Card>
            </Col>
          </Row>
        )}

        <Row gutter={[24, 24]}>
          {/* Conteúdo principal */}
          <Col xs={24} lg={16}>
            <Card>
              <Tabs 
                activeKey={activeTab} 
                onChange={setActiveTab}
                size="large"
              >
                <TabPane 
                  tab={
                    <span>
                      <StarOutlined />
                      Em Destaque
                    </span>
                  } 
                  key="featured"
                >
                  {loading ? (
                    <div style={{ textAlign: 'center', padding: '40px' }}>
                      <Spin size="large" />
                    </div>
                  ) : featuredArticles.length > 0 ? (
                    <List
                      dataSource={featuredArticles}
                      renderItem={renderArticleItem}
                      size="large"
                    />
                  ) : (
                    <Empty description="Nenhum artigo em destaque" />
                  )}
                </TabPane>

                <TabPane 
                  tab={
                    <span>
                      <FireOutlined />
                      Populares
                    </span>
                  } 
                  key="popular"
                >
                  {loading ? (
                    <div style={{ textAlign: 'center', padding: '40px' }}>
                      <Spin size="large" />
                    </div>
                  ) : popularArticles.length > 0 ? (
                    <List
                      dataSource={popularArticles}
                      renderItem={renderArticleItem}
                      size="large"
                    />
                  ) : (
                    <Empty description="Nenhum artigo popular" />
                  )}
                </TabPane>

                <TabPane 
                  tab={
                    <span>
                      <ClockCircleOutlined />
                      Recentes
                    </span>
                  } 
                  key="recent"
                >
                  {loading ? (
                    <div style={{ textAlign: 'center', padding: '40px' }}>
                      <Spin size="large" />
                    </div>
                  ) : recentArticles.length > 0 ? (
                    <List
                      dataSource={recentArticles}
                      renderItem={renderArticleItem}
                      size="large"
                    />
                  ) : (
                    <Empty description="Nenhum artigo recente" />
                  )}
                </TabPane>
              </Tabs>
            </Card>
          </Col>

          {/* Sidebar */}
          <Col xs={24} lg={8}>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              {/* Categorias */}
              <Card 
                title={
                  <Space>
                    <TagsOutlined />
                    <span>Categorias</span>
                  </Space>
                }
                size="small"
              >
                {loading ? (
                  <Spin />
                ) : categories.length > 0 ? (
                  <div className="categories-tree">
                    {categories.map(category => renderCategory(category))}
                  </div>
                ) : (
                  <Empty description="Nenhuma categoria" size="small" />
                )}
              </Card>

              {/* Tags populares */}
              <Card
                title={
                  <Space>
                    <TagsOutlined />
                    <span>Tags Populares</span>
                  </Space>
                }
                size="small"
              >
                {loading ? (
                  <Spin />
                ) : popularTags.length > 0 ? (
                  <div className="popular-tags">
                    {popularTags.map(tag => (
                      <Tag
                        key={tag.id}
                        color={tag.color}
                        style={{ 
                          marginBottom: '8px',
                          cursor: 'pointer'
                        }}
                        onClick={() => goToTag(tag)}
                      >
                        {tag.name}
                        <Badge 
                          count={tag.usage_count} 
                          size="small" 
                          style={{ marginLeft: '8px' }}
                        />
                      </Tag>
                    ))}
                  </div>
                ) : (
                  <Empty description="Nenhuma tag" size="small" />
                )}
              </Card>

              {/* Ações rápidas */}
              <Card
                title="Ações Rápidas"
                size="small"
              >
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Button 
                    block 
                    icon={<PlusOutlined />}
                    onClick={() => navigate('/wiki/new-article')}
                  >
                    Criar Artigo
                  </Button>
                  <Button 
                    block 
                    icon={<HeartFilled />}
                    onClick={() => navigate('/wiki/bookmarks')}
                  >
                    Meus Favoritos
                  </Button>
                  <Button 
                    block 
                    icon={<SearchOutlined />}
                    onClick={() => navigate('/wiki/search')}
                  >
                    Busca Avançada
                  </Button>
                </Space>
              </Card>
            </Space>
          </Col>
        </Row>
      </Content>
    </Layout>
  );
};

export default WikiDashboard; 