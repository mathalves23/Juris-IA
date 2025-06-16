import axios from 'axios';

// Configurar baseURL para sempre usar o backend real
const baseURL = process.env.NODE_ENV === 'production' 
  ? process.env.REACT_APP_API_URL || 'https://jurisia-api.onrender.com/api'  // URL de produção temporária
  : 'http://localhost:5005/api';   // URL de desenvolvimento

const api = axios.create({
  baseURL,
  timeout: 10000, // 10 segundos
});

// Interceptor para adicionar token de autenticação
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    config.headers['Content-Type'] = 'application/json';
    return config;
  },
  (error) => {
    console.error('Erro na requisição:', error);
    return Promise.reject(error);
  }
);

// Interceptor para tratamento de erros
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('Erro na resposta:', error);
    
    if (error.response && error.response.status === 401) {
      // Token expirado ou inválido
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      window.location.href = '/login';
    }
    
    if (error.response && error.response.status === 403) {
      // Acesso negado
      console.warn('Acesso negado ao recurso');
    }
    
    if (error.response && error.response.status >= 500) {
      // Erro do servidor
      console.error('Erro interno do servidor');
    }
    
    return Promise.reject(error);
  }
);

// Serviço de autenticação
export const authService = {
  login: async (email: string, senha: string) => {
    const response = await api.post('/auth/login', { email, senha });
    return response.data;
  },
  
  register: async (nome: string, email: string, senha: string) => {
    const response = await api.post('/auth/register', { nome, email, senha });
    return response.data;
  },
  
  refreshToken: async (refreshToken: string) => {
    const response = await api.post('/auth/refresh', { refreshToken });
    return response.data;
  },
  
  getUserInfo: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
  
  updateUser: async (userData: any) => {
    const response = await api.put('/auth/me', userData);
    return response.data;
  }
};

// Serviço de documentos
export const documentService = {
  getAll: async () => {
    const response = await api.get('/documents');
    return response.data;
  },
  
  getDocuments: async () => {
    const response = await api.get('/documents');
    return { documents: response.data };
  },
  
  getById: async (id: number) => {
    const response = await api.get(`/documents/${id}`);
    return response.data;
  },
  
  getDocument: async (id: number) => {
    const response = await api.get(`/documents/${id}`);
    return { document: response.data };
  },
  
  create: async (document: any) => {
    const response = await api.post('/documents', document);
    return response.data;
  },
  
  createDocument: async (document: any) => {
    const response = await api.post('/documents', document);
    return { document: response.data };
  },
  
  update: async (id: number, document: any) => {
    const response = await api.put(`/documents/${id}`, document);
    return response.data;
  },
  
  updateDocument: async (id: number, document: any) => {
    const response = await api.put(`/documents/${id}`, document);
    return { document: response.data };
  },
  
  delete: async (id: number) => {
    const response = await api.delete(`/documents/${id}`);
    return response.data;
  },
  
  deleteDocument: async (id: number) => {
    const response = await api.delete(`/documents/${id}`);
    return response.data;
  },
  
  getDocumentVersions: async (id: number) => {
    const response = await api.get(`/documents/${id}/versions`);
    return { versions: response.data };
  },
  
  restoreDocumentVersion: async (id: number, versionId: number) => {
    const response = await api.post(`/documents/${id}/versions/${versionId}/restore`);
    return { document: response.data };
  }
};

// Serviço de templates
export const templateService = {
  getAll: async () => {
    const response = await api.get('/templates');
    return response.data;
  },
  
  getTemplates: async () => {
    const response = await api.get('/templates');
    return { templates: response.data };
  },
  
  getById: async (id: number) => {
    const response = await api.get(`/templates/${id}`);
    return response.data;
  },
  
  getTemplate: async (id: number) => {
    const response = await api.get(`/templates/${id}`);
    return { template: response.data };
  },
  
  create: async (template: any) => {
    const response = await api.post('/templates', template);
    return response.data;
  },
  
  createTemplate: async (template: any) => {
    const response = await api.post('/templates', template);
    return { template: response.data };
  },
  
  update: async (id: number, template: any) => {
    const response = await api.put(`/templates/${id}`, template);
    return response.data;
  },
  
  updateTemplate: async (id: number, template: any) => {
    const response = await api.put(`/templates/${id}`, template);
    return { template: response.data };
  },
  
  delete: async (id: number) => {
    const response = await api.delete(`/templates/${id}`);
    return response.data;
  },
  
  deleteTemplate: async (id: number) => {
    const response = await api.delete(`/templates/${id}`);
    return response.data;
  },
  
  getCategories: async () => {
    const response = await api.get('/templates/categories');
    return { categories: response.data };
  }
};

