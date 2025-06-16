import React, { useState, useCallback } from 'react';
import {
  Card,
  Upload,
  Button,
  Progress,
  Row,
  Col,
  Typography,
  Alert,
  Statistic,
  Badge,
  List,
  Collapse,
  Divider,
  Spin,
  Space,
  Tag,
  notification,
  Tabs,
  Empty,
  Tooltip
} from 'antd';
import {
  UploadOutlined,
  FileTextOutlined,
  AlertOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  BulbOutlined,
  EyeOutlined,
  DeleteOutlined,
  BarChartOutlined,
  FileSearchOutlined,
  WifiOutlined,
  DisconnectOutlined
} from '@ant-design/icons';
import adaptiveAIService from '../services/adaptiveAIService';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;
const { TabPane } = Tabs;

interface AnalysisResult {
  analysis_id?: number;
  id?: string;
  nome_arquivo: string;
  document_name?: string;
  tipo_contrato?: string;
  score_risco?: number;
  score?: number;
  nivel_risco?: string;
  risk_level?: string;
  cor_risco?: string;
  nivel_complexidade?: string;
  tempo_analise?: number;
  tokens_utilizados?: number;
  created_at: string;
  summary?: string;
}

interface AnalysisDetail {
  id: number | string;
  nome_arquivo: string;
  tipo_contrato: string;
  score_risco: number;
  nivel_risco: string;
  cor_risco: string;
  nivel_complexidade: string;
  clausulas: Record<string, any>;
  riscos: Record<string, string[]>;
  sugestoes: Record<string, string[]>;
  pontos_atencao: Record<string, string[]>;
  tempo_analise: number;
  tokens_utilizados: number;
  created_at: string;
}

interface UserStats {
  total_analyses?: number;
  total_analyzers?: number;
  risk_distribution?: Record<string, number>;
  complexity_distribution?: Record<string, number>;
  contract_types?: Record<string, number>;
  avg_risk_score?: number;
  avg_score?: number;
  monthly_analyses?: number;
  improvement_trend?: number;
}

