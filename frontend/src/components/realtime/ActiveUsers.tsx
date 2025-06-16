import React from 'react';
import { useCollaboration } from './CollaborationProvider';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

const AVATAR_COLORS = [
  'bg-red-500', 'bg-blue-500', 'bg-green-500', 'bg-yellow-500',
  'bg-purple-500', 'bg-pink-500', 'bg-indigo-500', 'bg-teal-500'
];

const getInitials = (name: string): string => {
  return name
    .split(' ')
    .map(part => part.charAt(0))
    .join('')
    .toUpperCase()
    .slice(0, 2);
};

export const ActiveUsers = () => {
  const { isConnected, activeUsers, currentUser } = useCollaboration();

  if (!isConnected) {
    return (
      React.createElement('div', { className: "flex items-center space-x-2 text-sm text-gray-500" },
        React.createElement('div', { className: "w-2 h-2 bg-gray-400 rounded-full" }),
        React.createElement('span', null, 'Offline')
      )
    );
  }

  return (
    React.createElement('div', { className: "flex items-center space-x-3" },
      React.createElement('div', { className: "flex items-center space-x-2 text-sm text-green-600" },
        React.createElement('div', { className: "w-2 h-2 bg-green-500 rounded-full animate-pulse" }),
        React.createElement('span', null, 'Online')
      ),
      React.createElement('div', { className: "flex -space-x-2" },
        activeUsers.map((user, index) =>
          React.createElement('div', {
            key: user.id,
            className: "relative group",
            title: `${user.name} - Último acesso: ${format(user.lastSeen, 'HH:mm', { locale: ptBR })}`
          },
            React.createElement('div', {
              className: `
                w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-medium
                ring-2 ring-white hover:ring-blue-200 cursor-pointer transition-all
                ${AVATAR_COLORS[index % AVATAR_COLORS.length]}
                ${user.id === currentUser?.id ? 'ring-blue-400' : ''}
              `
            }, getInitials(user.name)),
            
            React.createElement('div', { className: "absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10" },
              React.createElement('div', { className: "font-medium" }, user.name),
              React.createElement('div', { className: "text-gray-300" }, user.email),
              React.createElement('div', { className: "text-gray-400" },
                `Último acesso: ${format(user.lastSeen, 'HH:mm', { locale: ptBR })}`
              ),
              React.createElement('div', { className: "absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900" })
            ),

            user.id === currentUser?.id && 
            React.createElement('div', { className: "absolute -bottom-1 -right-1 w-3 h-3 bg-blue-500 rounded-full border-2 border-white" })
          )
        )
      ),
      
      activeUsers.length > 0 && 
      React.createElement('span', { className: "text-sm text-gray-600" },
        `${activeUsers.length} ${activeUsers.length === 1 ? 'usuário' : 'usuários'} conectado${activeUsers.length === 1 ? '' : 's'}`
      )
    )
  );
};

export default ActiveUsers; 