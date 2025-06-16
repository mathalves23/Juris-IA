import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Input,
  Button,
  Select,
  Form,
  Typography,
  Space,
  Divider,
  Tag,
  Modal,
  Drawer,
  Collapse,
  Progress,
  Alert,
  Tooltip,
  Row,
  Col,
  Avatar,
  List,
  Spin,
  Badge,
  Rate
} from 'antd';
import {
  SendOutlined,
  RobotOutlined,
  HistoryOutlined,
  BookOutlined,
  BulbOutlined,
  QuestionCircleOutlined,
  StarOutlined,
  CopyOutlined,
  DownloadOutlined,
  SyncOutlined,
  MessageOutlined,
  LawOutlined,
  FileTextOutlined,
  SearchOutlined,
  BranchesOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { useAuth } from '../../contexts/AuthContext';
import legalAIService, { 
  ConversationMessage, 
  LegalPrompt, 
  ConversationContext,
  ClientContext,
  CaseContext 
} from '../../services/legalAIService';
import './LegalAIAssistant.css';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;
const { Panel } = Collapse;

interface Props {
  initialTopic?: string;
  initialArea?: string;
  clientContext?: ClientContext;
  caseContext?: CaseContext;
}

const LegalAIAssistant: React.FC<Props> = ({
  initialTopic,
  initialArea,
  clientContext,
  caseContext
}) => {
  const { user } = useAuth();
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedPrompt, setSelectedPrompt] = useState<string>('');
  const [promptParams, setPromptParams] = useState<{ [key: string]: string }>({});
  const [showPrompts, setShowPrompts] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [showKnowledge, setShowKnowledge] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<ConversationContext[]>([]);
  const [availablePrompts] = useState<LegalPrompt[]>(legalAIService.getAvailablePrompts());
  const [legalAreas] = useState<string[]>(legalAIService.getLegalAreas());
  const [selectedArea, setSelectedArea] = useState(initialArea || 'Civil');
  const [conversationTopic, setConversationTopic] = useState(initialTopic || '');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [form] = Form.useForm();

  // Estados para funcionalidades avançadas
  const [contextEnabled, setContextEnabled] = useState(true);
  const [precedentsVisible, setPrecedentsVisible] = useState(false);
  const [similarCases, setSimilarCases] = useState<any[]>([]);
  const [knowledgeBase, setKnowledgeBase] = useState<any[]>([]);
  const [conversationSummary, setConversationSummary] = useState('');

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (user) {
      loadConversationHistory();
    }
  }, [user]);

  useEffect(() => {
    if (initialTopic && initialArea && !currentConversationId) {
      startNewConversation();
    }
  }, [initialTopic, initialArea]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const loadConversationHistory = async () => {
    if (!user) return;
    
    try {
      const history = await legalAIService.getConversationHistory(user.id);
      setConversationHistory(history);
    } catch (error) {
      console.error('Erro ao carregar histórico:', error);
    }
  };

  const startNewConversation = async () => {
    if (!conversationTopic.trim() || !selectedArea) {
      Modal.warning({
        title: 'Informações Necessárias',
        content: 'Por favor, defina um tópico e selecione uma área do direito.'
      });
      return;
    }

    try {
      setLoading(true);
      const conversationId = await legalAIService.createConversation(
        conversationTopic,
        selectedArea,
        clientContext,
        caseContext
      );
      
      setCurrentConversationId(conversationId);
      setMessages([]);
      
      // Mensagem de boas-vindas
      const welcomeMessage: ConversationMessage = {
        id: 'welcome',
        role: 'assistant',
        content: `Olá! Sou seu assistente jurídico especializado em **${selectedArea}**.

Estou pronto para ajudar com "${conversationTopic}". Posso:

🔍 **Pesquisar** legislação e jurisprudência
📝 **Redigir** documentos jurídicos
⚖️ **Analisar** contratos e casos
💡 **Sugerir** estratégias jurídicas
📚 **Consultar** precedentes similares

Como posso ajudar você hoje?`,
        timestamp: new Date(),
        metadata: {
          confidence: 1.0,
          sources: [],
          legalReferences: []
        }
      };
      
      setMessages([welcomeMessage]);
    } catch (error) {
      console.error('Erro ao iniciar conversa:', error);
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!currentConversationId || !inputMessage.trim()) return;

    const userMessage: ConversationMessage = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await legalAIService.sendMessage(
        currentConversationId,
        inputMessage,
        selectedPrompt,
        promptParams
      );

      setMessages(prev => [...prev, response]);
      
      // Buscar casos similares se habilitado
      if (contextEnabled) {
        findSimilarCases(inputMessage);
      }

      // Limpar prompt selecionado
      setSelectedPrompt('');
      setPromptParams({});
    } catch (error) {
      console.error('Erro ao enviar mensagem:', error);
      
      const errorMessage: ConversationMessage = {
        id: `error_${Date.now()}`,
        role: 'assistant',
        content: 'Desculpe, ocorreu um erro ao processar sua solicitação. Tente novamente.',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const findSimilarCases = async (query: string) => {
    try {
      const precedents = await legalAIService.findSimilarPrecedents(query, selectedArea);
      setSimilarCases(precedents);
      if (precedents.length > 0) {
        setPrecedentsVisible(true);
      }
    } catch (error) {
      console.error('Erro ao buscar precedentes:', error);
    }
  };

  const usePrompt = (prompt: LegalPrompt) => {
    setSelectedPrompt(prompt.id);
    setShowPrompts(false);
    
    // Abrir modal para preenchimento de parâmetros
    if (prompt.parameters.length > 0) {
      showPromptParametersModal(prompt);
    } else {
      setInputMessage(prompt.template);
    }
  };

  const showPromptParametersModal = (prompt: LegalPrompt) => {
    Modal.confirm({
      title: `Configurar: ${prompt.name}`,
      width: 600,
      content: (
        <Form layout="vertical" onFinish={(values) => {
          setPromptParams(values);
          const filledTemplate = fillPromptTemplate(prompt.template, values);
          setInputMessage(filledTemplate);
          Modal.destroyAll();
        }}>
          {prompt.parameters.map(param => (
            <Form.Item
              key={param}
              name={param}
              label={formatParameterLabel(param)}
              rules={[{ required: true, message: `${param} é obrigatório` }]}
            >
              {param.includes('text') || param.includes('content') ? (
                <TextArea rows={3} placeholder={`Digite ${param}...`} />
              ) : (
                <Input placeholder={`Digite ${param}...`} />
              )}
            </Form.Item>
          ))}
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              Aplicar Template
            </Button>
          </Form.Item>
        </Form>
      ),
      footer: null
    });
  };

  const fillPromptTemplate = (template: string, params: { [key: string]: string }): string => {
    let filled = template;
    Object.entries(params).forEach(([key, value]) => {
      filled = filled.replace(new RegExp(`{${key}}`, 'g'), value);
    });
    return filled;
  };

  const formatParameterLabel = (param: string): string => {
    const labels: { [key: string]: string } = {
      'contract_type': 'Tipo de Contrato',
      'parties': 'Partes Envolvidas',
      'object': 'Objeto do Contrato',
      'value': 'Valor',
      'term': 'Prazo',
      'jurisdiction': 'Jurisdição',
      'contract_text': 'Texto do Contrato',
      'legal_question': 'Questão Jurídica',
      'legal_area': 'Área do Direito',
      'facts': 'Fatos',
      'action_type': 'Tipo de Ação',
      'plaintiff': 'Autor',
      'defendant': 'Réu',
      'cause': 'Causa de Pedir',
      'requests': 'Pedidos',
      'topic': 'Tópico'
    };
    
    return labels[param] || param.replace('_', ' ').toUpperCase();
  };

  const copyMessage = (content: string) => {
    navigator.clipboard.writeText(content);
    // Mostrar feedback visual
  };

  const generateSummary = async () => {
    if (!currentConversationId) return;
    
    try {
      const summary = await legalAIService.generateConversationSummary(currentConversationId);
      setConversationSummary(summary);
      
      Modal.info({
        title: 'Resumo da Conversa',
        content: summary,
        width: 600
      });
    } catch (error) {
      console.error('Erro ao gerar resumo:', error);
    }
  };

  const exportConversation = () => {
    const content = messages
      .filter(msg => msg.role !== 'system')
      .map(msg => `[${msg.role.toUpperCase()}] ${msg.content}`)
      .join('\n\n');
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conversa_juridica_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const renderMessage = (message: ConversationMessage) => {
    const isUser = message.role === 'user';
    
    return (
      <div key={message.id} className={`message ${isUser ? 'user' : 'assistant'}`}>
        <div className="message-avatar">
          {isUser ? (
            <Avatar size="small" icon={<MessageOutlined />} />
          ) : (
            <Avatar size="small" icon={<RobotOutlined />} style={{ backgroundColor: '#1890ff' }} />
          )}
        </div>
        
        <div className="message-content">
          <div className="message-header">
            <Text strong>{isUser ? 'Você' : 'Assistente Jurídico'}</Text>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {message.timestamp.toLocaleTimeString()}
            </Text>
          </div>
          
          <div className="message-text">
            <Paragraph style={{ marginBottom: 0, whiteSpace: 'pre-wrap' }}>
              {message.content}
            </Paragraph>
          </div>
          
          {!isUser && message.metadata && (
            <div className="message-metadata">
              <Space wrap>
                <Tooltip title="Confiança da resposta">
                  <Progress
                    percent={Math.round((message.metadata.confidence || 0) * 100)}
                    size="small"
                    style={{ width: 80 }}
                  />
                </Tooltip>
                
                {message.metadata.legalReferences?.length > 0 && (
                  <Tooltip title="Referências legais encontradas">
                    <Badge count={message.metadata.legalReferences.length}>
                      <LawOutlined style={{ color: '#1890ff' }} />
                    </Badge>
                  </Tooltip>
                )}
                
                {message.metadata.sources?.length > 0 && (
                  <Tooltip title={`Fontes: ${message.metadata.sources.join(', ')}`}>
                    <BookOutlined style={{ color: '#52c41a' }} />
                  </Tooltip>
                )}
              </Space>
              
              <div className="message-actions">
                <Button
                  type="text"
                  size="small"
                  icon={<CopyOutlined />}
                  onClick={() => copyMessage(message.content)}
                />
                <Button
                  type="text"
                  size="small"
                  icon={<StarOutlined />}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="legal-ai-assistant">
      <Row gutter={24}>
        {/* Painel Principal */}
        <Col xs={24} lg={16}>
          <Card
            title={
              <Space>
                <RobotOutlined style={{ color: '#1890ff' }} />
                <span>Assistente Jurídico IA</span>
                {selectedArea && <Tag color="blue">{selectedArea}</Tag>}
              </Space>
            }
            extra={
              <Space>
                <Tooltip title="Histórico de Conversas">
                  <Button
                    icon={<HistoryOutlined />}
                    onClick={() => setShowHistory(true)}
                  />
                </Tooltip>
                <Tooltip title="Templates Jurídicos">
                  <Button
                    icon={<FileTextOutlined />}
                    onClick={() => setShowPrompts(true)}
                  />
                </Tooltip>
                <Tooltip title="Base de Conhecimento">
                  <Button
                    icon={<BookOutlined />}
                    onClick={() => setShowKnowledge(true)}
                  />
                </Tooltip>
                <Tooltip title="Gerar Resumo">
                  <Button
                    icon={<SyncOutlined />}
                    onClick={generateSummary}
                    disabled={messages.length === 0}
                  />
                </Tooltip>
                <Tooltip title="Exportar Conversa">
                  <Button
                    icon={<DownloadOutlined />}
                    onClick={exportConversation}
                    disabled={messages.length === 0}
                  />
                </Tooltip>
              </Space>
            }
          >
            {/* Configuração inicial */}
            {!currentConversationId && (
              <div className="conversation-setup">
                <Alert
                  message="Configure sua consulta jurídica"
                  description="Defina o tópico e a área do direito para começar uma conversa especializada."
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
                
                <Row gutter={16}>
                  <Col xs={24} md={12}>
                    <Form.Item label="Área do Direito">
                      <Select
                        value={selectedArea}
                        onChange={setSelectedArea}
                        placeholder="Selecione a área"
                      >
                        {legalAreas.map(area => (
                          <Option key={area} value={area}>{area}</Option>
                        ))}
                      </Select>
                    </Form.Item>
                  </Col>
                  
                  <Col xs={24} md={12}>
                    <Form.Item label="Tópico da Consulta">
                      <Input
                        value={conversationTopic}
                        onChange={(e) => setConversationTopic(e.target.value)}
                        placeholder="Ex: Análise de contrato de prestação de serviços"
                      />
                    </Form.Item>
                  </Col>
                </Row>
                
                <Button
                  type="primary"
                  size="large"
                  onClick={startNewConversation}
                  loading={loading}
                  disabled={!conversationTopic.trim() || !selectedArea}
                  block
                >
                  Iniciar Consulta Jurídica
                </Button>
              </div>
            )}

            {/* Área de mensagens */}
            {currentConversationId && (
              <>
                <div className="messages-container">
                  {messages.map(renderMessage)}
                  {loading && (
                    <div className="message assistant">
                      <div className="message-avatar">
                        <Avatar size="small" icon={<RobotOutlined />} style={{ backgroundColor: '#1890ff' }} />
                      </div>
                      <div className="message-content">
                        <Spin size="small" />
                        <Text type="secondary" style={{ marginLeft: 8 }}>
                          Analisando sua solicitação...
                        </Text>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Input de mensagem */}
                <div className="message-input">
                  <Input.Group compact>
                    <TextArea
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      placeholder="Digite sua pergunta jurídica ou use um template..."
                      autoSize={{ minRows: 1, maxRows: 4 }}
                      onPressEnter={(e) => {
                        if (!e.shiftKey) {
                          e.preventDefault();
                          sendMessage();
                        }
                      }}
                      style={{ width: 'calc(100% - 120px)' }}
                    />
                    <Button
                      type="primary"
                      icon={<SendOutlined />}
                      onClick={sendMessage}
                      loading={loading}
                      disabled={!inputMessage.trim()}
                      style={{ width: 60 }}
                    >
                    </Button>
                    <Button
                      icon={<BulbOutlined />}
                      onClick={() => setShowPrompts(true)}
                      style={{ width: 60 }}
                      title="Templates"
                    />
                  </Input.Group>
                </div>
              </>
            )}
          </Card>
        </Col>

        {/* Painel Lateral */}
        <Col xs={24} lg={8}>
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            {/* Informações do Contexto */}
            {(clientContext || caseContext) && (
              <Card title="Contexto" size="small">
                {clientContext && (
                  <div>
                    <Text strong>Cliente:</Text>
                    <br />
                    <Text>{clientContext.type === 'pessoa_fisica' ? 'Pessoa Física' : 'Pessoa Jurídica'}</Text>
                    {clientContext.situation && (
                      <>
                        <br />
                        <Text type="secondary">{clientContext.situation}</Text>
                      </>
                    )}
                  </div>
                )}
                
                {caseContext && (
                  <div style={{ marginTop: clientContext ? 12 : 0 }}>
                    <Text strong>Caso:</Text>
                    <br />
                    <Tag color={caseContext.urgency === 'alta' ? 'red' : caseContext.urgency === 'media' ? 'orange' : 'green'}>
                      {caseContext.urgency.toUpperCase()}
                    </Tag>
                    <br />
                    <Text type="secondary">{caseContext.type}</Text>
                  </div>
                )}
              </Card>
            )}

            {/* Precedentes Similares */}
            {precedentsVisible && similarCases.length > 0 && (
              <Card 
                title="Precedentes Similares" 
                size="small"
                extra={
                  <Button 
                    type="text" 
                    size="small"
                    onClick={() => setPrecedentsVisible(false)}
                  >
                    ×
                  </Button>
                }
              >
                <List
                  size="small"
                  dataSource={similarCases.slice(0, 3)}
                  renderItem={(precedent: any) => (
                    <List.Item>
                      <div>
                        <Text strong style={{ fontSize: '12px' }}>
                          {precedent.court}
                        </Text>
                        <br />
                        <Text style={{ fontSize: '11px' }}>
                          {precedent.title.substring(0, 80)}...
                        </Text>
                        <br />
                        <Rate disabled defaultValue={precedent.similarity * 5} size="small" />
                      </div>
                    </List.Item>
                  )}
                />
              </Card>
            )}

            {/* Estatísticas da Conversa */}
            {messages.length > 0 && (
              <Card title="Estatísticas" size="small">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text type="secondary">Mensagens:</Text>
                    <Text strong style={{ float: 'right' }}>{messages.length}</Text>
                  </div>
                  <div>
                    <Text type="secondary">Duração:</Text>
                    <Text strong style={{ float: 'right' }}>
                      {messages.length > 1 ? 
                        Math.round((messages[messages.length - 1].timestamp.getTime() - messages[0].timestamp.getTime()) / 60000) + ' min'
                        : '< 1 min'
                      }
                    </Text>
                  </div>
                  <div>
                    <Text type="secondary">Confiança Média:</Text>
                    <Text strong style={{ float: 'right' }}>
                      {Math.round(
                        messages
                          .filter(m => m.metadata?.confidence)
                          .reduce((acc, m) => acc + (m.metadata?.confidence || 0), 0) /
                        messages.filter(m => m.metadata?.confidence).length * 100
                      ) || 0}%
                    </Text>
                  </div>
                </Space>
              </Card>
            )}
          </Space>
        </Col>
      </Row>

      {/* Modal de Templates */}
      <Modal
        title="Templates Jurídicos"
        open={showPrompts}
        onCancel={() => setShowPrompts(false)}
        footer={null}
        width={800}
      >
        <Collapse accordion>
          {availablePrompts.map(prompt => (
            <Panel
              header={
                <Space>
                  <Tag color="blue">{prompt.category}</Tag>
                  <span>{prompt.name}</span>
                </Space>
              }
              key={prompt.id}
            >
              <Paragraph>{prompt.description}</Paragraph>
              <Button
                type="primary"
                onClick={() => usePrompt(prompt)}
                block
              >
                Usar Template
              </Button>
            </Panel>
          ))}
        </Collapse>
      </Modal>

      {/* Drawer de Histórico */}
      <Drawer
        title="Histórico de Conversas"
        placement="right"
        onClose={() => setShowHistory(false)}
        open={showHistory}
        width={400}
      >
        <List
          dataSource={conversationHistory}
          renderItem={(conversation: ConversationContext) => (
            <List.Item
              actions={[
                <Button type="text" size="small">
                  Continuar
                </Button>
              ]}
            >
              <List.Item.Meta
                avatar={<Avatar icon={<LawOutlined />} />}
                title={conversation.topic}
                description={
                  <Space direction="vertical" size="small">
                    <Tag size="small">{conversation.legalArea}</Tag>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      {conversation.messages.length} mensagens
                    </Text>
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      </Drawer>

      {/* Drawer de Base de Conhecimento */}
      <Drawer
        title="Base de Conhecimento"
        placement="right"
        onClose={() => setShowKnowledge(false)}
        open={showKnowledge}
        width={500}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Input.Search
            placeholder="Buscar na base de conhecimento..."
            enterButton={<SearchOutlined />}
          />
          
          <Collapse>
            <Panel header="Legislação" key="legislation">
              <List
                size="small"
                dataSource={['Código Civil', 'CDC', 'CLT', 'CPC/2015']}
                renderItem={item => <List.Item>{item}</List.Item>}
              />
            </Panel>
            
            <Panel header="Jurisprudência" key="jurisprudence">
              <List
                size="small"
                dataSource={['STJ', 'STF', 'TST', 'TRTs']}
                renderItem={item => <List.Item>{item}</List.Item>}
              />
            </Panel>
            
            <Panel header="Doutrina" key="doctrine">
              <List
                size="small"
                dataSource={['Artigos', 'Livros', 'Comentários']}
                renderItem={item => <List.Item>{item}</List.Item>}
              />
            </Panel>
          </Collapse>
        </Space>
      </Drawer>
    </div>
  );
};

export default LegalAIAssistant; 