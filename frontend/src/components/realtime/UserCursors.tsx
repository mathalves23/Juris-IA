import React from 'react';
import { useCollaboration } from './CollaborationProvider';

interface UserCursor {
  id: string;
  name: string;
  x: number;
  y: number;
  color: string;
}

const CURSOR_COLORS = [
  '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57',
  '#FF9FF3', '#54A0FF', '#5F27CD', '#00D2D3', '#FF9F43'
];

export const UserCursors: React.FC = () => {
  const { activeUsers, currentUser, sendEvent } = useCollaboration();
  const [cursors, setCursors] = React.useState<UserCursor[]>([]);

  React.useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (currentUser) {
        sendEvent({
          type: 'cursor_move',
          data: { x: e.clientX, y: e.clientY }
        });
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [currentUser, sendEvent]);

  React.useEffect(() => {
    // Converter usuários ativos para cursores
    const newCursors: UserCursor[] = activeUsers
      .filter(user => user.id !== currentUser?.id && user.cursor)
      .map((user, index) => ({
        id: user.id,
        name: user.name,
        x: user.cursor!.x,
        y: user.cursor!.y,
        color: CURSOR_COLORS[index % CURSOR_COLORS.length]
      }));

    setCursors(newCursors);
  }, [activeUsers, currentUser]);

  return (
    <div className="fixed inset-0 pointer-events-none z-50">
      {cursors.map(cursor => (
        <div
          key={cursor.id}
          className="absolute transition-all duration-100 ease-out"
          style={{
            left: cursor.x,
            top: cursor.y,
            transform: 'translate(-2px, -2px)'
          }}
        >
          {/* Cursor SVG */}
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            className="drop-shadow-sm"
          >
            <path
              d="M8.5 2.5L5.5 19.5L9.5 15.5L13.5 19.5L8.5 2.5Z"
              fill={cursor.color}
              stroke="white"
              strokeWidth="1"
            />
          </svg>
          
          {/* Nome do usuário */}
          <div
            className="absolute top-6 left-2 px-2 py-1 text-xs text-white rounded-md shadow-lg whitespace-nowrap"
            style={{ backgroundColor: cursor.color }}
          >
            {cursor.name}
          </div>
        </div>
      ))}
    </div>
  );
};

export default UserCursors; 