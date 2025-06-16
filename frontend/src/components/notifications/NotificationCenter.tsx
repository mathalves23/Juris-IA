import React, { useState, useEffect, useRef } from 'react';
import { 
  Badge, 
  Popover, 
  List, 
  Button, 
  Typography, 
  Divider, 
  Tag, 
  Empty, 
  Spin, 
  Space,
  Tooltip,
  Dropdown,
  Menu,
  Switch,
  message
} from 'antd';
import { 
  BellOutlined, 
  SettingOutlined, 
  CheckOutlined, 
  DeleteOutlined,
  FilterOutlined,
  ReloadOutlined,
  InboxOutlined
} from '@ant-design/icons';
import axios from 'axios';
import { io, Socket } from 'socket.io-client';
import './NotificationCenter.css';

const { Text, Title } = Typography;

interface Notification {
  id: number;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'system' | 'legal' | 'task' | 'document' | 'ai';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  is_read: boolean;
  is_archived: boolean;
  created_at: string;
  read_at?: string;
  category?: string;
  action_url?: string;
  action_text?: string;
  metadata?: any;
}

interface NotificationStats {
  total: number;
  unread: number;
  archived: number;
  read: number;
  by_type: Record<string, number>;
  by_priority: Record<string, number>;
}

interface NotificationSettings {
  email_enabled: boolean;
  push_enabled: boolean;
  browser_enabled: boolean;
  legal_notifications: boolean;
  task_notifications: boolean;
  document_notifications: boolean;
  ai_notifications: boolean;
  system_notifications: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  weekend_notifications: boolean;
}

