import React from 'react';
import { Card, Row, Col, Button, Input, Select, Radio, Spin, Alert, Upload, message, Tabs, Divider, Space, Tag, Typography } from 'antd';
import { 
  SendOutlined, 
  RobotOutlined, 
  FileTextOutlined, 
  BulbOutlined, 
  CheckCircleOutlined, 
  SyncOutlined,
  UploadOutlined,
  DownloadOutlined,
  CopyOutlined,
  HistoryOutlined,
  WifiOutlined,
  DisconnectOutlined
} from '@ant-design/icons';
import adaptiveAIService from '../services/adaptiveAIService';

const { TextArea } = Input;
const { Option } = Select;
const { TabPane } = Tabs;
const { Title, Paragraph, Text } = Typography;

interface AIResponse {
  success: boolean;
  content?: string;
  generated_text?: string;
  review?: string;
  summary?: string;
  suggestions: string[];
  confidence: number;
  processing_time: number;
  tokens_used?: number;
}

interface Message {
  id: string;
  type: 'user' | 'ai' | 'system';
  content: string;
  timestamp: Date;
  task?: string;
  confidence?: number;
  mode?: 'api' | 'mock';
}

const AILegal = () => {
  const [loading, setLoading] = React.useState(false);
  const [activeTab, setActiveTab] = React.useState('chat');
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [inputText, setInputText] = React.useState('');
  const [documentType, setDocumentType] = React.useState('contrato');
  const [aiTask, setAiTask] = React.useState('generate');
  const [reviewText, setReviewText] = React.useState('');
  const [summarizeText, setSummarizeText] = React.useState('');
  const [result, setResult] = React.useState<AIResponse | null>(null);
  const [history, setHistory] = React.useState<Message[]>([]);
  const [serviceStatus, setServiceStatus] = React.useState<any>(null);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Verificar status do serviço ao carregar
  React.useEffect(() => {
    const status = adaptiveAIService.getServiceStatus();
    setServiceStatus(status);

    // Adicionar mensagem de boas-vindas
    const welcomeMessage: Message = {
      id: 'welcome',
      type: 'system',
      content: `🤖 **Assistente Jurídico ${status.mode === 'api' ? 'Avançado' : 'Básico'}** está pronto!\n\n${status.mode === 'api' 
        ? '✅ Conectado à IA em nuvem - Funcionalidades completas disponíveis'
        : '⚠️ Modo offline - Usando IA local com funcionalidades básicas'
      }\n\n**Como usar:**\n• Digite sua solicitação (ex: "Crie um contrato de locação")\n• Escolha o tipo de documento no menu\n• Use as abas para revisar ou resumir textos`,
      timestamp: new Date(),
      mode: status.mode
    };

    setMessages([welcomeMessage]);
  }, []);

  const documentTypes = [
    { value: 'contrato', label: 'Contrato' },
    { value: 'peticao', label: 'Petição Inicial' },
    { value: 'recurso', label: 'Recurso' },
    { value: 'parecer', label: 'Parecer Jurídico' },
    { value: 'procuracao', label: 'Procuração' },
    { value: 'defesa', label: 'Defesa' },
    { value: 'memoriais', label: 'Memoriais' },
    { value: 'acordo', label: 'Acordo' },
    { value: 'aditivo', label: 'Termo Aditivo' }
  ];

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputText,
      timestamp: new Date(),
      task: aiTask
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      // Usar o adaptive AI service
      const response = await adaptiveAIService.generateText(
        inputText, 
        { 
          document_type: documentType,
          legal_area: 'geral',
          context: `Solicitação de criação/análise de ${documentType}`
        }
      );

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: response.content,
        timestamp: new Date(),
        task: 'response',
        confidence: response.confidence,
        mode: serviceStatus?.mode
      };

      setMessages(prev => [...prev, aiMessage]);
      setHistory(prev => [...prev, userMessage, aiMessage]);
      
      message.success(`Resposta gerada com ${Math.round(response.confidence * 100)}% de confiança`);
      
    } catch (error: any) {
      console.error('Erro na geração:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: `❌ **Erro na geração**\n\nHouve um problema ao processar sua solicitação. Isto pode acontecer quando:\n\n• A IA está temporariamente indisponível\n• Há problemas de conectividade\n• O servidor está sobrecarregado\n\n**Sugestão:** Tente novamente em alguns momentos ou reformule sua pergunta de forma mais específica.`,
        timestamp: new Date(),
        task: 'error'
      };
      setMessages(prev => [...prev, errorMessage]);
      message.error('Erro na comunicação com a IA. Tente novamente.');
    } finally {
      setLoading(false);
      setInputText('');
    }
  };

  const handleReviewContent = async () => {
    if (!reviewText.trim()) {
      message.warning('Digite um texto para revisar');
      return;
    }

    setLoading(true);
    try {
      const response = await adaptiveAIService.analyzeDocument(reviewText, 'documento_geral');

      // Adaptar a resposta para o formato esperado
      const analysisResult: AIResponse = {
        success: true,
        review: `**Análise do Documento:**

**Pontos de Atenção:**
${response.risks.map((risk, i) => `${i + 1}. ${risk}`).join('\n')}

**Sugestões de Melhoria:**
${response.suggestions.map((sugg, i) => `${i + 1}. ${sugg}`).join('\n')}

**Conformidade:**
${response.compliance.map((comp, i) => `✓ ${comp}`).join('\n')}

**Pontuação Geral:** ${response.score}/100`,
        suggestions: response.suggestions,
        confidence: response.score / 100,
        processing_time: 0
      };

      setResult(analysisResult);
      message.success('Revisão concluída com sucesso!');
    } catch (error: any) {
      console.error('Erro na revisão:', error);
      message.error('Erro ao revisar documento. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const handleSummarizeContent = async () => {
    if (!summarizeText.trim()) {
      message.warning('Digite um texto para resumir');
      return;
    }

    setLoading(true);
    try {
      const response = await adaptiveAIService.summarizeText(summarizeText);

      const summaryResult: AIResponse = {
        success: true,
        summary: response.content,
        suggestions: response.legalReferences,
        confidence: response.confidence,
        processing_time: 0
      };

      setResult(summaryResult);
      message.success('Resumo gerado com sucesso!');
    } catch (error: any) {
      console.error('Erro no resumo:', error);
      message.error('Erro ao gerar resumo. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    message.success('Texto copiado para a área de transferência!');
  };

  const clearHistory = () => {
    setHistory([]);
    message.success('Histórico limpo!');
  };

  const refreshServiceStatus = () => {
    const status = adaptiveAIService.getServiceStatus();
    setServiceStatus(status);
    message.info(`Status atualizado: Modo ${status.mode === 'api' ? 'Online' : 'Offline'}`);
  };

  const renderMessage = (message: Message) => (
    <div key={message.id} className={`message ${message.type}`} style={{ marginBottom: 16 }}>
      <Card 
        size="small"
        className={message.type === 'user' ? 'user-message' : message.type === 'system' ? 'system-message' : 'ai-message'}
        style={{
          marginLeft: message.type === 'user' ? 'auto' : 0,
          marginRight: message.type === 'user' ? 0 : 'auto',
          maxWidth: message.type === 'system' ? '100%' : '80%',
          backgroundColor: 
            message.type === 'user' ? '#1890ff' : 
            message.type === 'system' ? '#52c41a' : '#f6f6f6',
          color: message.type === 'user' || message.type === 'system' ? 'white' : 'black',
          border: message.type === 'system' ? '1px solid #b7eb8f' : undefined
        }}
        actions={message.type === 'ai' ? [
          <CopyOutlined key="copy" onClick={() => copyToClipboard(message.content)} />,
          ...(message.confidence ? [<Tag key="confidence" color="blue">{Math.round(message.confidence * 100)}%</Tag>] : [])
        ] : message.type === 'system' ? [
          <Tag key="mode" color={message.mode === 'api' ? 'green' : 'orange'}>
            {message.mode === 'api' ? 'Online' : 'Offline'}
          </Tag>
        ] : []}
      >
        <div style={{ whiteSpace: 'pre-wrap' }}>
          {message.content}
        </div>
        <div style={{ 
          fontSize: '12px', 
          opacity: 0.7, 
          marginTop: 8,
          textAlign: 'right' 
        }}>
          {message.timestamp.toLocaleTimeString()}
        </div>
      </Card>
    </div>
  );

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '24px' }}>
        <Title level={2} style={{ margin: 0, flex: 1 }}>
          <RobotOutlined /> IA Jurídica Inteligente
        </Title>
        
        <Space>
          <Tag 
            color={serviceStatus?.mode === 'api' ? 'green' : 'orange'}
            icon={serviceStatus?.mode === 'api' ? <WifiOutlined /> : <DisconnectOutlined />}
          >
            {serviceStatus?.mode === 'api' ? 'Online' : 'Offline'}
          </Tag>
          <Button 
            size="small" 
            icon={<SyncOutlined />} 
            onClick={refreshServiceStatus}
          >
            Atualizar
          </Button>
        </Space>
      </div>

      <Paragraph>
        Assistente inteligente para criação, revisão e análise de documentos jurídicos.
        {serviceStatus?.mode === 'mock' && (
          <Alert 
            message="Modo Offline Ativo" 
            description="A IA está funcionando localmente. Para funcionalidades avançadas, configure a conexão com a API." 
            type="warning" 
            showIcon 
            style={{ marginTop: 8 }}
          />
        )}
      </Paragraph>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane 
          tab={<span><SendOutlined />Chat Interativo</span>} 
          key="chat"
        >
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Card 
                title="Configurações da IA"
                size="small"
                style={{ marginBottom: 16 }}
                extra={
                  <Space>
                    <Text type="secondary">
                      {serviceStatus?.capabilities?.length || 0} funcionalidades
                    </Text>
                  </Space>
                }
              >
                <Space wrap>
                  <Select
                    value={documentType}
                    onChange={setDocumentType}
                    style={{ width: 200 }}
                    placeholder="Tipo de Documento"
                  >
                    {documentTypes.map(type => (
                      <Option key={type.value} value={type.value}>
                        {type.label}
                      </Option>
                    ))}
                  </Select>
                  
                  <Tag color="blue">
                    {serviceStatus?.mode === 'api' ? 'GPT-4 Online' : 'IA Local'}
                  </Tag>
                  <Tag color="green">Especialista Jurídico</Tag>
                  {serviceStatus?.isOnline === false && (
                    <Tag color="red">Reconectando...</Tag>
                  )}
                </Space>
              </Card>
            </Col>

            <Col span={24}>
              <Card 
                title="Conversa"
                style={{ height: '500px', overflow: 'hidden' }}
                bodyStyle={{ height: '430px', overflowY: 'auto', padding: '16px' }}
              >
                {messages.length === 0 ? (
                  <div style={{ textAlign: 'center', color: '#999', marginTop: '150px' }}>
                    <RobotOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                    <div>Carregando assistente jurídico...</div>
                  </div>
                ) : (
                  messages.map(renderMessage)
                )}
                {loading && (
                  <div style={{ textAlign: 'center', margin: '20px 0' }}>
                    <Spin /> <Text type="secondary">Processando sua solicitação...</Text>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </Card>
            </Col>

            <Col span={24}>
              <Card size="small">
                <div style={{ display: 'flex', gap: '8px' }}>
                  <TextArea
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder="Digite sua solicitação... Ex: 'Crie um contrato de prestação de serviços para desenvolvimento de software'"
                    rows={2}
                    onPressEnter={(e) => {
                      if (e.shiftKey) return;
                      e.preventDefault();
                      handleSendMessage();
                    }}
                    style={{ flex: 1 }}
                    disabled={loading}
                  />
                  <Button
                    type="primary"
                    icon={<SendOutlined />}
                    onClick={handleSendMessage}
                    loading={loading}
                    disabled={!inputText.trim()}
                    size="large"
                  >
                    Enviar
                  </Button>
                </div>
                <div style={{ fontSize: '12px', color: '#999', marginTop: '4px' }}>
                  Pressione Enter para enviar, Shift+Enter para nova linha
                </div>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane 
          tab={<span><CheckCircleOutlined />Revisar Documento</span>} 
          key="review"
        >
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Card title="Texto para Revisão" style={{ height: '600px' }}>
                <TextArea
                  value={reviewText}
                  onChange={(e) => setReviewText(e.target.value)}
                  placeholder="Cole aqui o texto que deseja revisar...

Exemplo: Um contrato, uma petição, ou qualquer documento jurídico que precise de análise."
                  style={{ height: '450px', resize: 'none' }}
                />
                <div style={{ marginTop: '16px', textAlign: 'right' }}>
                  <Button
                    type="primary"
                    icon={<CheckCircleOutlined />}
                    onClick={handleReviewContent}
                    loading={loading}
                    disabled={!reviewText.trim()}
                  >
                    Revisar Texto
                  </Button>
                </div>
              </Card>
            </Col>

            <Col span={12}>
              <Card title="Resultado da Revisão" style={{ height: '600px' }}>
                {result && result.review ? (
                  <div>
                    <Alert
                      message={`Confiança: ${Math.round(result.confidence * 100)}%`}
                      type="info"
                      showIcon
                      style={{ marginBottom: '16px' }}
                    />
                    
                    <div style={{ marginBottom: '16px' }}>
                      <div style={{ marginTop: '8px', whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>
                        {result.review}
                      </div>
                    </div>

                    <div style={{ marginTop: '16px', textAlign: 'right' }}>
                      <Space>
                        <Button
                          icon={<CopyOutlined />}
                          onClick={() => copyToClipboard(result.review || '')}
                        >
                          Copiar Análise
                        </Button>
                      </Space>
                    </div>
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', color: '#999', marginTop: '200px' }}>
                    <FileTextOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                    <div>Cole um texto na área ao lado e clique em "Revisar"</div>
                    <div style={{ marginTop: '8px', fontSize: '14px' }}>
                      A IA analisará riscos, sugestões e conformidade
                    </div>
                  </div>
                )}
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane 
          tab={<span><BulbOutlined />Resumir Texto</span>} 
          key="summarize"
        >
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Card title="Texto para Resumo" style={{ height: '600px' }}>
                <TextArea
                  value={summarizeText}
                  onChange={(e) => setSummarizeText(e.target.value)}
                  placeholder="Cole aqui o texto que deseja resumir...

Exemplo: Documentos longos, jurisprudências, artigos de lei, ou qualquer texto jurídico extenso."
                  style={{ height: '450px', resize: 'none' }}
                />
                <div style={{ marginTop: '16px', textAlign: 'right' }}>
                  <Button
                    type="primary"
                    icon={<BulbOutlined />}
                    onClick={handleSummarizeContent}
                    loading={loading}
                    disabled={!summarizeText.trim()}
                  >
                    Gerar Resumo
                  </Button>
                </div>
              </Card>
            </Col>

            <Col span={12}>
              <Card title="Resumo Gerado" style={{ height: '600px' }}>
                {result && result.summary ? (
                  <div>
                    <Alert
                      message={`Redução: ${Math.round((1 - (result.summary.length / summarizeText.length)) * 100)}%`}
                      type="success"
                      showIcon
                      style={{ marginBottom: '16px' }}
                    />
                    
                    <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>
                      {result.summary}
                    </div>

                    {result.suggestions.length > 0 && (
                      <div style={{ marginTop: '16px' }}>
                        <Text strong>Referências Jurídicas:</Text>
                        <ul style={{ marginTop: '8px' }}>
                          {result.suggestions.map((ref, index) => (
                            <li key={index}>{ref}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <div style={{ marginTop: '16px', textAlign: 'right' }}>
                      <Button
                        icon={<CopyOutlined />}
                        onClick={() => copyToClipboard(result.summary || '')}
                      >
                        Copiar Resumo
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', color: '#999', marginTop: '200px' }}>
                    <BulbOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                    <div>Cole um texto na área ao lado e clique em "Gerar Resumo"</div>
                    <div style={{ marginTop: '8px', fontSize: '14px' }}>
                      A IA criará um resumo inteligente e conciso
                    </div>
                  </div>
                )}
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane 
          tab={<span><HistoryOutlined />Histórico</span>} 
          key="history"
        >
          <Card 
            title="Histórico de Conversas"
            extra={
              <Space>
                <Text type="secondary">{history.length} mensagens</Text>
                <Button 
                  size="small" 
                  onClick={clearHistory}
                  disabled={history.length === 0}
                >
                  Limpar
                </Button>
              </Space>
            }
          >
            {history.length === 0 ? (
              <div style={{ textAlign: 'center', color: '#999', padding: '100px 0' }}>
                <HistoryOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                <div>Nenhuma conversa salva ainda</div>
                <div style={{ marginTop: '8px', fontSize: '14px' }}>
                  Suas conversas aparecerão aqui automaticamente
                </div>
              </div>
            ) : (
              <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
                {history.map(renderMessage)}
              </div>
            )}
          </Card>
        </TabPane>
      </Tabs>

      <style jsx>{`
        .user-message {
          background-color: #1890ff !important;
          color: white !important;
        }
        
        .ai-message {
          background-color: #f6f6f6 !important;
          color: black !important;
        }

        .system-message {
          background-color: #52c41a !important;
          color: white !important;
        }
        
        .ant-card-actions {
          background: rgba(255, 255, 255, 0.1);
        }

        .ant-card-actions li {
          margin: 0 4px;
        }
      `}</style>
    </div>
  );
};

export default AILegal; 