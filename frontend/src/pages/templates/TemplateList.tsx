import React from 'react';
import { Link } from 'react-router-dom';
import { templateService } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext.js';
import { useToast } from '../../contexts/ToastContext.js';
import Loading from '../../components/Loading';
import Modal from '../../components/Modal';

const TemplatesList = () => {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [templates, setTemplates] = React.useState<any[]>([]);
  const [filteredTemplates, setFilteredTemplates] = React.useState<any[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [searchTerm, setSearchTerm] = React.useState('');
  const [selectedCategory, setSelectedCategory] = React.useState('all');
  const [selectedFilter, setSelectedFilter] = React.useState('all'); // all, public, private, mine
  const [deleteModal, setDeleteModal] = React.useState<{ isOpen: boolean; template?: any }>({ isOpen: false });

  const categories = [
    { value: 'all', label: 'Todas as Categorias' },
    { value: 'Petições', label: 'Petições' },
    { value: 'Defesas', label: 'Defesas' },
    { value: 'Recursos', label: 'Recursos' },
    { value: 'Criminal', label: 'Criminal' },
    { value: 'Administrativo', label: 'Administrativo' },
    { value: 'Trabalhista', label: 'Trabalhista' },
    { value: 'Cível', label: 'Cível' },
  ];

  const filters = [
    { value: 'all', label: 'Todos', icon: '📄' },
    { value: 'public', label: 'Públicos', icon: '🌐' },
    { value: 'private', label: 'Privados', icon: '🔒' },
    { value: 'mine', label: 'Meus Templates', icon: '👤' },
  ];

  React.useEffect(() => {
    const fetchTemplates = async () => {
      try {
        setIsLoading(true);
        const templates = await templateService.getAll();
        setTemplates(templates);
      } catch (err) {
        console.error('Erro ao carregar templates:', err);
        showToast({ type: 'error', title: 'Erro ao carregar templates' });
      } finally {
        setIsLoading(false);
      }
    };

    fetchTemplates();
  }, [showToast]);

  React.useEffect(() => {
    let filtered = [...templates];

    // Filtro por categoria
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(template => template.categoria === selectedCategory);
    }

    // Filtro por tipo
    if (selectedFilter === 'public') {
      filtered = filtered.filter(template => template.publico);
    } else if (selectedFilter === 'private') {
      filtered = filtered.filter(template => !template.publico);
    } else if (selectedFilter === 'mine') {
      filtered = filtered.filter(template => template.user_id === user?.id);
    }

    // Filtro por busca
    if (searchTerm) {
      filtered = filtered.filter(template =>
        template.titulo.toLowerCase().includes(searchTerm.toLowerCase()) ||
        template.categoria.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (template.tags && template.tags.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    setFilteredTemplates(filtered);
  }, [templates, selectedCategory, selectedFilter, searchTerm, user?.id]);

  const handleDeleteTemplate = async (template: any) => {
    try {
      await templateService.delete(template.id);
      setTemplates(templates.filter(t => t.id !== template.id));
      setDeleteModal({ isOpen: false });
              showToast({ type: 'success', title: 'Template excluído com sucesso' });
    } catch (err) {
      console.error('Erro ao excluir template:', err);
              showToast({ type: 'error', title: 'Erro ao excluir template' });
    }
  };

  const openDeleteModal = (template: any) => {
    setDeleteModal({ isOpen: true, template });
  };

  if (isLoading) {
    return <Loading />;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Templates Jurídicos</h1>
            <p className="mt-2 text-gray-600">
              Gerencie e utilize modelos de documentos jurídicos
            </p>
          </div>
          <div className="mt-4 sm:mt-0">
            <Link
              to="/templates/new"
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Novo Template
            </Link>
          </div>
        </div>
      </div>

      {/* Filtros e Busca */}
      <div className="mb-8 space-y-4">
        {/* Barra de busca */}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
            </svg>
          </div>
          <input
            type="text"
            placeholder="Buscar templates por título, categoria ou tags..."
            className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {/* Filtros */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          {/* Filtros por tipo */}
          <div className="flex flex-wrap gap-2">
            {filters.map((filter) => (
              <button
                key={filter.value}
                onClick={() => setSelectedFilter(filter.value)}
                className={`inline-flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  selectedFilter === filter.value
                    ? 'bg-blue-100 text-blue-700 border border-blue-200'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                <span className="mr-2">{filter.icon}</span>
                {filter.label}
              </button>
            ))}
          </div>

          {/* Filtro por categoria */}
          <div className="flex items-center space-x-2">
            <label htmlFor="category" className="text-sm font-medium text-gray-700">
              Categoria:
            </label>
            <select
              id="category"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="block pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
            >
              {categories.map((category) => (
                <option key={category.value} value={category.value}>
                  {category.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Estatísticas */}
      <div className="mb-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="text-2xl">📄</div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Total</p>
              <p className="text-lg font-semibold text-gray-900">{templates.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="text-2xl">🌐</div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Públicos</p>
              <p className="text-lg font-semibold text-gray-900">
                {templates.filter(t => t.publico).length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="text-2xl">👤</div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Meus</p>
              <p className="text-lg font-semibold text-gray-900">
                {templates.filter(t => t.user_id === user?.id).length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="text-2xl">📊</div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Resultado</p>
              <p className="text-lg font-semibold text-gray-900">{filteredTemplates.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Lista de Templates */}
      {filteredTemplates.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border">
          <div className="text-6xl mb-4">🗂️</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {searchTerm || selectedCategory !== 'all' || selectedFilter !== 'all'
              ? 'Nenhum template encontrado'
              : 'Nenhum template disponível'
            }
          </h3>
          <p className="text-gray-500 mb-6">
            {searchTerm || selectedCategory !== 'all' || selectedFilter !== 'all'
              ? 'Tente ajustar os filtros ou criar um novo template.'
              : 'Comece criando seu primeiro template jurídico.'}
          </p>
          <Link
            to="/templates/new"
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Criar Template
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTemplates.map((template) => (
            <div
              key={template.id}
              className="bg-white rounded-lg border hover:border-blue-300 hover:shadow-md transition-all duration-200"
            >
              <div className="p-6">
                {/* Header do card */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">
                      {template.titulo}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {template.categoria}
                    </p>
                  </div>
                  <div className="flex space-x-1">
                    {template.publico ? (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        🌐 Público
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        🔒 Privado
                      </span>
                    )}
                  </div>
                </div>

                {/* Tags */}
                {template.tags && (
                  <div className="mb-4">
                    <div className="flex flex-wrap gap-1">
                      {template.tags.split(',').slice(0, 3).map((tag: string, index: number) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-50 text-blue-700"
                        >
                          {tag.trim()}
                        </span>
                      ))}
                      {template.tags.split(',').length > 3 && (
                        <span className="text-xs text-gray-500">
                          +{template.tags.split(',').length - 3} mais
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Ações */}
                <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                  <div className="flex space-x-2">
                    <Link
                      to={`/documents/new?template=${template.id}`}
                      className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-blue-600 hover:bg-blue-700"
                    >
                      🚀 Usar
                    </Link>
                    <Link
                      to={`/templates/${template.id}/edit`}
                      className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                    >
                      ✏️ Editar
                    </Link>
                  </div>
                  
                  {template.user_id === user?.id && (
                    <button
                      onClick={() => openDeleteModal(template)}
                      className="inline-flex items-center px-2 py-1.5 text-xs font-medium rounded text-red-600 hover:bg-red-50"
                    >
                      🗑️
                    </button>
                  )}
                </div>

                {/* Info adicional */}
                <div className="mt-3 text-xs text-gray-500">
                  Criado em {new Date(template.created_at).toLocaleDateString('pt-BR')}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal de confirmação de exclusão */}
      <Modal
        isOpen={deleteModal.isOpen}
        onClose={() => setDeleteModal({ isOpen: false })}
        title="Confirmar Exclusão"
        size="sm"
      >
        <div className="text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <p className="text-gray-600 mb-6">
            Tem certeza que deseja excluir o template <strong>{deleteModal.template?.titulo}</strong>?
            Esta ação não pode ser desfeita.
          </p>
          <div className="flex justify-center space-x-3">
            <button
              onClick={() => setDeleteModal({ isOpen: false })}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              onClick={() => handleDeleteTemplate(deleteModal.template)}
              className="px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-red-600 hover:bg-red-700"
            >
              Excluir
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default TemplatesList;
