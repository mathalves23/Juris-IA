import api from './api';

export interface LoginData {
  email: string;
  password: string;
}

export interface RegisterData {
  name: string;
  email: string;
  password: string;
}

export interface User {
  id: number;
  nome: string;
  email: string;
  plano: 'trial' | 'editor_ia' | 'completo';
  limite_documentos: number;
  ativo: boolean;
}

export interface AuthResponse {
  access_token: string;
  user: User;
}

export const login = async (email: string, password: string): Promise<AuthResponse> => {
  try {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.message || 'Erro no login');
  }
};

export const register = async (name: string, email: string, password: string): Promise<AuthResponse> => {
  try {
    const response = await api.post('/auth/register', { 
      nome: name,
      email, 
      password 
    });
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.message || 'Erro no registro');
  }
};

export const verifyToken = async (token: string): Promise<boolean> => {
  try {
    const response = await api.get('/auth/verify', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response.status === 200;
  } catch (error) {
    return false;
  }
};

export const getCurrentUser = async (): Promise<User> => {
  try {
    const response = await api.get('/auth/me');
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.message || 'Erro ao buscar usuário');
  }
};

export const setFlagsFromString = async (flags: string, environment: 'test' | 'prod' = 'test'): Promise<any> => {
  try {
    const response = await api.post('/auth/set-flags', { 
      flags, 
      environment 
    });
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.message || 'Erro ao configurar flags');
  }
};

export const getFlags = async (environment: 'test' | 'prod' = 'test'): Promise<any> => {
  try {
    const response = await api.get(`/auth/flags?environment=${environment}`);
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.message || 'Erro ao buscar flags');
  }
};