const NotificationCenter: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [visible, setVisible] = useState(false);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');
  const [settings, setSettings] = useState<NotificationSettings | null>(null);
  const [settingsVisible, setSettingsVisible] = useState(false);
  const [stats, setStats] = useState<NotificationStats | null>(null);
  
  const socketRef = useRef<Socket | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Cores por tipo de notificação
  const getTypeColor = (type: string) => {
    const colors = {
      info: '#1890ff',
      success: '#52c41a',
      warning: '#faad14',
      error: '#ff4d4f',
      system: '#722ed1',
      legal: '#13c2c2',
      task: '#eb2f96',
      document: '#2f54eb',
      ai: '#fa8c16'
    };
    return colors[type as keyof typeof colors] || '#1890ff';
  };

  // Ícones por tipo
  const getTypeIcon = (type: string) => {
    const icons = {
      info: '💡',
      success: '✅',
      warning: '⚠️',
      error: '❌',
      system: '⚙️',
      legal: '⚖️',
      task: '📋',
      document: '📄',
      ai: '🤖'
    };
    return icons[type as keyof typeof icons] || '📢';
  };

  // Conectar WebSocket
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;

    const socket = io('ws://localhost:5006', {
      auth: { token }
    });

    socket.on('connect', () => {
      console.log('Conectado ao WebSocket de notificações');
    });

    socket.on('new_notification', (notification: Notification) => {
      setNotifications(prev => [notification, ...prev]);
      setUnreadCount(prev => prev + 1);
      
      // Reproduzir som de notificação
      if (audioRef.current && settings?.browser_enabled) {
        audioRef.current.play().catch(console.error);
      }
      
      // Mostrar notificação nativa do browser
      if (settings?.browser_enabled && 'Notification' in window && Notification.permission === 'granted') {
        new Notification(`JurisIA - ${notification.title}`, {
          body: notification.message,
          icon: '/favicon.ico',
          tag: `notification-${notification.id}`
        });
      }
    });

    socket.on('unread_count_updated', (data: { count: number }) => {
      setUnreadCount(data.count);
    });

    socketRef.current = socket;

    return () => {
      socket.disconnect();
    };
  }, [settings]);

  // Carregar notificações
  const loadNotifications = async (append = false) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const params = {
        unread_only: filter === 'unread',
        limit: 20,
        offset: append ? notifications.length : 0
      };

      const response = await axios.get('/api/notifications', {
        headers: { Authorization: `Bearer ${token}` },
        params
      });

      if (response.data.success) {
        const newNotifications = response.data.data.notifications;
        setNotifications(prev => append ? [...prev, ...newNotifications] : newNotifications);
        setUnreadCount(response.data.data.unread_count);
      }
    } catch (error) {
      console.error('Erro ao carregar notificações:', error);
      message.error('Erro ao carregar notificações');
    } finally {
      setLoading(false);
    }
  };

  // Carregar configurações
  const loadSettings = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('/api/notifications/settings', {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        setSettings(response.data.data);
      }
    } catch (error) {
      console.error('Erro ao carregar configurações:', error);
    }
  };

  // Carregar estatísticas
  const loadStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('/api/notifications/stats', {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        setStats(response.data.data);
      }
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
    }
  };

  // Marcar como lida
  const markAsRead = async (notificationId: number) => {
    try {
      const token = localStorage.getItem('token');
      await axios.patch(`/api/notifications/${notificationId}/read`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setNotifications(prev => 
        prev.map(n => 
          n.id === notificationId 
            ? { ...n, is_read: true, read_at: new Date().toISOString() }
            : n
        )
      );
    } catch (error) {
      console.error('Erro ao marcar como lida:', error);
      message.error('Erro ao marcar notificação como lida');
    }
  };

  // Marcar todas como lidas
  const markAllAsRead = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.patch('/api/notifications/mark-all-read', {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setNotifications(prev => 
        prev.map(n => ({ ...n, is_read: true, read_at: new Date().toISOString() }))
      );
      setUnreadCount(0);
      message.success('Todas as notificações foram marcadas como lidas');
    } catch (error) {
      console.error('Erro ao marcar todas como lidas:', error);
      message.error('Erro ao marcar notificações como lidas');
    }
  };

  // Arquivar notificação
  const archiveNotification = async (notificationId: number) => {
    try {
      const token = localStorage.getItem('token');
      await axios.patch(`/api/notifications/${notificationId}/archive`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setNotifications(prev => prev.filter(n => n.id !== notificationId));
      message.success('Notificação arquivada');
    } catch (error) {
      console.error('Erro ao arquivar:', error);
      message.error('Erro ao arquivar notificação');
    }
  };

  // Deletar notificação
  const deleteNotification = async (notificationId: number) => {
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`/api/notifications/${notificationId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setNotifications(prev => prev.filter(n => n.id !== notificationId));
      message.success('Notificação removida');
    } catch (error) {
      console.error('Erro ao deletar:', error);
      message.error('Erro ao remover notificação');
    }
  };

  // Atualizar configurações
  const updateSettings = async (newSettings: Partial<NotificationSettings>) => {
    try {
      const token = localStorage.getItem('token');
      await axios.put('/api/notifications/settings', newSettings, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setSettings(prev => prev ? { ...prev, ...newSettings } : null);
      message.success('Configurações atualizadas');
    } catch (error) {
      console.error('Erro ao atualizar configurações:', error);
      message.error('Erro ao atualizar configurações');
    }
  };

  // Solicitar permissão para notificações do browser
  const requestNotificationPermission = async () => {
    if ('Notification' in window && Notification.permission === 'default') {
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        message.success('Notificações do navegador ativadas');
      }
    }
  };

  // Carregar dados iniciais
  useEffect(() => {
    loadNotifications();
    loadSettings();
    loadStats();
    requestNotificationPermission();
  }, [filter]);

  // Menu de filtros
  const filterMenu = (
    <Menu
      selectedKeys={[filter]}
      onClick={({ key }) => setFilter(key as 'all' | 'unread')}
    >
      <Menu.Item key="all">Todas</Menu.Item>
      <Menu.Item key="unread">Não lidas</Menu.Item>
    </Menu>
  );

  // Menu de ações em lote
  const actionMenu = (
    <Menu>
      <Menu.Item key="mark-all-read" onClick={markAllAsRead}>
        <CheckOutlined /> Marcar todas como lidas
      </Menu.Item>
      <Menu.Item key="refresh" onClick={() => loadNotifications()}>
        <ReloadOutlined /> Atualizar
      </Menu.Item>
    </Menu>
  );

  // Renderizar item de notificação
  const renderNotificationItem = (notification: Notification) => (
    <List.Item
      key={notification.id}
      className={`notification-item ${!notification.is_read ? 'unread' : ''}`}
      actions={[
        <Tooltip title="Marcar como lida">
          <Button 
            type="text" 
            size="small" 
            icon={<CheckOutlined />}
            onClick={() => markAsRead(notification.id)}
            disabled={notification.is_read}
          />
        </Tooltip>,
        <Tooltip title="Arquivar">
          <Button 
            type="text" 
            size="small" 
            icon={<InboxOutlined />}
            onClick={() => archiveNotification(notification.id)}
          />
        </Tooltip>,
        <Tooltip title="Remover">
          <Button 
            type="text" 
            size="small" 
            danger
            icon={<DeleteOutlined />}
            onClick={() => deleteNotification(notification.id)}
          />
        </Tooltip>
      ]}
    >
      <List.Item.Meta
        avatar={
          <div 
            className="notification-avatar"
            style={{ backgroundColor: getTypeColor(notification.type) }}
          >
            {getTypeIcon(notification.type)}
          </div>
        }
        title={
          <div className="notification-title">
            <Text strong={!notification.is_read}>
              {notification.title}
            </Text>
            <div className="notification-tags">
              <Tag color={getTypeColor(notification.type)} size="small">
                {notification.type}
              </Tag>
              {notification.priority === 'urgent' && (
                <Tag color="red" size="small">URGENTE</Tag>
              )}
              {notification.priority === 'high' && (
                <Tag color="orange" size="small">ALTA</Tag>
              )}
            </div>
          </div>
        }
        description={
          <div className="notification-content">
            <Text type="secondary" className={!notification.is_read ? 'unread-text' : ''}>
              {notification.message}
            </Text>
            <div className="notification-meta">
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {new Date(notification.created_at).toLocaleString()}
              </Text>
              {notification.action_url && (
                <Button 
                  type="link" 
                  size="small"
                  onClick={() => window.open(notification.action_url, '_blank')}
                >
                  {notification.action_text || 'Ver mais'}
                </Button>
              )}
            </div>
          </div>
        }
      />
    </List.Item>
  );

  // Conteúdo do popover
  const notificationContent = (
    <div className="notification-popover">
      <div className="notification-header">
        <Title level={4} style={{ margin: 0 }}>
          Notificações
          {stats && (
            <Text type="secondary" style={{ fontSize: '14px', marginLeft: '8px' }}>
              ({stats.unread} não lidas)
            </Text>
          )}
        </Title>
        <Space>
          <Dropdown overlay={filterMenu} trigger={['click']}>
            <Button type="text" size="small" icon={<FilterOutlined />} />
          </Dropdown>
          <Dropdown overlay={actionMenu} trigger={['click']}>
            <Button type="text" size="small" icon={<SettingOutlined />} />
          </Dropdown>
        </Space>
      </div>
      
      <Divider style={{ margin: '8px 0' }} />
      
      <div className="notification-list">
        {loading ? (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <Spin />
          </div>
        ) : notifications.length === 0 ? (
          <Empty 
            description="Nenhuma notificação encontrada"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            style={{ padding: '20px' }}
          />
        ) : (
          <List
            dataSource={notifications}
            renderItem={renderNotificationItem}
            size="small"
          />
        )}
      </div>
      
      {notifications.length > 0 && (
        <>
          <Divider style={{ margin: '8px 0' }} />
          <div style={{ textAlign: 'center' }}>
            <Button type="link" onClick={() => setVisible(false)}>
              Ver todas as notificações
            </Button>
          </div>
        </>
      )}
    </div>
  );

  return (
    <>
      <Popover
        content={notificationContent}
        title={null}
        trigger="click"
        visible={visible}
        onVisibleChange={setVisible}
        placement="bottomRight"
        overlayClassName="notification-popover-overlay"
        overlayStyle={{ width: '400px', maxHeight: '600px' }}
      >
        <Badge count={unreadCount} size="small" offset={[-2, 2]}>
          <Button 
            type="text" 
            icon={<BellOutlined />} 
            size="large"
            className="notification-trigger"
          />
        </Badge>
      </Popover>
      
      {/* Áudio para notificações */}
      <audio
        ref={audioRef}
        preload="auto"
        src="/notification-sound.mp3"
      />
    </>
  );
};

export default NotificationCenter; 