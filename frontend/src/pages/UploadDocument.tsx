import React from 'react';
import { Card, Row, Col, Button, Upload, Alert, Spin, Tabs, Typography, Space, Tag, Progress, message, List, Divider } from 'antd';
import { 
  UploadOutlined, 
  FileTextOutlined, 
  EyeOutlined, 
  SaveOutlined, 
  DownloadOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import type { UploadProps, UploadFile } from 'antd';
import api from '../services/api';

const { Dragger } = Upload;
const { TabPane } = Tabs;
const { Title, Paragraph, Text } = Typography;

interface AnalysisResult {
  filename: string;
  text: string;
  variable_suggestions: string[];
  stats: {
    words: number;
    characters: number;
    paragraphs: number;
  };
}

interface UploadResult {
  message: string;
  template: any;
  original_text: string;
  processed_text: string;
  variable_suggestions: string[];
}

const UploadDocument = () => {
  const [loading, setLoading] = React.useState(false);
  const [analysisResult, setAnalysisResult] = React.useState<AnalysisResult | null>(null);
  const [uploadResult, setUploadResult] = React.useState<UploadResult | null>(null);
  const [fileList, setFileList] = React.useState<UploadFile[]>([]);
  const [activeTab, setActiveTab] = React.useState('upload');
  const [templateTitle, setTemplateTitle] = React.useState('');
  const [templateCategory, setTemplateCategory] = React.useState('');

  const handlePreview = async (file: UploadFile) => {
    setLoading(true);
    
    const formData = new FormData();
    formData.append('file', file.originFileObj as File);

    try {
      const response = await api.post('/upload/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setAnalysisResult(response.data);
      setActiveTab('preview');
      message.success('Documento analisado com sucesso!');
    } catch (error: any) {
      message.error(`Erro na análise: ${error.response?.data?.error || 'Erro desconhecido'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (file: UploadFile) => {
    setLoading(true);
    
    const formData = new FormData();
    formData.append('file', file.originFileObj as File);
    formData.append('titulo', templateTitle || file.name);
    formData.append('categoria', templateCategory || 'Geral');

    try {
      const response = await api.post('/upload/document', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadResult(response.data);
      setActiveTab('result');
      message.success('Template criado com sucesso!');
    } catch (error: any) {
      message.error(`Erro no upload: ${error.response?.data?.error || 'Erro desconhecido'}`);
    } finally {
      setLoading(false);
    }
  };

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    fileList,
    accept: '.pdf,.docx,.doc',
    beforeUpload: (file) => {
      const isValidType = file.type === 'application/pdf' || 
                         file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
                         file.type === 'application/msword';
      
      if (!isValidType) {
        message.error('Apenas arquivos PDF e DOCX são permitidos!');
        return false;
      }

      const isLt10M = file.size / 1024 / 1024 < 10;
      if (!isLt10M) {
        message.error('Arquivo deve ter menos de 10MB!');
        return false;
      }

      setFileList([file]);
      return false; // Não fazer upload automático
    },
    onRemove: () => {
      setFileList([]);
      setAnalysisResult(null);
      setUploadResult(null);
    },
  };

  const renderStats = (stats: any) => (
    <Row gutter={16} style={{ marginBottom: 16 }}>
      <Col span={8}>
        <Card size="small" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
            {stats.words.toLocaleString()}
          </div>
          <div>Palavras</div>
        </Card>
      </Col>
      <Col span={8}>
        <Card size="small" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#52c41a' }}>
            {stats.characters.toLocaleString()}
          </div>
          <div>Caracteres</div>
        </Card>
      </Col>
      <Col span={8}>
        <Card size="small" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#faad14' }}>
            {stats.paragraphs}
          </div>
          <div>Parágrafos</div>
        </Card>
      </Col>
    </Row>
  );

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <Title level={2}>
        <UploadOutlined /> Upload de Documentos
      </Title>
      <Paragraph>
        Faça upload de documentos PDF ou DOCX para criar templates inteligentes com variáveis automaticamente detectadas.
      </Paragraph>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane 
          tab={<span><UploadOutlined />Upload</span>} 
          key="upload"
        >
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Card>
                <Dragger {...uploadProps} style={{ marginBottom: 16 }}>
                  <p className="ant-upload-drag-icon">
                    <FileTextOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
                  </p>
                  <p className="ant-upload-text">
                    Clique ou arraste arquivos para esta área
                  </p>
                  <p className="ant-upload-hint">
                    Suporte para arquivos PDF e DOCX. Máximo 10MB.
                  </p>
                </Dragger>

                {fileList.length > 0 && (
                  <div>
                    <Alert
                      message="Arquivo selecionado"
                      description={`${fileList[0].name} (${(fileList[0].size! / 1024 / 1024).toFixed(2)} MB)`}
                      type="success"
                      showIcon
                      style={{ marginBottom: 16 }}
                    />

                    <Space wrap style={{ marginBottom: 16 }}>
                      <Button
                        type="default"
                        icon={<EyeOutlined />}
                        onClick={() => handlePreview(fileList[0])}
                        loading={loading}
                      >
                        Analisar Documento
                      </Button>
                      
                      <Button
                        type="primary"
                        icon={<SaveOutlined />}
                        onClick={() => handleUpload(fileList[0])}
                        loading={loading}
                      >
                        Criar Template
                      </Button>
                    </Space>

                    <div style={{ marginTop: 16 }}>
                      <Text strong>Título do Template:</Text>
                      <input
                        type="text"
                        value={templateTitle}
                        onChange={(e) => setTemplateTitle(e.target.value)}
                        placeholder={fileList[0].name.replace(/\.[^/.]+$/, "")}
                        style={{
                          width: '100%',
                          padding: '8px',
                          marginTop: '4px',
                          border: '1px solid #d9d9d9',
                          borderRadius: '6px'
                        }}
                      />
                      
                      <Text strong style={{ marginTop: 16, display: 'block' }}>Categoria:</Text>
                      <input
                        type="text"
                        value={templateCategory}
                        onChange={(e) => setTemplateCategory(e.target.value)}
                        placeholder="Ex: Contratos, Petições, Pareceres"
                        style={{
                          width: '100%',
                          padding: '8px',
                          marginTop: '4px',
                          border: '1px solid #d9d9d9',
                          borderRadius: '6px'
                        }}
                      />
                    </div>
                  </div>
                )}
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane 
          tab={<span><EyeOutlined />Prévia</span>} 
          key="preview"
          disabled={!analysisResult}
        >
          {analysisResult && (
            <Row gutter={[16, 16]}>
              <Col span={24}>
                <Card title={`Análise: ${analysisResult.filename}`}>
                  {renderStats(analysisResult.stats)}
                  
                  {analysisResult.variable_suggestions.length > 0 && (
                    <div style={{ marginBottom: 16 }}>
                      <Alert
                        message="Variáveis Detectadas"
                        description="Possíveis campos variáveis encontrados no documento:"
                        type="info"
                        showIcon
                        style={{ marginBottom: 12 }}
                      />
                      <Space wrap>
                        {analysisResult.variable_suggestions.map((variable, index) => (
                          <Tag key={index} color="blue">
                            {variable}
                          </Tag>
                        ))}
                      </Space>
                    </div>
                  )}
                </Card>
              </Col>

              <Col span={24}>
                <Card 
                  title="Texto Extraído"
                  extra={
                    <Button
                      icon={<SaveOutlined />}
                      onClick={() => fileList[0] && handleUpload(fileList[0])}
                      loading={loading}
                    >
                      Criar Template
                    </Button>
                  }
                >
                  <div 
                    style={{ 
                      height: '400px', 
                      overflow: 'auto', 
                      border: '1px solid #f0f0f0',
                      padding: '16px',
                      backgroundColor: '#fafafa',
                      whiteSpace: 'pre-wrap',
                      fontFamily: 'monospace',
                      fontSize: '14px',
                      lineHeight: '1.6'
                    }}
                  >
                    {analysisResult.text}
                  </div>
                </Card>
              </Col>
            </Row>
          )}
        </TabPane>

        <TabPane 
          tab={<span><CheckCircleOutlined />Resultado</span>} 
          key="result"
          disabled={!uploadResult}
        >
          {uploadResult && (
            <Row gutter={[16, 16]}>
              <Col span={24}>
                <Alert
                  message="Template Criado com Sucesso!"
                  description={uploadResult.message}
                  type="success"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
              </Col>

              <Col span={12}>
                <Card title="Texto Original">
                  <div 
                    style={{ 
                      height: '400px', 
                      overflow: 'auto', 
                      padding: '16px',
                      backgroundColor: '#fafafa',
                      border: '1px solid #f0f0f0',
                      whiteSpace: 'pre-wrap',
                      fontFamily: 'monospace',
                      fontSize: '13px',
                      lineHeight: '1.5'
                    }}
                  >
                    {uploadResult.original_text}
                  </div>
                </Card>
              </Col>

              <Col span={12}>
                <Card title="Template com Variáveis">
                  <div 
                    style={{ 
                      height: '400px', 
                      overflow: 'auto', 
                      padding: '16px',
                      backgroundColor: '#f6ffed',
                      border: '1px solid #b7eb8f',
                      whiteSpace: 'pre-wrap',
                      fontFamily: 'monospace',
                      fontSize: '13px',
                      lineHeight: '1.5'
                    }}
                  >
                    {uploadResult.processed_text}
                  </div>
                </Card>
              </Col>

              <Col span={24}>
                <Card title="Variáveis Criadas">
                  <List
                    dataSource={uploadResult.variable_suggestions}
                    renderItem={(item, index) => (
                      <List.Item>
                        <Space>
                          <Tag color="green">#{index + 1}</Tag>
                          <Text code>{`{${item.toUpperCase().replace(' ', '_')}}`}</Text>
                          <Text type="secondary">← {item}</Text>
                        </Space>
                      </List.Item>
                    )}
                    style={{ backgroundColor: '#fafafa', padding: '16px' }}
                  />
                </Card>
              </Col>

              <Col span={24}>
                <Card>
                  <Space>
                    <Button type="primary" href="/templates">
                      Ver Templates
                    </Button>
                    <Button 
                      onClick={() => {
                        setActiveTab('upload');
                        setFileList([]);
                        setAnalysisResult(null);
                        setUploadResult(null);
                        setTemplateTitle('');
                        setTemplateCategory('');
                      }}
                    >
                      Novo Upload
                    </Button>
                  </Space>
                </Card>
              </Col>
            </Row>
          )}
        </TabPane>
      </Tabs>

      <div style={{ marginTop: 24 }}>
        <Card title="Formatos Suportados" size="small">
          <Row gutter={16}>
            <Col span={8}>
              <div style={{ textAlign: 'center' }}>
                <FileTextOutlined style={{ fontSize: '32px', color: '#ff4d4f' }} />
                <div style={{ marginTop: 8 }}>
                  <Text strong>PDF</Text>
                  <div style={{ fontSize: '12px', color: '#999' }}>
                    Documentos Adobe PDF
                  </div>
                </div>
              </div>
            </Col>
            <Col span={8}>
              <div style={{ textAlign: 'center' }}>
                <FileTextOutlined style={{ fontSize: '32px', color: '#1890ff' }} />
                <div style={{ marginTop: 8 }}>
                  <Text strong>DOCX</Text>
                  <div style={{ fontSize: '12px', color: '#999' }}>
                    Microsoft Word 2007+
                  </div>
                </div>
              </div>
            </Col>
            <Col span={8}>
              <div style={{ textAlign: 'center' }}>
                <FileTextOutlined style={{ fontSize: '32px', color: '#52c41a' }} />
                <div style={{ marginTop: 8 }}>
                  <Text strong>DOC</Text>
                  <div style={{ fontSize: '12px', color: '#999' }}>
                    Microsoft Word Legacy
                  </div>
                </div>
              </div>
            </Col>
          </Row>
        </Card>
      </div>

      {loading && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <Card style={{ textAlign: 'center', minWidth: 200 }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>
              Processando documento...
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default UploadDocument; 