import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext.js';
import { useToast } from '../../contexts/ToastContext.js';
import { documentService } from '../../services/api';
import Loading from '../../components/Loading';
import Modal from '../../components/Modal';

const DocumentsList = () => {
  const { subscription } = useAuth();
  const { showToast } = useToast();
  const [documents, setDocuments] = React.useState<any[]>([]);
  const [filteredDocuments, setFilteredDocuments] = React.useState<any[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [searchTerm, setSearchTerm] = React.useState('');
  const [statusFilter, setStatusFilter] = React.useState('all');
  const [sortBy, setSortBy] = React.useState('updated'); // updated, created, title
  const [sortOrder, setSortOrder] = React.useState('desc'); // asc, desc
  const [viewMode, setViewMode] = React.useState('grid'); // grid, list
  const [deleteModal, setDeleteModal] = React.useState<{ isOpen: boolean; document?: any }>({ isOpen: false });

  const statusOptions = React.useMemo(() => [
    { value: 'all', label: 'Todos os Status', icon: '📄', count: 0 },
    { value: 'rascunho', label: 'Rascunhos', icon: '✏️', count: 0 },
    { value: 'revisao', label: 'Em Revisão', icon: '👀', count: 0 },
    { value: 'publicado', label: 'Publicados', icon: '✅', count: 0 },
  ], []);

  const sortOptions = [
    { value: 'updated', label: 'Última atualização' },
    { value: 'created', label: 'Data de criação' },
    { value: 'title', label: 'Título (A-Z)' },
  ];

  React.useEffect(() => {
    const fetchDocuments = async () => {
      try {
        setIsLoading(true);
        const documents = await documentService.getAll();
        setDocuments(documents);
      } catch (err) {
        console.error('Erro ao carregar documentos:', err);
        showToast({ type: 'error', title: 'Erro ao carregar documentos' });
      } finally {
        setIsLoading(false);
      }
    };

    fetchDocuments();
  }, [showToast]);

  React.useEffect(() => {
    let filtered = [...documents];

    // Filtro por status
    if (statusFilter !== 'all') {
      filtered = filtered.filter(doc => doc.status === statusFilter);
    }

    // Filtro por busca
    if (searchTerm) {
      filtered = filtered.filter(doc =>
        doc.titulo.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (doc.tags && doc.tags.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // Ordenação
    filtered.sort((a, b) => {
      let valueA, valueB;
      
      switch (sortBy) {
        case 'created':
          valueA = new Date(a.created_at);
          valueB = new Date(b.created_at);
          break;
        case 'title':
          valueA = a.titulo.toLowerCase();
          valueB = b.titulo.toLowerCase();
          break;
        default: // updated
          valueA = new Date(a.updated_at);
          valueB = new Date(b.updated_at);
      }

      if (sortOrder === 'asc') {
        return valueA > valueB ? 1 : -1;
      } else {
        return valueA < valueB ? 1 : -1;
      }
    });

    setFilteredDocuments(filtered);

    // Atualizar contadores de status
    statusOptions.forEach(option => {
      if (option.value === 'all') {
        option.count = documents.length;
      } else {
        option.count = documents.filter(doc => doc.status === option.value).length;
      }
    });

  }, [documents, statusFilter, searchTerm, sortBy, sortOrder, statusOptions]);

  const handleDeleteDocument = async (document: any) => {
    try {
      await documentService.delete(document.id);
      setDocuments(documents.filter(doc => doc.id !== document.id));
      setDeleteModal({ isOpen: false });
              showToast({ type: 'success', title: 'Documento excluído com sucesso' });
    } catch (err) {
      console.error('Erro ao excluir documento:', err);
              showToast({ type: 'error', title: 'Erro ao excluir documento' });
    }
  };

  const openDeleteModal = (document: any) => {
    setDeleteModal({ isOpen: true, document });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'rascunho':
        return 'bg-yellow-100 text-yellow-800';
      case 'revisao':
        return 'bg-blue-100 text-blue-800';
      case 'publicado':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'rascunho':
        return '✏️';
      case 'revisao':
        return '👀';
      case 'publicado':
        return '✅';
      default:
        return '📄';
    }
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
            <h1 className="text-3xl font-bold text-gray-900">Meus Documentos</h1>
            <p className="mt-2 text-gray-600">
              Gerencie todos os seus documentos jurídicos
            </p>
            {subscription && subscription.limite_documentos && (
              <div className="mt-2">
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-500">
                    {subscription.documentos_utilizados || 0} / {subscription.limite_documentos} documentos utilizados
                  </span>
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{
                        width: `${Math.min(((subscription.documentos_utilizados || 0) / subscription.limite_documentos) * 100, 100)}%`
                      }}
                    ></div>
                  </div>
                </div>
              </div>
            )}
          </div>
          <div className="mt-4 sm:mt-0">
            <Link
              to="/documents/new"
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Novo Documento
            </Link>
          </div>
        </div>
      </div>

      {/* Barra de busca e filtros */}
      <div className="mb-8 space-y-4">
        {/* Busca */}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
            </svg>
          </div>
          <input
            type="text"
            placeholder="Buscar documentos por título ou tags..."
            className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {/* Filtros e controles */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          
          {/* Filtros de status */}
          <div className="flex flex-wrap gap-2">
            {statusOptions.map((status) => (
              <button
                key={status.value}
                onClick={() => setStatusFilter(status.value)}
                className={`inline-flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  statusFilter === status.value
                    ? 'bg-blue-100 text-blue-700 border border-blue-200'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                <span className="mr-2">{status.icon}</span>
                {status.label}
                <span className="ml-2 bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full text-xs">
                  {status.count}
                </span>
              </button>
            ))}
          </div>

          {/* Controles de ordenação e visualização */}
          <div className="flex items-center space-x-4">
            {/* Ordenação */}
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Ordenar por:</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="block pl-3 pr-8 py-2 text-sm border-gray-300 focus:ring-blue-500 focus:border-blue-500 rounded-md"
              >
                {sortOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <button
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                className="p-2 text-gray-400 hover:text-gray-600"
              >
                {sortOrder === 'asc' ? '↑' : '↓'}
              </button>
            </div>

            {/* Modo de visualização */}
            <div className="flex border border-gray-300 rounded-md">
              <button
                onClick={() => setViewMode('grid')}
                className={`px-3 py-2 text-sm font-medium rounded-l-md ${
                  viewMode === 'grid'
                    ? 'bg-blue-50 text-blue-700 border-blue-300'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                🔳
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`px-3 py-2 text-sm font-medium rounded-r-md border-l ${
                  viewMode === 'list'
                    ? 'bg-blue-50 text-blue-700 border-blue-300'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                ☰
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Estatísticas rápidas */}
      <div className="mb-8 grid grid-cols-1 sm:grid-cols-4 gap-4">
        {statusOptions.slice(1).map((status) => (
          <div key={status.value} className="bg-white rounded-lg border p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="text-2xl">{status.icon}</div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">{status.label}</p>
                <p className="text-lg font-semibold text-gray-900">{status.count}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Lista/Grid de documentos */}
      {filteredDocuments.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border">
          <div className="text-6xl mb-4">📄</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {searchTerm || statusFilter !== 'all'
              ? 'Nenhum documento encontrado'
              : 'Nenhum documento criado ainda'
            }
          </h3>
          <p className="text-gray-500 mb-6">
            {searchTerm || statusFilter !== 'all'
              ? 'Tente ajustar os filtros ou criar um novo documento.'
              : 'Comece criando seu primeiro documento jurídico.'}
          </p>
          <Link
            to="/documents/new"
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Criar Documento
          </Link>
        </div>
      ) : (
        <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' : 'space-y-4'}>
          {filteredDocuments.map((document) => (
            viewMode === 'grid' ? (
              // Grid view
              <div
                key={document.id}
                className="bg-white rounded-lg border hover:border-blue-300 hover:shadow-md transition-all duration-200"
              >
                <div className="p-6">
                  {/* Header do card */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-1">
                        <Link 
                          to={`/documents/${document.id}/edit`}
                          className="hover:text-blue-600 transition-colors"
                        >
                          {document.titulo}
                        </Link>
                      </h3>
                      <p className="text-sm text-gray-500">
                        Versão {document.versao || 1}
                      </p>
                    </div>
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(document.status)}`}>
                      {getStatusIcon(document.status)} {document.status}
                    </span>
                  </div>

                  {/* Conteúdo preview */}
                  {document.conteudo && (
                    <div className="mb-4">
                      <p className="text-sm text-gray-600 line-clamp-3">
                        {document.conteudo.replace(/<[^>]*>/g, '').substring(0, 150)}...
                      </p>
                    </div>
                  )}

                  {/* Tags */}
                  {document.tags && (
                    <div className="mb-4">
                      <div className="flex flex-wrap gap-1">
                        {document.tags.split(',').slice(0, 3).map((tag: string, index: number) => (
                          <span
                            key={index}
                            className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-50 text-blue-700"
                          >
                            {tag.trim()}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Ações */}
                  <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                    <div className="flex space-x-2">
                      <Link
                        to={`/documents/${document.id}/edit`}
                        className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-blue-600 hover:bg-blue-700"
                      >
                        ✏️ Editar
                      </Link>
                      <button className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50">
                        📄 Exportar
                      </button>
                    </div>
                    
                    <button
                      onClick={() => openDeleteModal(document)}
                      className="inline-flex items-center px-2 py-1.5 text-xs font-medium rounded text-red-600 hover:bg-red-50"
                    >
                      🗑️
                    </button>
                  </div>

                  {/* Info adicional */}
                  <div className="mt-3 text-xs text-gray-500">
                    Atualizado em {new Date(document.updated_at).toLocaleDateString('pt-BR')}
                  </div>
                </div>
              </div>
            ) : (
              // List view
              <div
                key={document.id}
                className="bg-white rounded-lg border hover:border-blue-300 transition-colors"
              >
                <div className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <h3 className="text-lg font-medium text-gray-900">
                          <Link 
                            to={`/documents/${document.id}/edit`}
                            className="hover:text-blue-600 transition-colors"
                          >
                            {document.titulo}
                          </Link>
                        </h3>
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(document.status)}`}>
                          {getStatusIcon(document.status)} {document.status}
                        </span>
                      </div>
                      <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                        <span>Versão {document.versao || 1}</span>
                        <span>•</span>
                        <span>Atualizado em {new Date(document.updated_at).toLocaleDateString('pt-BR')}</span>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Link
                        to={`/documents/${document.id}/edit`}
                        className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-blue-600 hover:bg-blue-700"
                      >
                        ✏️ Editar
                      </Link>
                      <button className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50">
                        📄 Exportar
                      </button>
                      <button
                        onClick={() => openDeleteModal(document)}
                        className="inline-flex items-center px-2 py-1.5 text-xs font-medium rounded text-red-600 hover:bg-red-50"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )
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
            Tem certeza que deseja excluir o documento <strong>{deleteModal.document?.titulo}</strong>?
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
              onClick={() => handleDeleteDocument(deleteModal.document)}
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

export default DocumentsList;
