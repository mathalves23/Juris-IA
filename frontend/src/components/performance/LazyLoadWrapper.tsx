import React, { Suspense } from 'react';
import LoadingSpinner from './LoadingSpinner';

interface LazyLoadWrapperProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  errorFallback?: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ReactNode },
  ErrorBoundaryState
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Erro no componente lazy:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        React.createElement('div', { 
          className: "flex items-center justify-center p-8 text-red-600" 
        },
          React.createElement('div', { className: "text-center" },
            React.createElement('h3', { className: "text-lg font-medium mb-2" }, 'Erro ao carregar componente'),
            React.createElement('p', { className: "text-sm text-gray-500" }, 'Tente recarregar a página'),
            React.createElement('button', {
              className: "mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600",
              onClick: () => this.setState({ hasError: false })
            }, 'Tentar novamente')
          )
        )
      );
    }

    return this.props.children;
  }
}

export const LazyLoadWrapper: React.FC<LazyLoadWrapperProps> = ({
  children,
  fallback,
  errorFallback
}) => {
  return (
    React.createElement(ErrorBoundary, { fallback: errorFallback },
      React.createElement(Suspense, { 
        fallback: fallback || React.createElement(LoadingSpinner, null)
      }, children)
    )
  );
};

export default LazyLoadWrapper; 