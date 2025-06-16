import React, { useState, useEffect } from 'react';
import {
  Layout,
  Card,
  Row,
  Col,
  Typography,
  Statistic,
  Select,
  DatePicker,
  Button,
  Space,
  Progress,
  Badge,
  Tooltip,
  Table,
  Tag,
  Divider,
  Empty,
  Spin,
  Alert,
  Tabs
} from 'antd';
import {
  TrophyOutlined,
  RiseOutlined,
  FallOutlined,
  DownloadOutlined,
  ReloadOutlined,
  CalendarOutlined,
  ClockCircleOutlined,
  UserOutlined,
  FileTextOutlined,
  BulbOutlined,
  BookOutlined,
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  HeatMapOutlined
} from '@ant-design/icons';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend
} from 'recharts';
import axios from 'axios';
import dayjs from 'dayjs';
import './AnalyticsDashboard.css';

const { Content } = Layout;
const { Title, Text } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;
const { TabPane } = Tabs;

interface DashboardMetrics {
  period: {
    start_date: string;
    end_date: string;
    range: string;
  };
  documents: {
    created: number;
    updated: number;
    total: number;
    by_type: Array<{ type: string; count: number }>;
    avg_size_kb: number;
    growth_rate: number;
  };
  kanban: {
    boards: number;
    cards_created: number;
    cards_completed: number;
    completion_rate: number;
    total_hours: number;
    billable_hours: number;
    productivity_score: number;
  };
  wiki: {
    articles_created: number;
    total_views: number;
    likes_received: number;
    comments_made: number;
    most_popular_article?: {
      title: string;
      views: number;
      likes: number;
    };
    engagement_score: number;
  };
  ai_usage: {
    total_requests: number;
    by_type: Array<{ type: string; count: number }>;
    total_tokens: number;
    avg_response_time_ms: number;
    success_rate: number;
    efficiency_score: number;
  };
  productivity: {
    weekday_pattern: Array<{ day: string; activity_count: number }>;
    hourly_pattern: Array<{ hour: number; activity_count: number }>;
    activity_streak: number;
    productivity_score: number;
    achievements: Array<{
      id: string;
      title: string;
      description: string;
      icon: string;
      earned_at: string;
    }>;
    recommendations: Array<{
      id: string;
      title: string;
      description: string;
      priority: string;
      category: string;
    }>;
  };
  notifications: {
    total_received: number;
    total_read: number;
    read_rate: number;
    by_type: Array<{ type: string; count: number }>;
    avg_read_time_minutes: number;
  };
}

const COLORS = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2', '#eb2f96', '#fa8c16'];

const AnalyticsDashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState('30days');
  const [activeTab, setActiveTab] = useState('overview');
  const [chartsData, setChartsData] = useState<any>({});
  const [error, setError] = useState<string | null>(null);

  // Carregar dados do dashboard
  useEffect(() => {
    loadDashboardData();
  }, [selectedPeriod]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [overviewRes, chartsRes] = await Promise.all([
        axios.get(`/api/analytics/dashboard/overview?range=${selectedPeriod}`),
        loadChartsData()
      ]);

      setMetrics(overviewRes.data.data);
      
    } catch (error: any) {
      console.error('Erro ao carregar dados:', error);
      setError('Erro ao carregar dados do dashboard');
    } finally {
      setLoading(false);
    }
  };

  const loadChartsData = async () => {
    try {
      const [
        timelineRes,
        progressRes,
        engagementRes,
        trendsRes,
        heatmapRes
      ] = await Promise.all([
        axios.get(`/api/analytics/charts/documents_timeline?period=${selectedPeriod}`),
        axios.get(`/api/analytics/charts/kanban_progress?period=${selectedPeriod}`),
        axios.get(`/api/analytics/charts/wiki_engagement?period=${selectedPeriod}`),
        axios.get(`/api/analytics/charts/ai_usage_trends?period=${selectedPeriod}`),
        axios.get(`/api/analytics/charts/productivity_heatmap?period=${selectedPeriod}`)
      ]);

      setChartsData({
        timeline: timelineRes.data.data,
        progress: progressRes.data.data,
        engagement: engagementRes.data.data,
        trends: trendsRes.data.data,
        heatmap: heatmapRes.data.data
      });

    } catch (error) {
      console.error('Erro ao carregar gráficos:', error);
    }
  };

  const exportData = async (format: string) => {
    try {
      const response = await axios.post('/api/analytics/export', {
        type: format,
        categories: ['documents', 'kanban', 'wiki', 'ai', 'productivity'],
        period: selectedPeriod
      });

      // Simular download
      const link = document.createElement('a');
      link.href = response.data.data.download_url;
      link.download = response.data.data.filename;
      link.click();

    } catch (error) {
      console.error('Erro ao exportar dados:', error);
    }
  };

  // Renderizar card de métrica principal
  const renderMetricCard = (
    title: string,
    value: number | string,
    suffix?: string,
    prefix?: React.ReactNode,
    trend?: number,
    color?: string
  ) => (
    <Card>
      <Statistic
        title={title}
        value={value}
        suffix={suffix}
        prefix={prefix}
        valueStyle={{ color: color || '#1890ff' }}
      />
      {trend !== undefined && (
        <div style={{ marginTop: '8px' }}>
          <Text type={trend > 0 ? 'success' : trend < 0 ? 'danger' : 'secondary'}>
            {trend > 0 ? <RiseOutlined /> : trend < 0 ? <FallOutlined /> : null}
            {trend > 0 ? '+' : ''}{trend.toFixed(1)}%
          </Text>
          <Text type="secondary" style={{ marginLeft: '8px' }}>
            vs período anterior
          </Text>
        </div>
      )}
    </Card>
  );

  // Renderizar gráfico de linha
  const renderLineChart = (data: any[], dataKey: string, title: string, color: string = '#1890ff') => (
    <Card title={title}>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <RechartsTooltip />
          <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );

  // Renderizar gráfico de barras
  const renderBarChart = (data: any[], dataKey: string, title: string, color: string = '#1890ff') => (
    <Card title={title}>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <RechartsTooltip />
          <Bar dataKey={dataKey} fill={color} />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );

  // Renderizar gráfico de pizza
  const renderPieChart = (data: any[], title: string) => (
    <Card title={title}>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <RechartsTooltip />
        </PieChart>
      </ResponsiveContainer>
    </Card>
  );

  if (loading) {
    return (
      <Layout className="analytics-dashboard">
        <Content style={{ padding: '24px' }}>
          <div style={{ textAlign: 'center', padding: '100px' }}>
            <Spin size="large" />
            <div style={{ marginTop: '16px' }}>
              <Text>Carregando analytics...</Text>
            </div>
          </div>
        </Content>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout className="analytics-dashboard">
        <Content style={{ padding: '24px' }}>
          <Alert
            message="Erro ao carregar dados"
            description={error}
            type="error"
            showIcon
            action={
              <Button size="small" onClick={loadDashboardData}>
                Tentar novamente
              </Button>
            }
          />
        </Content>
      </Layout>
    );
  }

  if (!metrics) {
    return (
      <Layout className="analytics-dashboard">
        <Content style={{ padding: '24px' }}>
          <Empty description="Nenhum dado disponível" />
        </Content>
      </Layout>
    );
  }

  return (
    <Layout className="analytics-dashboard">
      <Content style={{ padding: '24px' }}>
        {/* Header */}
        <div className="dashboard-header">
          <Row justify="space-between" align="middle">
            <Col>
              <Title level={2} style={{ margin: 0 }}>
                📊 Analytics Dashboard
              </Title>
              <Text type="secondary">
                Análise detalhada da sua produtividade e atividades
              </Text>
            </Col>
            <Col>
              <Space>
                <Select
                  value={selectedPeriod}
                  onChange={setSelectedPeriod}
                  style={{ width: 120 }}
                >
                  <Option value="7days">7 dias</Option>
                  <Option value="30days">30 dias</Option>
                  <Option value="90days">90 dias</Option>
                  <Option value="1year">1 ano</Option>
                </Select>
                <Button icon={<ReloadOutlined />} onClick={loadDashboardData}>
                  Atualizar
                </Button>
                <Button 
                  icon={<DownloadOutlined />} 
                  onClick={() => exportData('csv')}
                >
                  Exportar
                </Button>
              </Space>
            </Col>
          </Row>
        </div>

        <Tabs activeKey={activeTab} onChange={setActiveTab} size="large">
          {/* Visão Geral */}
          <TabPane tab={<span><BarChartOutlined />Visão Geral</span>} key="overview">
            {/* KPIs Principais */}
            <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
              <Col xs={12} sm={8} lg={6}>
                {renderMetricCard(
                  'Score de Produtividade',
                  metrics.productivity.productivity_score,
                  '%',
                  <TrophyOutlined />,
                  5.2,
                  '#52c41a'
                )}
              </Col>
              <Col xs={12} sm={8} lg={6}>
                {renderMetricCard(
                  'Documentos Criados',
                  metrics.documents.created,
                  undefined,
                  <FileTextOutlined />,
                  metrics.documents.growth_rate
                )}
              </Col>
              <Col xs={12} sm={8} lg={6}>
                {renderMetricCard(
                  'Tarefas Completadas',
                  metrics.kanban.cards_completed,
                  undefined,
                  <UserOutlined />,
                  undefined,
                  '#faad14'
                )}
              </Col>
              <Col xs={12} sm={8} lg={6}>
                {renderMetricCard(
                  'Artigos Publicados',
                  metrics.wiki.articles_created,
                  undefined,
                  <BookOutlined />,
                  undefined,
                  '#722ed1'
                )}
              </Col>
            </Row>

            {/* Gráficos Principais */}
            <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
              <Col xs={24} lg={12}>
                {renderLineChart(
                  chartsData.timeline || [],
                  'documents',
                  'Timeline de Documentos',
                  '#1890ff'
                )}
              </Col>
              <Col xs={24} lg={12}>
                {renderBarChart(
                  metrics.kanban.cards_created > 0 ? [
                    { name: 'Criadas', value: metrics.kanban.cards_created },
                    { name: 'Completadas', value: metrics.kanban.cards_completed }
                  ] : [],
                  'value',
                  'Kanban - Tarefas',
                  '#52c41a'
                )}
              </Col>
            </Row>

            {/* Cards de Detalhes */}
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={8}>
                <Card title="⏱️ Gestão de Tempo" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text type="secondary">Horas Trabalhadas</Text>
                      <div>
                        <Text strong>{metrics.kanban.total_hours}h</Text>
                      </div>
                    </div>
                    <div>
                      <Text type="secondary">Horas Faturáveis</Text>
                      <div>
                        <Text strong style={{ color: '#52c41a' }}>
                          {metrics.kanban.billable_hours}h
                        </Text>
                      </div>
                    </div>
                    <Progress
                      percent={Math.round(
                        (metrics.kanban.billable_hours / metrics.kanban.total_hours) * 100
                      )}
                      status="active"
                      strokeColor="#52c41a"
                    />
                  </Space>
                </Card>
              </Col>

              <Col xs={24} lg={8}>
                <Card title="🤖 Uso da IA" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text type="secondary">Requests Totais</Text>
                      <div>
                        <Text strong>{metrics.ai_usage.total_requests}</Text>
                      </div>
                    </div>
                    <div>
                      <Text type="secondary">Taxa de Sucesso</Text>
                      <div>
                        <Text strong style={{ color: '#1890ff' }}>
                          {metrics.ai_usage.success_rate}%
                        </Text>
                      </div>
                    </div>
                    <div>
                      <Text type="secondary">Tempo Médio de Resposta</Text>
                      <div>
                        <Text strong>{metrics.ai_usage.avg_response_time_ms}ms</Text>
                      </div>
                    </div>
                  </Space>
                </Card>
              </Col>

              <Col xs={24} lg={8}>
                <Card title="📚 Engajamento Wiki" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text type="secondary">Visualizações</Text>
                      <div>
                        <Text strong>{metrics.wiki.total_views}</Text>
                      </div>
                    </div>
                    <div>
                      <Text type="secondary">Curtidas Recebidas</Text>
                      <div>
                        <Text strong style={{ color: '#eb2f96' }}>
                          {metrics.wiki.likes_received}
                        </Text>
                      </div>
                    </div>
                    <div>
                      <Text type="secondary">Score de Engajamento</Text>
                      <div>
                        <Progress
                          percent={metrics.wiki.engagement_score}
                          status="active"
                          strokeColor="#722ed1"
                          size="small"
                        />
                      </div>
                    </div>
                  </Space>
                </Card>
              </Col>
            </Row>
          </TabPane>

          {/* Produtividade */}
          <TabPane tab={<span><TrophyOutlined />Produtividade</span>} key="productivity">
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={16}>
                <Card title="📈 Padrão de Atividade Semanal">
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={metrics.productivity.weekday_pattern}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="day" />
                      <YAxis />
                      <RechartsTooltip />
                      <Bar dataKey="activity_count" fill="#1890ff" />
                    </BarChart>
                  </ResponsiveContainer>
                </Card>
              </Col>
              
              <Col xs={24} lg={8}>
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                  <Card title="🏆 Conquistas Recentes" size="small">
                    {metrics.productivity.achievements.length > 0 ? (
                      <Space direction="vertical" style={{ width: '100%' }}>
                        {metrics.productivity.achievements.map(achievement => (
                          <div key={achievement.id} className="achievement-item">
                            <Space>
                              <span style={{ fontSize: '20px' }}>{achievement.icon}</span>
                              <div>
                                <div>
                                  <Text strong>{achievement.title}</Text>
                                </div>
                                <div>
                                  <Text type="secondary" style={{ fontSize: '12px' }}>
                                    {achievement.description}
                                  </Text>
                                </div>
                              </div>
                            </Space>
                          </div>
                        ))}
                      </Space>
                    ) : (
                      <Empty description="Nenhuma conquista recente" size="small" />
                    )}
                  </Card>

                  <Card title="💡 Recomendações" size="small">
                    {metrics.productivity.recommendations.length > 0 ? (
                      <Space direction="vertical" style={{ width: '100%' }}>
                        {metrics.productivity.recommendations.map(rec => (
                          <div key={rec.id} className="recommendation-item">
                            <div>
                              <Text strong>{rec.title}</Text>
                              <Tag 
                                size="small" 
                                color={rec.priority === 'high' ? 'red' : rec.priority === 'medium' ? 'orange' : 'blue'}
                                style={{ marginLeft: '8px' }}
                              >
                                {rec.priority}
                              </Tag>
                            </div>
                            <div>
                              <Text type="secondary" style={{ fontSize: '12px' }}>
                                {rec.description}
                              </Text>
                            </div>
                          </div>
                        ))}
                      </Space>
                    ) : (
                      <Empty description="Nenhuma recomendação" size="small" />
                    )}
                  </Card>
                </Space>
              </Col>
            </Row>
          </TabPane>

          {/* Detalhamento */}
          <TabPane tab={<span><PieChartOutlined />Detalhamento</span>} key="details">
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={12}>
                {renderPieChart(
                  metrics.documents.by_type.map(item => ({
                    name: item.type,
                    value: item.count
                  })),
                  'Documentos por Tipo'
                )}
              </Col>
              
              <Col xs={24} lg={12}>
                {renderPieChart(
                  metrics.ai_usage.by_type.map(item => ({
                    name: item.type,
                    value: item.count
                  })),
                  'Uso da IA por Tipo'
                )}
              </Col>
            </Row>

            <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
              <Col xs={24}>
                <Card title="📊 Resumo Detalhado">
                  <Row gutter={[16, 16]}>
                    <Col xs={24} sm={12} lg={6}>
                      <Statistic
                        title="Sequência de Atividade"
                        value={metrics.productivity.activity_streak}
                        suffix="dias"
                        prefix={<ClockCircleOutlined />}
                      />
                    </Col>
                    <Col xs={24} sm={12} lg={6}>
                      <Statistic
                        title="Taxa de Conclusão"
                        value={metrics.kanban.completion_rate}
                        suffix="%"
                        precision={1}
                        valueStyle={{ color: '#52c41a' }}
                      />
                    </Col>
                    <Col xs={24} sm={12} lg={6}>
                      <Statistic
                        title="Tokens IA Consumidos"
                        value={metrics.ai_usage.total_tokens}
                        prefix={<BulbOutlined />}
                      />
                    </Col>
                    <Col xs={24} sm={12} lg={6}>
                      <Statistic
                        title="Taxa de Leitura"
                        value={metrics.notifications.read_rate}
                        suffix="%"
                        precision={1}
                        valueStyle={{ color: '#1890ff' }}
                      />
                    </Col>
                  </Row>
                </Card>
              </Col>
            </Row>
          </TabPane>
        </Tabs>
      </Content>
    </Layout>
  );
};

export default AnalyticsDashboard; 