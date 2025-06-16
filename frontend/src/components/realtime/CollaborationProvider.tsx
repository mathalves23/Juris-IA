import React from 'react';
import toast from 'react-hot-toast';

interface User {
  id: string;
  name: string;
  email: string;
  cursor?: { x: number; y: number };
  lastSeen: Date;
}

interface CollaborationEvent {
  type: 'user_joined' | 'user_left' | 'cursor_move' | 'text_change' | 'selection_change';
  userId: string;
  data: any;
  timestamp: Date;
}

interface CollaborationContextType {
  isConnected: boolean;
  activeUsers: User[];
  currentUser: User | null;
  connect: (documentId: string, user: User) => void;
  disconnect: () => void;
  sendEvent: (event: Omit<CollaborationEvent, 'userId' | 'timestamp'>) => void;
  onEvent: (callback: (event: CollaborationEvent) => void) => () => void;
}

const CollaborationContext = React.createContext<CollaborationContextType | null>(null);

export const useCollaboration = () => {
  const context = React.useContext(CollaborationContext);
  if (!context) {
    throw new Error('useCollaboration deve ser usado dentro de CollaborationProvider');
  }
  return context;
};

interface CollaborationProviderProps {
  children: React.ReactNode;
  wsUrl?: string;
}

export const CollaborationProvider: React.FC<CollaborationProviderProps> = ({
  children,
  wsUrl = 'ws://localhost:5005/ws/collaboration'
}) => {
  const [ws, setWs] = React.useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = React.useState(false);
  const [activeUsers, setActiveUsers] = React.useState<User[]>([]);
  const [currentUser, setCurrentUser] = React.useState<User | null>(null);
  const [eventCallbacks, setEventCallbacks] = React.useState<((event: CollaborationEvent) => void)[]>([]);

  const connect = React.useCallback((documentId: string, user: User) => {
    if (ws) {
      ws.close();
    }

    const newWs = new WebSocket(`${wsUrl}/${documentId}`);
    
    newWs.onopen = () => {
      setIsConnected(true);
      setCurrentUser(user);
      
      newWs.send(JSON.stringify({
        type: 'user_joined',
        data: user
      }));
      
      toast.success('Conectado para colaboração em tempo real');
    };

    newWs.onmessage = (event) => {
      try {
        const collaborationEvent: CollaborationEvent = JSON.parse(event.data);
        
        if (collaborationEvent.type === 'user_joined') {
          setActiveUsers(prev => {
            const exists = prev.find(u => u.id === collaborationEvent.data.id);
            if (!exists) {
              return [...prev, { ...collaborationEvent.data, lastSeen: new Date() }];
            }
            return prev.map(u => u.id === collaborationEvent.data.id 
              ? { ...u, lastSeen: new Date() } 
              : u
            );
          });
        } else if (collaborationEvent.type === 'user_left') {
          setActiveUsers(prev => prev.filter(u => u.id !== collaborationEvent.userId));
        }

        eventCallbacks.forEach(callback => callback(collaborationEvent));
      } catch (error) {
        console.error('Erro ao processar evento de colaboração:', error);
      }
    };

    newWs.onclose = () => {
      setIsConnected(false);
      setActiveUsers([]);
      setCurrentUser(null);
      toast.error('Conexão de colaboração perdida');
    };

    newWs.onerror = (error) => {
      console.error('Erro na conexão WebSocket:', error);
      toast.error('Erro na colaboração em tempo real');
    };

    setWs(newWs);
  }, [wsUrl, eventCallbacks]);

  const disconnect = React.useCallback(() => {
    if (ws) {
      ws.close();
      setWs(null);
    }
  }, [ws]);

  const sendEvent = React.useCallback((event: Omit<CollaborationEvent, 'userId' | 'timestamp'>) => {
    if (ws && isConnected && currentUser) {
      ws.send(JSON.stringify({
        ...event,
        userId: currentUser.id,
        timestamp: new Date()
      }));
    }
  }, [ws, isConnected, currentUser]);

  const onEvent = React.useCallback((callback: (event: CollaborationEvent) => void) => {
    setEventCallbacks(prev => [...prev, callback]);
    
    return () => {
      setEventCallbacks(prev => prev.filter(cb => cb !== callback));
    };
  }, []);

  React.useEffect(() => {
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [ws]);

  const value: CollaborationContextType = {
    isConnected,
    activeUsers,
    currentUser,
    connect,
    disconnect,
    sendEvent,
    onEvent
  };

  return (
    <CollaborationContext.Provider value={value}>
      {children}
    </CollaborationContext.Provider>
  );
}; 