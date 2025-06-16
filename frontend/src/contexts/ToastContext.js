import React from 'react';

// Contexto simples para toasts
const ToastContext = React.createContext({
  showToast: () => {},
  hideToast: () => {},
  success: () => {},
  error: () => {}
});

export const ToastProvider = ({ children }) => {
  const showToast = (message, type = 'info') => {
    console.log(`Toast: ${message} (${type})`);
  };

  const hideToast = (id) => {
    console.log(`Hide toast: ${id}`);
  };

  const success = (message) => {
    console.log(`Success: ${message}`);
  };

  const error = (message) => {
    console.error(`Error: ${message}`);
  };

  const contextValue = {
    showToast,
    hideToast,
    success,
    error
  };

  return React.createElement(
    ToastContext.Provider,
    { value: contextValue },
    children
  );
};

export const useToast = () => {
  const context = React.useContext(ToastContext);
  if (!context) {
    throw new Error('useToast deve ser usado dentro de um ToastProvider');
  }
  return context;
}; 