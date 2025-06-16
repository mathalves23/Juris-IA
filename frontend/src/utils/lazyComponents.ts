import { lazy } from 'react';

// Lazy loading dos principais componentes da aplicação
export const LazyDashboard = lazy(() => 
  import('../pages/Dashboard').then(module => ({ default: module.Dashboard }))
);

export const LazyDocumentEditor = lazy(() => 
  import('../pages/documents/DocumentEditor').then(module => ({ default: module.DocumentEditor }))
);

export const LazyTemplateEditor = lazy(() => 
  import('../pages/templates/TemplateEditor').then(module => ({ default: module.TemplateEditor }))
);

export const LazyKanbanBoard = lazy(() => 
  import('../pages/kanban/KanbanBoard').then(module => ({ default: module.KanbanBoard }))
);

export const LazyClientManagement = lazy(() => 
  import('../pages/clients/ClientManagement').then(module => ({ default: module.ClientManagement }))
);

export const LazyProcessManagement = lazy(() => 
  import('../pages/processes/ProcessManagement').then(module => ({ default: module.ProcessManagement }))
);

export const LazyWikiPage = lazy(() => 
  import('../pages/wiki/WikiPage').then(module => ({ default: module.WikiPage }))
);

export const LazyNotifications = lazy(() => 
  import('../pages/notifications/NotificationCenter').then(module => ({ default: module.NotificationCenter }))
);

export const LazyAnalytics = lazy(() => 
  import('../pages/analytics/Analytics').then(module => ({ default: module.Analytics }))
);

export const LazySettings = lazy(() => 
  import('../pages/settings/Settings').then(module => ({ default: module.Settings }))
);

export const LazyUserProfile = lazy(() => 
  import('../pages/profile/UserProfile').then(module => ({ default: module.UserProfile }))
);

// Lazy loading de componentes específicos
export const LazyPDFViewer = lazy(() => 
  import('../components/documents/PDFViewer').then(module => ({ default: module.PDFViewer }))
);

export const LazyRichTextEditor = lazy(() => 
  import('../components/editor/RichTextEditor').then(module => ({ default: module.RichTextEditor }))
);

export const LazyDataTable = lazy(() => 
  import('../components/common/DataTable').then(module => ({ default: module.DataTable }))
);

export const LazyChartDashboard = lazy(() => 
  import('../components/analytics/ChartDashboard').then(module => ({ default: module.ChartDashboard }))
);

export const LazyFileUpload = lazy(() => 
  import('../components/upload/FileUpload').then(module => ({ default: module.FileUpload }))
);

// Função utilitária para preload de componentes
export const preloadComponent = (componentLoader: () => Promise<any>) => {
  // Precarrega o componente em background
  componentLoader().catch(error => {
    console.warn('Erro ao precarregar componente:', error);
  });
};

// Preload estratégico baseado na rota atual
export const preloadRouteComponents = (currentRoute: string) => {
  switch (currentRoute) {
    case '/dashboard':
      // Precarrega componentes relacionados ao dashboard
      preloadComponent(() => import('../pages/documents/DocumentEditor'));
      preloadComponent(() => import('../components/analytics/ChartDashboard'));
      break;
    
    case '/documents':
      // Precarrega editor e PDF viewer
      preloadComponent(() => import('../pages/documents/DocumentEditor'));
      preloadComponent(() => import('../components/documents/PDFViewer'));
      break;
    
    case '/templates':
      // Precarrega editor de templates
      preloadComponent(() => import('../pages/templates/TemplateEditor'));
      preloadComponent(() => import('../components/editor/RichTextEditor'));
      break;
    
    case '/kanban':
      // Precarrega board do Kanban
      preloadComponent(() => import('../pages/kanban/KanbanBoard'));
      break;
    
    case '/clients':
      // Precarrega gerenciamento de clientes e processos
      preloadComponent(() => import('../pages/clients/ClientManagement'));
      preloadComponent(() => import('../pages/processes/ProcessManagement'));
      break;
    
    default:
      // Preload básico
      preloadComponent(() => import('../pages/Dashboard'));
      break;
  }
};

// Função para lazy loading condicional
export const createConditionalLazy = <T>(
  condition: () => boolean,
  componentLoader: () => Promise<{ default: T }>,
  fallbackLoader: () => Promise<{ default: T }>
) => {
  return lazy(() => {
    if (condition()) {
      return componentLoader();
    } else {
      return fallbackLoader();
    }
  });
};

// Cache de componentes carregados
const loadedComponents = new Set<string>();

export const loadComponentOnce = (
  componentName: string,
  loader: () => Promise<any>
): Promise<any> => {
  if (loadedComponents.has(componentName)) {
    return Promise.resolve();
  }
  
  loadedComponents.add(componentName);
  return loader();
};

// Função para loading com retry
export const createRetryableLazy = <T>(
  componentLoader: () => Promise<{ default: T }>,
  maxRetries: number = 3
) => {
  return lazy(() => {
    let retries = 0;
    
    const tryLoad = (): Promise<{ default: T }> => {
      return componentLoader().catch(error => {
        if (retries < maxRetries) {
          retries++;
          console.warn(`Tentativa ${retries} de carregamento falhou, tentando novamente...`);
          return new Promise(resolve => {
            setTimeout(() => resolve(tryLoad()), 1000 * retries);
          });
        }
        throw error;
      });
    };
    
    return tryLoad();
  });
}; 