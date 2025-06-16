import React, { useState, useEffect } from 'react';
import { 
  Alert, 
  Badge, 
  Button, 
  Tooltip, 
  Modal, 
  List, 
  Typography, 
  Space,
  Tag,
  Popover,
  Progress 
} from 'antd';
import {
  WifiOutlined,
  DisconnectOutlined,
  InfoCircleOutlined,
  ReloadOutlined,
  SettingOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import adaptiveAIService from '../../services/adaptiveAIService';

const { Text, Title } = Typography;

interface ServiceStatusProps {
  showDetails?: boolean;
  style?: React.CSSProperties;
  size?: 'small' | 'default' | 'large';
}

const ServiceStatus: React.FC<ServiceStatusProps> = ({ 
  showDetails = true, 
  style = {},
  size = 'default'
}) => {
  const [status, setStatus] = useState(adaptiveAIService.getServiceStatus());
  const [showModal, setShowModal] = useState(false);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    // Atualizar status periodicamente
    const interval = setInterval(() => {
      const newStatus = adaptiveAIService.getServiceStatus();
      setStatus(newStatus);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleCheckStatus = async () => {
    setChecking(true);
    try {
      await adaptiveAIService.forceStatusCheck();
      const newStatus = adaptiveAIService.getServiceStatus();
      setStatus(newStatus);
    } catch (error) {
      console.error('Erro ao verificar status:', error);
    } finally {
      setChecking(false);
    }
  };

  const getStatusColor = () => {
    if (status.isOnline) return 'success';
    if (status.mode === 'mock') return 'warning';
    return 'error';
  };

  const getStatusIcon = () => {
    if (status.isOnline) return <WifiOutlined />;
    return <DisconnectOutlined />;
  };

  const getStatusText = () => {
    if (status.isOnline) return 'Online';
    if (status.mode === 'mock') return 'Offline (Modo Local)';
    return 'Desconectado';
  };

  const getStatusDescription = () => {
    if (status.isOnline) {
      return 'Todas as funcionalidades estão disponíveis';
    }
    if (status.mode === 'mock') {
      return 'Funcionando localmente com recursos limitados';
    }
    return 'Verifique sua conexão com a internet';
  };

  const StatusBadge = () => (
    <Badge 
      status={getStatusColor()} 
      text={
        <Space size="small">
          {getStatusIcon()}
          <Text style={{ fontSize: size === 'small' ? 12 : 14 }}>
            {getStatusText()}
          </Text>
        </Space>
      }
    />
  );

  const DetailedStatus = () => (
    <Alert
      message={
        <Space>
          <StatusBadge />
          {showDetails && (
            <Tooltip title="Ver detalhes completos">
              <Button 
                type="link" 
                size="small" 
                icon={<InfoCircleOutlined />}
                onClick={() => setShowModal(true)}
              >
                Detalhes
              </Button>
            </Tooltip>
          )}
          <Tooltip title="Verificar status">
            <Button
              type="link"
              size="small"
              icon={<ReloadOutlined />}
              loading={checking}
              onClick={handleCheckStatus}
            >
              Atualizar
            </Button>
          </Tooltip>
        </Space>
      }
      type={getStatusColor()}
      showIcon={false}
      style={style}
    />
  );

  const StatusModal = () => (
    <Modal
      title={
        <Space>
          <SettingOutlined />
          Status do Sistema JurisIA
        </Space>
      }
      open={showModal}
      onCancel={() => setShowModal(false)}
      footer={[
        <Button key="refresh" icon={<ReloadOutlined />} onClick={handleCheckStatus} loading={checking}>
          Atualizar Status
        </Button>,
        <Button key="close" type="primary" onClick={() => setShowModal(false)}>
          Fechar
        </Button>
      ]}
      width={600}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {/* Status Geral */}
        <div>
          <Title level={4}>Status da Conexão</Title>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text>Modo de Operação:</Text>
              <Tag color={status.isOnline ? 'green' : 'orange'}>
                {status.mode === 'api' ? 'API Online' : 'Modo Local'}
              </Tag>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text>Status da Rede:</Text>
              <Space>
                {status.isOnline ? <CheckCircleOutlined style={{ color: '#52c41a' }} /> : <ExclamationCircleOutlined style={{ color: '#faad14' }} />}
                <Text>{status.isOnline ? 'Conectado' : 'Desconectado'}</Text>
              </Space>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text>Última Verificação:</Text>
              <Text type="secondary">
                {status.lastCheck.toLocaleTimeString()}
              </Text>
            </div>
            
            {status.errorCount > 0 && (
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text>Erros de Conexão:</Text>
                <Tag color="red">{status.errorCount}</Tag>
              </div>
            )}
          </Space>
        </div>

        {/* Capacidades Disponíveis */}
        <div>
          <Title level={4}>Funcionalidades Disponíveis</Title>
          <List
            size="small"
            dataSource={status.capabilities}
            renderItem={(capability) => (
              <List.Item>
                <Space>
                  <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  <Text>{capability}</Text>
                </Space>
              </List.Item>
            )}
          />
        </div>

        {/* Informações do Sistema */}
        <div>
          <Title level={4}>Informações do Sistema</Title>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Text>Versão do Frontend:</Text>
              <Text>2.0.0</Text>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Text>Ambiente:</Text>
              <Text>{process.env.NODE_ENV || 'development'}</Text>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Text>URL da API:</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {process.env.REACT_APP_API_URL || 'https://jurisia-api.onrender.com/api'}
              </Text>
            </div>
          </Space>
        </div>

        {/* Status de Performance */}
        {status.isOnline && (
          <div>
            <Title level={4}>Performance</Title>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text>Velocidade de Resposta</Text>
                <Progress percent={85} size="small" status="active" />
              </div>
              <div>
                <Text>Qualidade da Conexão</Text>
                <Progress percent={92} size="small" status="active" strokeColor="#52c41a" />
              </div>
            </Space>
          </div>
        )}

        {/* Recomendações */}
        {!status.isOnline && (
          <Alert
            message="Sistema em Modo Offline"
            description={
              <div>
                <p>O sistema está funcionando localmente com recursos limitados. Para acessar todas as funcionalidades:</p>
                <ul>
                  <li>Verifique sua conexão com a internet</li>
                  <li>Aguarde alguns minutos e tente novamente</li>
                  <li>Entre em contato com o suporte se o problema persistir</li>
                </ul>
              </div>
            }
            type="warning"
            showIcon
          />
        )}
      </Space>
    </Modal>
  );

  const PopoverContent = () => (
    <div style={{ width: 250 }}>
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        <div>
          <Text strong>Status: </Text>
          <Text>{getStatusText()}</Text>
        </div>
        <div>
          <Text type="secondary">{getStatusDescription()}</Text>
        </div>
        <div>
          <Text strong>Funcionalidades: </Text>
          <Text>{status.capabilities.length}</Text>
        </div>
        <Button size="small" type="link" onClick={() => setShowModal(true)}>
          Ver detalhes completos
        </Button>
      </Space>
    </div>
  );

  if (size === 'small') {
    return (
      <>
        <Popover content={<PopoverContent />} title="Status do Sistema">
          <div style={{ cursor: 'pointer', ...style }}>
            <StatusBadge />
          </div>
        </Popover>
        <StatusModal />
      </>
    );
  }

  return (
    <>
      <DetailedStatus />
      <StatusModal />
    </>
  );
};

export default ServiceStatus; 