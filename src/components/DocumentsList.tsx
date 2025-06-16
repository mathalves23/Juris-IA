import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { documentService } from '../services/api';

const DocumentsList: React.FC = () => {
  const { user, subscription } = useAuth();
  const [documents, setDocuments] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('all'); // all, draft, finished

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const { documents } = await documentService.getDocuments();
        setDocuments(documents);
      } catch (err) {
        setError('Erro ao carregar documentos');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDocuments();
  }, []);

  const filteredDocuments = documents.filter(doc => {
    if (filter === 'all') return true;
    if (filter === 'draft') return doc.status === 'Rascunho';
    if (filter === 'finished') return doc.status === 'Finalizado';
    return true;
  });

  const handleDeleteDocument = async (id: number) => {
    if (window.confirm('Tem certeza que deseja excluir este documento?')) {
      try {
        await documentService.deleteDocument(id);
        setDocuments(documents.filter(doc => doc.id !== id));
      } catch (err) {
        console.error('Erro ao excluir documento:', err);
        alert('Erro ao excluir documento. Tente novamente.');
      }
    }
  };

  return (
    <div className="px-4 py-6 sm:px-0">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-semibold text-gray-900">Meus Documentos</h1>
          <Link
            to="/documents/new"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700"
          >
            Novo Documento
          </Link>
        </div>

        {/* Filtros */}
        <div className="mb-6">
          <div className="sm:flex sm:items-center">
            <div className="sm:flex-auto">
              <p className="mt-1 text-sm text-gray-500">
                {subscription?.plano === 'Editor IA' 
                  ? `Você utilizou ${subscription.documentos_utilizados} de ${subscription.limite_documentos} documentos neste mês.` 
                  : 'Você está utilizando o plano Plataforma Total sem limites de documentos.'}
              </p>
            </div>
            <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
              <div className="flex space-x-4">
                <button
                  type="button"
                  onClick={() => setFilter('all')}
                  className={`px-3 py-1 text-sm font-medium rounded-md ${
                    filter === 'all' 
                      ? 'bg-indigo-100 text-indigo-700' 
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  Todos
                </button>
                <button
                  type="button"
                  onClick={() => setFilter('draft')}
                  className={`px-3 py-1 text-sm font-medium rounded-md ${
                    filter === 'draft' 
                      ? 'bg-yellow-100 text-yellow-700' 
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  Rascunhos
                </button>
                <button
                  type="button"
                  onClick={() => setFilter('finished')}
                  className={`px-3 py-1 text-sm font-medium rounded-md ${
                    filter === 'finished' 
                      ? 'bg-green-100 text-green-700' 
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  Finalizados
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Lista de documentos */}
        {isLoading ? (
          <div className="text-center py-10">
            <p>Carregando documentos...</p>
          </div>
        ) : error ? (
          <div className="text-center py-10 text-red-500">
            <p>{error}</p>
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="text-center py-10 bg-white shadow overflow-hidden sm:rounded-md">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhum documento encontrado</h3>
            <p className="mt-1 text-sm text-gray-500">
              {filter !== 'all' 
                ? 'Tente mudar os filtros ou crie um novo documento.' 
                : 'Comece criando um novo documento.'}
            </p>
            <div className="mt-6">
              <Link
                to="/documents/new"
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
              >
                <svg
                  className="-ml-1 mr-2 h-5 w-5"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                    clipRule="evenodd"
                  />
                </svg>
                Novo Documento
              </Link>
            </div>
          </div>
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
              {filteredDocuments.map((doc) => (
                <li key={doc.id}>
                  <div className="px-4 py-4 flex items-center sm:px-6">
                    <div className="min-w-0 flex-1 sm:flex sm:items-center sm:justify-between">
                      <div>
                        <Link to={`/documents/${doc.id}`} className="text-sm font-medium text-indigo-600 truncate hover:underline">
                          {doc.titulo}
                        </Link>
                        <div className="mt-2 flex">
                          <div className="flex items-center text-sm text-gray-500">
                            <svg
                              className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400"
                              xmlns="http://www.w3.org/2000/svg"
                              viewBox="0 0 20 20"
                              fill="currentColor"
                            >
                              <path
                                fillRule="evenodd"
                                d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z"
                                clipRule="evenodd"
                              />
                            </svg>
                            <span>
                              Atualizado em {new Date(doc.data_atualizacao).toLocaleDateString('pt-BR')}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="mt-4 flex-shrink-0 sm:mt-0 sm:ml-5">
                        <div className="flex -space-x-1 overflow-hidden">
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              doc.status === 'Rascunho'
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-green-100 text-green-800'
                            }`}
                          >
                            {doc.status}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="ml-5 flex-shrink-0">
                      <div className="flex space-x-2">
                        <Link
                          to={`/documents/${doc.id}`}
                          className="inline-flex items-center p-1 border border-transparent rounded-full shadow-sm text-white bg-indigo-600 hover:bg-indigo-700"
                        >
                          <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                            <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                          </svg>
                        </Link>
                        <button
                          onClick={() => handleDeleteDocument(doc.id)}
                          className="inline-flex items-center p-1 border border-transparent rounded-full shadow-sm text-white bg-red-600 hover:bg-red-700"
                        >
                          <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                            <path
                              fillRule="evenodd"
                              d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                              clipRule="evenodd"
                            />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
  );
};

export default DocumentsList;
