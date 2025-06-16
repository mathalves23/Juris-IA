import React from 'react';

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
}

const Loading = ({ size = 'md', text = 'Carregando...' }: LoadingProps) => {
  const getSizeClass = (s: string) => {
    switch (s) {
      case 'sm': return 'h-16 w-16';
      case 'lg': return 'h-48 w-48';
      default: return 'h-32 w-32';
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <div className={`animate-spin rounded-full border-b-2 border-indigo-600 ${getSizeClass(size)}`}></div>
      {text && <p className="mt-4 text-gray-600">{text}</p>}
    </div>
  );
};

interface ButtonLoadingProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
}

export const ButtonLoading = ({ size = 'sm', text = 'Carregando...' }: ButtonLoadingProps) => {
  const getSizeClass = (s: string) => {
    switch (s) {
      case 'md': return 'h-6 w-6';
      case 'lg': return 'h-8 w-8';
      default: return 'h-4 w-4';
    }
  };

  return (
    <div className="flex items-center justify-center space-x-2">
      <div className={`animate-spin rounded-full border-b-2 border-white ${getSizeClass(size)}`}></div>
      <span>{text}</span>
    </div>
  );
};

export default Loading; 