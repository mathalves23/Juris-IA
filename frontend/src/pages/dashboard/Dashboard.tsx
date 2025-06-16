import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext.js';
import { useToast } from '../../contexts/ToastContext.js';
import { documentService, templateService } from '../../services/api';
import Loading from '../../components/Loading';

const Dashboard = () => {
  const { user, subscription } = useAuth();
  const { showToast } = useToast();
  const [recentDocuments, setRecentDocuments] = React.useState<any[]>([]);
  const [recentTemplates, setRecentTemplates] = React.useState<any[]>([]);
  const [stats, setStats] = React.useState({
    totalDocuments: 0,
    totalTemplates: 0,
    documentsThisMonth: 0,
    templatesCreated: 0
  });
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setIsLoading(true);
        
        // Buscar documentos recentes
        const documents = await documentService.getAll();
        setRecentDocuments(documents.slice(0, 6));
        
        // Buscar templates recentes
        const templates = await templateService.getAll();
        setRecentTemplates(templates.slice(0, 6));
        
        // Calcular estatísticas
        const currentMonth = new Date().getMonth();
        const currentYear = new Date().getFullYear();
        
        const documentsThisMonth = documents.filter((doc: any) => {
          const docDate = new Date(doc.created_at);
          return docDate.getMonth() === currentMonth && docDate.getFullYear() === currentYear;
        }).length;
        
        setStats({
          totalDocuments: documents.length,
          totalTemplates: templates.length,
          documentsThisMonth,
          templatesCreated: templates.filter((t: any) => t.user_id === user?.id).length
        });
        
      } catch (err) {
        showToast({ type: 'error', title: 'Erro ao carregar dados do dashboard' });
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, [user?.id, showToast]);

  if (isLoading) {
    return <Loading />;
  }

  const quickActions = [
    {
      title: 'Novo Documento',
      description: 'Criar documento do zero',
      icon: '📝',
      href: '/documents/new',
      color: 'bg-blue-500 hover:bg-blue-600'
    },
    {
      title: 'Novo Template',
      description: 'Criar modelo personalizado',
      icon: '📄',
      href: '/templates/new',
      color: 'bg-green-500 hover:bg-green-600'
    },
    {
      title: 'IA Jurídica',
      description: 'Gerar texto com IA',
      icon: '🤖',
      href: '/ai',
      color: 'bg-purple-500 hover:bg-purple-600'
    },
    {
      title: 'Upload de Arquivo',
      description: 'Importar documento existente',
      icon: '📁',
      href: '/upload',
      color: 'bg-orange-500 hover:bg-orange-600'
    }
  ];

  const statsCards = [
    {
      title: 'Total de Documentos',
      value: stats.totalDocuments,
      icon: '📊',
             change: subscription?.documentos_utilizados && subscription?.limite_documentos ? 
         `${Math.round((subscription.documentos_utilizados / subscription.limite_documentos) * 100)}% do limite usado` :
         'Sem limite',
       changeType: subscription?.documentos_utilizados && subscription?.limite_documentos && 
         subscription.documentos_utilizados > subscription.limite_documentos * 0.8 ? 'warning' : 'positive'
    },
    {
      title: 'Documentos este Mês',
      value: stats.documentsThisMonth,
      icon: '📈',
      change: 'Criados recentemente',
      changeType: 'neutral'
    },
    {
      title: 'Meus Templates',
      value: stats.templatesCreated,
      icon: '🗂️',
      change: `${stats.totalTemplates} disponíveis`,
      changeType: 'positive'
    },
    {
      title: 'Plano Atual',
      value: subscription?.plano || 'Premium',
      icon: '⭐',
      change: subscription?.status === 'ativo' ? 'Ativo' : 'Inativo',
      changeType: subscription?.status === 'ativo' ? 'positive' : 'warning'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Header Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Bem-vindo, {user?.nome}! 👋
              </h1>
              <p className="mt-2 text-lg text-gray-600">
                Gerencie seus documentos jurídicos com tecnologia IA
              </p>
            </div>
            <div className="hidden md:flex items-center space-x-3">
              <div className="bg-white rounded-lg shadow-sm px-4 py-2">
                <div className="text-sm text-gray-500">Último acesso</div>
                <div className="text-sm font-medium">
                  {new Date().toLocaleDateString('pt-BR')}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {statsCards.map((stat, index) => (
            <div
              key={index}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-2">{stat.value}</p>
                </div>
                <div className="text-3xl">{stat.icon}</div>
              </div>
              <div className="mt-4">
                <span className={`text-sm ${
                  stat.changeType === 'positive' ? 'text-green-600' :
                  stat.changeType === 'warning' ? 'text-yellow-600' :
                  'text-gray-600'
                }`}>
                  {stat.change}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Ações Rápidas</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {quickActions.map((action, index) => (
              <Link
                key={index}
                to={action.href}
                className={`${action.color} text-white rounded-xl p-6 text-center shadow-sm hover:shadow-md transition-all transform hover:scale-105`}
              >
                <div className="text-3xl mb-3">{action.icon}</div>
                <h3 className="font-semibold text-lg">{action.title}</h3>
                <p className="text-sm opacity-90 mt-1">{action.description}</p>
              </Link>
            ))}
          </div>
        </div>

        {/* Recent Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Recent Documents */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">
                📄 Documentos Recentes
              </h2>
              <Link
                to="/documents"
                className="text-blue-600 hover:text-blue-700 text-sm font-medium"
              >
                Ver todos
              </Link>
            </div>
            
            {recentDocuments.length > 0 ? (
              <div className="space-y-4">
                {recentDocuments.map((doc) => (
                  <div
                    key={doc.id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900 truncate">
                        {doc.titulo}
                      </h3>
                      <p className="text-sm text-gray-500 mt-1">
                        {new Date(doc.updated_at).toLocaleDateString('pt-BR')}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        doc.status === 'publicado' ? 'bg-green-100 text-green-800' :
                        doc.status === 'rascunho' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {doc.status}
                      </span>
                      <Link
                        to={`/documents/${doc.id}/edit`}
                        className="text-blue-600 hover:text-blue-700"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5l7 7-7 7" />
                        </svg>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="text-4xl mb-4">📝</div>
                <p className="text-gray-500">Nenhum documento encontrado</p>
                <Link
                  to="/documents/new"
                  className="mt-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  Criar primeiro documento
                </Link>
              </div>
            )}
          </div>

          {/* Recent Templates */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">
                🗂️ Templates Disponíveis
              </h2>
              <Link
                to="/templates"
                className="text-blue-600 hover:text-blue-700 text-sm font-medium"
              >
                Ver todos
              </Link>
            </div>
            
            {recentTemplates.length > 0 ? (
              <div className="space-y-4">
                {recentTemplates.map((template) => (
                  <div
                    key={template.id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900 truncate">
                        {template.titulo}
                      </h3>
                      <p className="text-sm text-gray-500 mt-1">
                        {template.categoria}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        template.publico ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
                      }`}>
                        {template.publico ? 'Público' : 'Privado'}
                      </span>
                      <Link
                        to={`/documents/new?template=${template.id}`}
                        className="text-blue-600 hover:text-blue-700"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                        </svg>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="text-4xl mb-4">🗂️</div>
                <p className="text-gray-500">Nenhum template encontrado</p>
                <Link
                  to="/templates/new"
                  className="mt-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
                >
                  Criar primeiro template
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Tips Section */}
        <div className="mt-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl p-6 text-white">
          <h2 className="text-xl font-semibold mb-4">💡 Dicas para Maximizar sua Produtividade</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white bg-opacity-20 rounded-lg p-4">
              <h3 className="font-medium mb-2">Use Templates</h3>
              <p className="text-sm opacity-90">
                Crie templates para documentos recorrentes e economize tempo
              </p>
            </div>
            <div className="bg-white bg-opacity-20 rounded-lg p-4">
              <h3 className="font-medium mb-2">IA Jurídica</h3>
              <p className="text-sm opacity-90">
                Use nossa IA para gerar textos jurídicos precisos e rápidos
              </p>
            </div>
            <div className="bg-white bg-opacity-20 rounded-lg p-4">
              <h3 className="font-medium mb-2">Auto-save</h3>
              <p className="text-sm opacity-90">
                Seus documentos são salvos automaticamente a cada mudança
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
