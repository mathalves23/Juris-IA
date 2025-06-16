import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  className?: string;
  overlay?: boolean;
}

const Loading: React.FC<LoadingProps> = ({ 
  size = 'md', 
  text = 'Carregando...', 
  className = '',
  overlay = false
}) => {
  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'w-4 h-4';
      case 'md':
        return 'w-6 h-6';
      case 'lg':
        return 'w-8 h-8';
      default:
        return 'w-6 h-6';
    }
  };

  const getTextSize = () => {
    switch (size) {
      case 'sm':
        return 'text-sm';
      case 'md':
        return 'text-base';
      case 'lg':
        return 'text-lg';
      default:
        return 'text-base';
    }
  };

  const loadingContent = (
    <div className={`flex flex-col items-center justify-center space-y-2 ${className}`}>
      <Loader2 className={`${getSizeClasses()} animate-spin text-blue-600`} />
      {text && (
        <p className={`${getTextSize()} text-gray-600 font-medium`}>
          {text}
        </p>
      )}
    </div>
  );

  if (overlay) {
    return (
      <div className="fixed inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50">
        <div className="bg-white p-6 rounded-lg shadow-lg">
          {loadingContent}
        </div>
      </div>
    );
  }

  return loadingContent;
};

// Componente específico para botões
export const ButtonLoading: React.FC<{ text?: string }> = ({ text = 'Processando...' }) => (
  <div className="flex items-center space-x-2">
    <Loader2 className="w-4 h-4 animate-spin" />
    <span>{text}</span>
  </div>
);

// Componente para seções da página
export const SectionLoading: React.FC<{ text?: string }> = ({ text = 'Carregando dados...' }) => (
  <div className="flex flex-col items-center justify-center py-12 space-y-4">
    <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
    <p className="text-gray-600 text-lg font-medium">{text}</p>
    <div className="w-32 h-1 bg-gray-200 rounded overflow-hidden">
      <div className="w-full h-full bg-blue-600 animate-pulse"></div>
    </div>
  </div>
);

// Componente para lista de itens carregando
export const ListLoading: React.FC<{ count?: number }> = ({ count = 3 }) => (
  <div className="space-y-4">
    {Array.from({ length: count }, (_, index) => (
      <div key={index} className="animate-pulse">
        <div className="bg-gray-200 rounded-lg p-4 space-y-3">
          <div className="h-4 bg-gray-300 rounded w-3/4"></div>
          <div className="h-3 bg-gray-300 rounded w-1/2"></div>
          <div className="h-3 bg-gray-300 rounded w-5/6"></div>
        </div>
      </div>
    ))}
  </div>
);

export default Loading; 