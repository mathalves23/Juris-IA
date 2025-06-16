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
  HistoryOutlined
} from '@ant-design/icons';
import api from '../services/api';

const { TextArea } = Input;
const { Option } = Select;
const { TabPane } = Tabs;
const { Title, Paragraph, Text } = Typography;

interface AIResponse {
  success: boolean;
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
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
  task?: string;
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
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const documentTypes = [
    { value: 'contrato', label: 'Contrato' },
    { value: 'peticao', label: 'Petição Inicial' },
    { value: 'recurso', label: 'Recurso' },
    { value: 'parecer', label: 'Parecer Jurídico' },
    { value: 'procuracao', label: 'Procuração' },
    { value: 'defesa', label: 'Defesa' },
    { value: 'memoriais', label: 'Memoriais' }
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
      const response = await api.post('/ai/generate', {
        prompt: inputText,
        document_type: documentType
      });

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: response.data.generated_text,
        timestamp: new Date(),
        task: 'response'
      };

      setMessages(prev => [...prev, aiMessage]);
      setHistory(prev => [...prev, userMessage, aiMessage]);
      
    } catch (error: any) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: `Erro: ${error.response?.data?.error || 'Falha na comunicação com a IA'}`,
        timestamp: new Date(),
        task: 'error'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      setInputText('');
    }
  };

  const handleReviewContent = async () => {
    if (!reviewText.trim()) return;

    setLoading(true);
    try {
      const response = await api.post('/ai/review', {
        content: reviewText
      });

      setResult(response.data);
      message.success('Revisão concluída!');
    } catch (error: any) {
      message.error(`Erro na revisão: ${error.response?.data?.error || 'Erro desconhecido'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSummarizeContent = async () => {
    if (!summarizeText.trim()) return;

    setLoading(true);
    try {
      const response = await api.post('/ai/summarize', {
        content: summarizeText
      });

      setResult(response.data);
      message.success('Resumo gerado!');
    } catch (error: any) {
      message.error(`Erro no resumo: ${error.response?.data?.error || 'Erro desconhecido'}`);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    message.success('Texto copiado!');
  };

  const renderMessage = (message: Message) => (
    <div key={message.id} className={`message ${message.type}`} style={{ marginBottom: 16 }}>
      <Card 
        size="small"
        className={message.type === 'user' ? 'user-message' : 'ai-message'}
        style={{
          marginLeft: message.type === 'user' ? 'auto' : 0,
          marginRight: message.type === 'user' ? 0 : 'auto',
          maxWidth: '80%',
          backgroundColor: message.type === 'user' ? '#1890ff' : '#f6f6f6',
          color: message.type === 'user' ? 'white' : 'black'
        }}
        actions={message.type === 'ai' ? [
          <CopyOutlined key="copy" onClick={() => copyToClipboard(message.content)} />
        ] : undefined}
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
      <Title level={2}>
        <RobotOutlined /> IA Jurídica
      </Title>
      <Paragraph>
        Assistente inteligente para criação, revisão e análise de documentos jurídicos.
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
                  
                  <Tag color="blue">GPT-4</Tag>
                  <Tag color="green">Especialista Jurídico</Tag>
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
                    <div>Olá! Sou seu assistente jurídico. Como posso ajudar hoje?</div>
                    <div style={{ marginTop: '8px', fontSize: '14px' }}>
                      Exemplos: "Crie um contrato de locação" ou "Analise esta cláusula"
                    </div>
                  </div>
                ) : (
                  messages.map(renderMessage)
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
                    placeholder="Digite sua solicitação... Ex: 'Crie um contrato de prestação de serviços'"
                    rows={2}
                    onPressEnter={(e) => {
                      if (e.shiftKey) return;
                      e.preventDefault();
                      handleSendMessage();
                    }}
                    style={{ flex: 1 }}
                  />
                  <Button
                    type="primary"
                    icon={<SendOutlined />}
                    onClick={handleSendMessage}
                    loading={loading}
                    disabled={!inputText.trim()}
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
                  placeholder="Cole aqui o texto que deseja revisar..."
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
                      <Text strong>Análise:</Text>
                      <div style={{ marginTop: '8px', whiteSpace: 'pre-wrap' }}>
                        {result.review}
                      </div>
                    </div>

                    {result.suggestions.length > 0 && (
                      <div>
                        <Text strong>Sugestões de Melhoria:</Text>
                        <ul style={{ marginTop: '8px' }}>
                          {result.suggestions.map((suggestion, index) => (
                            <li key={index}>{suggestion}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <div style={{ marginTop: '16px', textAlign: 'right' }}>
                      <Button
                        icon={<CopyOutlined />}
                        onClick={() => copyToClipboard(result.review || '')}
                      >
                        Copiar Revisão
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', color: '#999', marginTop: '200px' }}>
                    <FileTextOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                    <div>Cole um texto na área ao lado e clique em "Revisar"</div>
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
                  placeholder="Cole aqui o texto que deseja resumir..."
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
          <Card title="Histórico de Conversas">
            {history.length === 0 ? (
              <div style={{ textAlign: 'center', color: '#999', padding: '100px 0' }}>
                <HistoryOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                <div>Nenhuma conversa salva ainda</div>
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
        }
        
        .message {
          animation: fadeIn 0.3s ease-in;
        }
        
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
};

export default AILegal; 