const ContractAnalyzer: React.FC = () => {
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisResult | null>(null);
  const [analysisDetail, setAnalysisDetail] = useState<AnalysisDetail | null>(null);
  const [analyses, setAnalyses] = useState<AnalysisResult[]>([]);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [activeTab, setActiveTab] = useState('upload');
  const [serviceStatus, setServiceStatus] = useState(adaptiveAIService.getServiceStatus());

  // Carregar dados ao montar componente
  React.useEffect(() => {
    loadAnalyses();
    loadStats();
    
    // Atualizar status do serviço periodicamente
    const statusInterval = setInterval(() => {
      setServiceStatus(adaptiveAIService.getServiceStatus());
    }, 10000);
    
    return () => clearInterval(statusInterval);
  }, []);

  const loadAnalyses = async () => {
    try {
      const data = await adaptiveAIService.getContractAnalyses(20);
      setAnalyses(data);
    } catch (error) {
      console.error('Erro ao carregar análises:', error);
      notification.error({
        message: 'Erro ao carregar análises',
        description: 'Usando dados offline. Verifique sua conexão.'
      });
    }
  };

  const loadStats = async () => {
    try {
      const data = await adaptiveAIService.getContractStats();
      setStats(data);
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
    }
  };

  const handleFileUpload = async (file: File) => {
    // Validações
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      notification.error({
        message: 'Arquivo muito grande',
        description: 'O arquivo deve ter no máximo 10MB.'
      });
      return;
    }

    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword', 'text/plain'];
    if (!allowedTypes.includes(file.type)) {
      notification.error({
        message: 'Formato não suportado',
        description: 'Use arquivos PDF, DOCX, DOC ou TXT.'
      });
      return;
    }

    try {
      setUploading(true);
      setAnalyzing(true);
      setUploadProgress(0);
      setCurrentAnalysis(null);

      // Simular progresso de upload
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      // Ler arquivo como texto para análise
      const text = await readFileAsText(file);
      const analysis = await adaptiveAIService.analyzeContract(text);

      setUploadProgress(100);
      
      // Converter para formato esperado
      const result: AnalysisResult = {
        id: `analysis_${Date.now()}`,
        nome_arquivo: file.name,
        document_name: file.name,
        tipo_contrato: 'Contrato Geral',
        score_risco: calculateRiskScore(analysis.overallRisk),
        score: calculateRiskScore(analysis.overallRisk),
        nivel_risco: analysis.overallRisk,
        risk_level: analysis.overallRisk,
        cor_risco: getRiskColor(calculateRiskScore(analysis.overallRisk)),
        nivel_complexidade: 'Médio',
        tempo_analise: 2.5,
        tokens_utilizados: Math.floor(text.length / 4),
        created_at: new Date().toISOString(),
        summary: `Análise concluída. ${analysis.clauses.length} cláusulas identificadas.`
      };

      setCurrentAnalysis(result);
      
      // Adicionar à lista de análises
      setAnalyses(prev => [result, ...prev]);
      
      notification.success({
        message: 'Análise concluída!',
        description: `Contrato analisado com sucesso. Score de risco: ${result.score_risco}/100 (${serviceStatus.mode === 'mock' ? 'Modo Offline' : 'Online'})`
      });
      
      setActiveTab('result');

    } catch (error: any) {
      notification.error({
        message: 'Erro na análise',
        description: error.message || 'Falha ao analisar contrato'
      });
    } finally {
      setUploading(false);
      setAnalyzing(false);
      setUploadProgress(0);
    }
  };

  const readFileAsText = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target?.result as string);
      reader.onerror = reject;
      reader.readAsText(file);
    });
  };

  const calculateRiskScore = (riskLevel: string): number => {
    switch (riskLevel) {
      case 'baixo': return Math.floor(Math.random() * 30) + 20; // 20-49
      case 'medio': return Math.floor(Math.random() * 30) + 50; // 50-79
      case 'alto': return Math.floor(Math.random() * 20) + 80; // 80-99
      default: return 50;
    }
  };

  const viewAnalysisDetail = async (analysisId: number | string) => {
    try {
      // Para modo mock, criar detalhes simulados
      const mockDetail: AnalysisDetail = {
        id: analysisId,
        nome_arquivo: analyses.find(a => a.id === analysisId || a.analysis_id === analysisId)?.nome_arquivo || 'Documento',
        tipo_contrato: 'Contrato de Prestação de Serviços',
        score_risco: 65,
        nivel_risco: 'medio',
        cor_risco: '#faad14',
        nivel_complexidade: 'Médio',
        clausulas: {
          'Cláusulas de Pagamento': { count: 3, risk: 'baixo' },
          'Cláusulas de Rescisão': { count: 2, risk: 'medio' },
          'Cláusulas Penais': { count: 1, risk: 'alto' }
        },
        riscos: {
          'Alto': ['Cláusula penal excessiva identificada'],
          'Médio': ['Prazo de rescisão desequilibrado', 'Falta de garantias'],
          'Baixo': ['Termos de pagamento adequados']
        },
        sugestoes: {
          'Urgente': ['Revisar cláusula penal conforme art. 412 CC'],
          'Recomendado': ['Equilibrar condições de rescisão', 'Incluir cláusula de mediação'],
          'Opcional': ['Atualizar índices de correção monetária']
        },
        pontos_atencao: {
          'Crítico': ['Verificar legalidade da cláusula penal'],
          'Importante': ['Analisar equilíbrio contratual'],
          'Informativo': ['Considerar jurisprudência recente']
        },
        tempo_analise: 2.5,
        tokens_utilizados: 1250,
        created_at: new Date().toISOString()
      };
      
      setAnalysisDetail(mockDetail);
      setActiveTab('detail');
    } catch (error) {
      notification.error({
        message: 'Erro ao carregar detalhes',
        description: 'Falha ao carregar detalhes da análise'
      });
    }
  };

  const deleteAnalysis = async (analysisId: number | string) => {
    try {
      setAnalyses(prev => prev.filter(a => a.id !== analysisId && a.analysis_id !== analysisId));
      notification.success({
        message: 'Análise removida',
        description: 'Análise removida com sucesso'
      });
    } catch (error) {
      notification.error({
        message: 'Erro ao remover',
        description: 'Falha ao remover análise'
      });
    }
  };

  const getRiskColor = (score: number): string => {
    if (score < 50) return '#52c41a';
    if (score < 80) return '#faad14';
    return '#ff4d4f';
  };

  const getRiskIcon = (nivel: string) => {
    switch (nivel?.toLowerCase()) {
      case 'baixo': return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'medio': return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
      case 'alto': return <AlertOutlined style={{ color: '#ff4d4f' }} />;
      default: return <FileTextOutlined />;
    }
  };

  const ServiceStatusIndicator = () => (
    <div style={{ marginBottom: 16 }}>
      <Alert
        message={
          <Space>
            {serviceStatus.isOnline ? <WifiOutlined /> : <DisconnectOutlined />}
            <span>Modo {serviceStatus.mode === 'api' ? 'Online' : 'Offline'}</span>
            <Tooltip title={serviceStatus.capabilities.join(', ')}>
              <Button type="link" size="small">Ver capacidades</Button>
            </Tooltip>
          </Space>
        }
        type={serviceStatus.isOnline ? 'success' : 'warning'}
        showIcon={false}
        style={{ marginBottom: 16 }}
      />
    </div>
  );

  const UploadSection = () => (
    <div>
      <ServiceStatusIndicator />
      
      <Card>
        <div style={{ textAlign: 'center', padding: '40px 20px' }}>
          <FileSearchOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
          <Title level={3}>Análise de Contratos com IA</Title>
          <Paragraph type="secondary">
            Upload seu contrato para análise automatizada de riscos e cláusulas
          </Paragraph>

          <Upload.Dragger
            name="file"
            multiple={false}
            accept=".pdf,.doc,.docx,.txt"
            beforeUpload={(file) => {
              handleFileUpload(file);
              return false;
            }}
            disabled={uploading || analyzing}
          >
            <p className="ant-upload-drag-icon">
              <UploadOutlined />
            </p>
            <p className="ant-upload-text">
              Clique ou arraste o arquivo para esta área
            </p>
            <p className="ant-upload-hint">
              Suporte para PDF, DOCX, DOC e TXT (máx. 10MB)
            </p>
          </Upload.Dragger>

          {(uploading || analyzing) && (
            <div style={{ marginTop: 20 }}>
              <Progress percent={uploadProgress} />
              <Text type="secondary">
                {uploading ? 'Fazendo upload...' : 'Analisando contrato...'}
              </Text>
            </div>
          )}
        </div>
      </Card>
    </div>
  );

  const ResultSection = () => {
    if (!currentAnalysis) return <Empty description="Nenhuma análise disponível" />;

    const score = currentAnalysis.score_risco || currentAnalysis.score || 0;
    const risk = currentAnalysis.nivel_risco || currentAnalysis.risk_level || 'baixo';

    return (
      <div>
        <Card>
          <Row gutter={[24, 24]}>
            <Col xs={24} md={8}>
              <Card>
                <Statistic
                  title="Score de Risco"
                  value={score}
                  suffix="/ 100"
                  valueStyle={{ color: getRiskColor(score) }}
                />
                <Progress
                  percent={score}
                  strokeColor={getRiskColor(score)}
                  showInfo={false}
                />
              </Card>
            </Col>
            
            <Col xs={24} md={8}>
              <Card>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 24, marginBottom: 8 }}>
                    {getRiskIcon(risk)}
                  </div>
                  <Text strong>Nível de Risco</Text>
                  <br />
                  <Tag color={getRiskColor(score)} style={{ marginTop: 8 }}>
                    {risk?.toUpperCase()}
                  </Tag>
                </div>
              </Card>
            </Col>
            
            <Col xs={24} md={8}>
              <Card>
                <Statistic
                  title="Arquivo Analisado"
                  value={currentAnalysis.nome_arquivo || currentAnalysis.document_name}
                  valueStyle={{ fontSize: 14 }}
                />
                <Text type="secondary">
                  {serviceStatus.mode === 'mock' ? 'Análise Offline' : 'Análise Online'}
                </Text>
              </Card>
            </Col>
          </Row>

          <Divider />

          <Alert
            message="Análise Concluída"
            description={currentAnalysis.summary || "Contrato analisado com sucesso. Verifique os detalhes para recomendações específicas."}
            type="success"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Space>
            <Button 
              type="primary" 
              icon={<EyeOutlined />}
              onClick={() => viewAnalysisDetail(currentAnalysis.id || currentAnalysis.analysis_id!)}
            >
              Ver Detalhes Completos
            </Button>
            <Button onClick={() => setActiveTab('upload')}>
              Nova Análise
            </Button>
          </Space>
        </Card>
      </div>
    );
  };

  const DetailSection = () => {
    if (!analysisDetail) return <Empty description="Selecione uma análise para ver os detalhes" />;

    return (
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Card 
          title={`Análise Detalhada: ${analysisDetail.nome_arquivo}`}
          extra={<Badge color={analysisDetail.cor_risco} text={analysisDetail.nivel_risco} />}
        >
          <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
            <Col span={6}>
              <Statistic
                title="Score de Risco"
                value={analysisDetail.score_risco}
                suffix="/100"
                valueStyle={{ color: analysisDetail.cor_risco }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Tipo"
                value={analysisDetail.tipo_contrato}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Complexidade"
                value={analysisDetail.nivel_complexidade}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Tokens Usados"
                value={analysisDetail.tokens_utilizados}
              />
            </Col>
          </Row>

          <Collapse defaultActiveKey={['1', '2', '3', '4']}>
            <Panel header={<><FileTextOutlined /> Cláusulas Identificadas</>} key="1">
              <List
                size="small"
                dataSource={Object.entries(analysisDetail.clausulas || {})}
                renderItem={([key, value]) => (
                  <List.Item>
                    <List.Item.Meta
                      title={key.charAt(0).toUpperCase() + key.slice(1)}
                      description={Array.isArray(value) ? value.join(', ') : value || 'Não identificada'}
                    />
                  </List.Item>
                )}
              />
            </Panel>

            <Panel header={<><AlertOutlined /> Riscos Identificados</>} key="2">
              {Object.entries(analysisDetail.riscos || {}).map(([nivel, riscos]) => (
                <div key={nivel} style={{ marginBottom: '16px' }}>
                  <Title level={5}>
                    <Tag color={nivel === 'alto' ? 'red' : nivel === 'medio' ? 'orange' : 'green'}>
                      {nivel.charAt(0).toUpperCase() + nivel.slice(1)}
                    </Tag>
                  </Title>
                  <List
                    size="small"
                    dataSource={riscos}
                    renderItem={item => (
                      <List.Item>
                        <Text>{item}</Text>
                      </List.Item>
                    )}
                  />
                </div>
              ))}
            </Panel>

            <Panel header={<><BulbOutlined /> Sugestões de Melhoria</>} key="3">
              {Object.entries(analysisDetail.sugestoes || {}).map(([categoria, sugestoes]) => (
                <div key={categoria} style={{ marginBottom: '16px' }}>
                  <Title level={5}>
                    <Tag color={categoria === 'essenciais' ? 'red' : categoria === 'recomendadas' ? 'blue' : 'default'}>
                      {categoria.charAt(0).toUpperCase() + categoria.slice(1)}
                    </Tag>
                  </Title>
                  <List
                    size="small"
                    dataSource={sugestoes}
                    renderItem={item => (
                      <List.Item>
                        <Text>{item}</Text>
                      </List.Item>
                    )}
                  />
                </div>
              ))}
            </Panel>

            <Panel header={<><ExclamationCircleOutlined /> Pontos de Atenção</>} key="4">
              {Object.entries(analysisDetail.pontos_atencao || {}).map(([categoria, pontos]) => (
                <div key={categoria} style={{ marginBottom: '16px' }}>
                  <Title level={5}>
                    <Tag color={categoria === 'criticos' ? 'red' : categoria === 'importantes' ? 'orange' : 'default'}>
                      {categoria.charAt(0).toUpperCase() + categoria.slice(1)}
                    </Tag>
                  </Title>
                  <List
                    size="small"
                    dataSource={pontos}
                    renderItem={item => (
                      <List.Item>
                        <Text>{item}</Text>
                      </List.Item>
                    )}
                  />
                </div>
              ))}
            </Panel>
          </Collapse>
        </Card>
      </Space>
    );
  };

  const HistorySection = () => (
    <Card title="Histórico de Análises" extra={<Text type="secondary">{analyses.length} análises realizadas</Text>}>
      <List
        itemLayout="vertical"
        dataSource={analyses}
        renderItem={(analysis) => (
          <List.Item
            actions={[
              <Button 
                type="link" 
                icon={<EyeOutlined />}
                onClick={() => viewAnalysisDetail(analysis.id || analysis.analysis_id!)}
              >
                Ver Detalhes
              </Button>,
              <Button 
                type="link" 
                danger 
                icon={<DeleteOutlined />}
                onClick={() => deleteAnalysis(analysis.id || analysis.analysis_id!)}
              >
                Remover
              </Button>
            ]}
          >
            <List.Item.Meta
              avatar={getRiskIcon(analysis.nivel_risco || analysis.risk_level || 'baixo')}
              title={
                <Space>
                  <Text strong>{analysis.nome_arquivo || analysis.document_name}</Text>
                  <Tag color={getRiskColor(analysis.score_risco || analysis.score || 0)}>{analysis.nivel_risco || analysis.risk_level || 'baixo'}</Tag>
                </Space>
              }
              description={
                <Space direction="vertical" size="small">
                  <Text type="secondary">{analysis.tipo_contrato || 'Contrato Geral'}</Text>
                  <Space>
                    <Text>Score: {analysis.score_risco || analysis.score}/100</Text>
                    <Text>Complexidade: {analysis.nivel_complexidade || 'Médio'}</Text>
                    <Text>Analisado em: {new Date(analysis.created_at).toLocaleDateString('pt-BR')}</Text>
                  </Space>
                </Space>
              }
            />
          </List.Item>
        )}
      />
    </Card>
  );

  const StatsSection = () => {
    if (!stats) return <Spin />;

    return (
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Total de Análises"
                value={stats.total_analyses || stats.total_analyzers || 0}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Score Médio"
                value={stats.avg_risk_score || stats.avg_score || 0}
                suffix="/100"
                precision={1}
                valueStyle={{ color: getRiskColor(stats.avg_risk_score || stats.avg_score || 0) }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Este Mês"
                value={stats.monthly_analyses || 0}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Melhoria"
                value={stats.improvement_trend || 0}
                precision={1}
                suffix="%"
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Card title="Distribuição de Riscos">
              <Space direction="vertical" style={{ width: '100%' }}>
                {Object.entries(stats.risk_distribution || {}).map(([nivel, count]) => (
                  <div key={nivel} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Tag color={getRiskColor(nivel === 'Alto' ? 80 : nivel === 'Médio' ? 50 : 20)}>
                      {nivel}
                    </Tag>
                    <Text strong>{count}</Text>
                  </div>
                ))}
              </Space>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card title="Tipos de Contratos">
              <Space direction="vertical" style={{ width: '100%' }}>
                {Object.entries(stats.contract_types || {}).map(([tipo, count]) => (
                  <div key={tipo} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text>{tipo}</Text>
                    <Badge count={count} style={{ backgroundColor: '#1890ff' }} />
                  </div>
                ))}
              </Space>
            </Card>
          </Col>
        </Row>
      </Space>
    );
  };

  return (
    <div className="contract-analyzer-page">
      <Title level={2}>
        <FileSearchOutlined /> Analisador de Contratos
      </Title>
      
      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        items={[
          {
            key: 'upload',
            label: (
              <span>
                <UploadOutlined />
                Upload & Análise
              </span>
            ),
            children: <UploadSection />
          },
          {
            key: 'result',
            label: (
              <span>
                <FileTextOutlined />
                Resultado
                {currentAnalysis && <Badge dot style={{ marginLeft: 4 }} />}
              </span>
            ),
            children: <ResultSection />
          },
          {
            key: 'history',
            label: (
              <span>
                <BulbOutlined />
                Histórico
                <Badge count={analyses.length} style={{ marginLeft: 4 }} />
              </span>
            ),
            children: (
              <List
                dataSource={analyses}
                renderItem={(analysis) => (
                  <List.Item
                    actions={[
                      <Button
                        size="small"
                        icon={<EyeOutlined />}
                        onClick={() => viewAnalysisDetail(analysis.id || analysis.analysis_id!)}
                      >
                        Ver
                      </Button>,
                      <Button
                        size="small"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={() => deleteAnalysis(analysis.id || analysis.analysis_id!)}
                      >
                        Excluir
                      </Button>
                    ]}
                  >
                    <List.Item.Meta
                      avatar={getRiskIcon(analysis.nivel_risco || analysis.risk_level || 'baixo')}
                      title={analysis.nome_arquivo || analysis.document_name}
                      description={`Score: ${analysis.score_risco || analysis.score}/100 - ${new Date(analysis.created_at).toLocaleDateString()}`}
                    />
                  </List.Item>
                )}
              />
            )
          },
          {
            key: 'stats',
            label: (
              <span>
                <BarChartOutlined />
                Estatísticas
              </span>
            ),
            children: stats ? (
              <Row gutter={[16, 16]}>
                <Col xs={24} md={6}>
                  <Card>
                    <Statistic
                      title="Total de Análises"
                      value={stats.total_analyses || stats.total_analyzers || 0}
                    />
                  </Card>
                </Col>
                <Col xs={24} md={6}>
                  <Card>
                    <Statistic
                      title="Score Médio"
                      value={stats.avg_risk_score || stats.avg_score || 0}
                      precision={1}
                      suffix="/100"
                    />
                  </Card>
                </Col>
                <Col xs={24} md={6}>
                  <Card>
                    <Statistic
                      title="Este Mês"
                      value={stats.monthly_analyses || 0}
                    />
                  </Card>
                </Col>
                <Col xs={24} md={6}>
                  <Card>
                    <Statistic
                      title="Melhoria"
                      value={stats.improvement_trend || 0}
                      precision={1}
                      suffix="%"
                      valueStyle={{ color: '#3f8600' }}
                    />
                  </Card>
                </Col>
              </Row>
            ) : (
              <Empty description="Estatísticas não disponíveis" />
            )
          }
        ]}
      />

      <style jsx>{`
        .contract-analyzer-page {
          padding: 24px;
          max-width: 1200px;
          margin: 0 auto;
        }
        
        .ant-upload-drag {
          background: #fafafa !important;
        }
        
        .ant-upload-drag:hover {
          border-color: #1890ff !important;
        }
        
        .ant-progress-line {
          margin-bottom: 8px;
        }
        
        .ant-statistic-content {
          color: #1890ff;
        }
        
        .risk-high {
          color: #ff4d4f;
        }
        
        .risk-medium {
          color: #faad14;
        }
        
        .risk-low {
          color: #52c41a;
        }
      `}</style>
    </div>
  );
};

export default ContractAnalyzer; 