// Serviço de IA - INTEGRAÇÃO REAL COM CHATGPT
export const aiService = {
  generateText: async (promptData: { prompt: string; context?: string; document_id?: number; document_type?: string }) => {
    const response = await api.post('/ai/generate', promptData);
    return { generated_text: response.data.generated_text || response.data.content };
  },
  
  extractVariables: async (content: string) => {
    const response = await api.post('/ai/extract-variables', { content });
    return { variables: response.data.variables };
  },
  
  reviewContent: async (content: string) => {
    const response = await api.post('/ai/review', { content });
    return response.data;
  },
  
  summarizeContent: async (content: string) => {
    const response = await api.post('/ai/summarize', { content });
    return response.data;
  }
};

// Serviço de upload
export const uploadService = {
  uploadDocument: async (file: File, titulo?: string, categoria?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (titulo) formData.append('titulo', titulo);
    if (categoria) formData.append('categoria', categoria);
    
    const response = await api.post('/upload/document', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  
  analyzeDocument: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/upload/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }
};

// Serviço de exportação
export const exportService = {
  exportDocumentPDF: async (documentId: number) => {
    const response = await api.get(`/export/document/${documentId}/pdf`, {
      responseType: 'blob',
    });
    return response.data;
  },
  
  exportDocumentDOCX: async (documentId: number) => {
    const response = await api.get(`/export/document/${documentId}/docx`, {
      responseType: 'blob',
    });
    return response.data;
  },
  
  exportTemplatePDF: async (templateId: number, variables: Record<string, string>) => {
    const response = await api.post(`/export/template/${templateId}/pdf`, { variables }, {
      responseType: 'blob',
    });
    return response.data;
  },
  
  exportTemplateDOCX: async (templateId: number, variables: Record<string, string>) => {
    const response = await api.post(`/export/template/${templateId}/docx`, { variables }, {
      responseType: 'blob',
    });
    return response.data;
  }
};

// Serviço de clientes
export const clientService = {
  getAll: async () => {
    const response = await api.get('/clients');
    return response.data;
  },
  
  getById: async (id: number) => {
    const response = await api.get(`/clients/${id}`);
    return response.data;
  },
  
  create: async (client: any) => {
    const response = await api.post('/clients', client);
    return response.data;
  },
  
  update: async (id: number, client: any) => {
    const response = await api.put(`/clients/${id}`, client);
    return response.data;
  },
  
  delete: async (id: number) => {
    const response = await api.delete(`/clients/${id}`);
    return response.data;
  }
};

// Serviço de processos
export const processService = {
  getAll: async () => {
    const response = await api.get('/processes');
    return response.data;
  },
  
  getById: async (id: number) => {
    const response = await api.get(`/processes/${id}`);
    return response.data;
  },
  
  create: async (process: any) => {
    const response = await api.post('/processes', process);
    return response.data;
  },
  
  update: async (id: number, process: any) => {
    const response = await api.put(`/processes/${id}`, process);
    return response.data;
  },
  
  delete: async (id: number) => {
    const response = await api.delete(`/processes/${id}`);
    return response.data;
  }
};

// Serviço de kanban
export const kanbanService = {
  getBoards: async () => {
    const response = await api.get('/kanban/boards');
    return response.data;
  },
  
  getBoard: async (id: number) => {
    const response = await api.get(`/kanban/boards/${id}`);
    return response.data;
  },
  
  createBoard: async (board: any) => {
    const response = await api.post('/kanban/boards', board);
    return response.data;
  },
  
  updateBoard: async (id: number, board: any) => {
    const response = await api.put(`/kanban/boards/${id}`, board);
    return response.data;
  },
  
  deleteBoard: async (id: number) => {
    const response = await api.delete(`/kanban/boards/${id}`);
    return response.data;
  }
};

// Serviço de wiki
export const wikiService = {
  getAll: async () => {
    const response = await api.get('/wiki');
    return response.data;
  },
  
  getById: async (id: number) => {
    const response = await api.get(`/wiki/${id}`);
    return response.data;
  },
  
  create: async (wiki: any) => {
    const response = await api.post('/wiki', wiki);
    return response.data;
  },
  
  update: async (id: number, wiki: any) => {
    const response = await api.put(`/wiki/${id}`, wiki);
    return response.data;
  },
  
  delete: async (id: number) => {
    const response = await api.delete(`/wiki/${id}`);
    return response.data;
  }
};

// Serviço de notificações
export const notificationService = {
  getAll: async () => {
    const response = await api.get('/notifications');
    return response.data;
  },
  
  markAsRead: async (id: number) => {
    const response = await api.put(`/notifications/${id}/read`);
    return response.data;
  },
  
  delete: async (id: number) => {
    const response = await api.delete(`/notifications/${id}`);
    return response.data;
  }
};

export default api;
