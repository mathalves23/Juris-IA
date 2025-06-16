import React from 'react';

// Contexto simples de autenticação
const AuthContext = React.createContext({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  login: async () => {},
  logout: () => {},
  register: async () => {}
});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = React.useState({ 
    id: 1, 
    nome: 'Advogado Demo', 
    email: 'advogado@jurisia.com',
    telefone: '(11) 99999-9999',
    oab: '123456/SP'
  });
  const [isLoading, setIsLoading] = React.useState(false);
  const [isAuthenticated, setIsAuthenticated] = React.useState(true);
  
  const login = async (email, password) => {
    console.log('Login demo:', email, password);
    setIsLoading(true);
    // Simular delay de autenticação
    await new Promise(resolve => setTimeout(resolve, 800));
    setIsAuthenticated(true);
    setIsLoading(false);
    return Promise.resolve({
      user,
      accessToken: 'demo-token-' + Date.now()
    });
  };

  const register = async (nome, email, password) => {
    console.log('Register demo:', nome, email, password);
    setIsLoading(true);
    await new Promise(resolve => setTimeout(resolve, 800));
    const newUser = { ...user, nome, email };
    setUser(newUser);
    setIsAuthenticated(true);
    setIsLoading(false);
    return Promise.resolve({
      user: newUser,
      accessToken: 'demo-token-' + Date.now()
    });
  };

  const logout = () => {
    console.log('Logout demo');
    setIsAuthenticated(false);
    setUser(null);
  };

  const contextValue = {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    register
  };

  return React.createElement(
    AuthContext.Provider,
    { value: contextValue },
    children
  );
};

export const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider');
  }
  return context;
}; 