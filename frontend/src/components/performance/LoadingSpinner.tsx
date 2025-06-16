import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  className?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  text = 'Carregando...',
  className = ''
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  };

  return (
    React.createElement('div', { 
      className: `flex flex-col items-center justify-center p-8 ${className}` 
    },
      React.createElement('div', {
        className: `animate-spin rounded-full border-4 border-gray-200 border-t-blue-600 ${sizeClasses[size]}`
      }),
      text && React.createElement('p', { 
        className: "mt-4 text-sm text-gray-600" 
      }, text)
    )
  );
};

export default LoadingSpinner; 