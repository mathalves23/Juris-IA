import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { templateService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const TemplatesList: React.FC = () => {
  const { user } = useAuth();
  const [templates, setTemplates] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Carregar templates
        const { templates: temps } = await templateService.getTemplates();
        setTemplates(temps);
        
        // Carregar categorias
        const { categories: cats } = await templateService.getCategories();
        setCategories(cats);
      } catch (err) {
        console.error('Erro ao carregar dados:', err);
        setError('Erro ao carregar modelos. Tente novamente.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleDeleteTemplate = async (id: number) => {
    if (window.confirm('Tem certeza que deseja excluir este modelo?')) {
      try {
        await templateService.deleteTemplate(id);
        setTemplates(templates.filter(template => template.id !== id));
      } catch (err) {
        console.error('Erro ao excluir modelo:', err);
        alert('Erro ao excluir modelo. Tente novamente.');
      }
    }
  };

  const filteredTemplates = selectedCategory 
    ? templates.filter(template => template.categoria_id === selectedCategory)
    : templates;

  return (
    <div className="px-4 py-6 sm:px-0">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-semibold text-gray-900">Modelos de Documentos</h1>
          <Link
            to="/templates/new"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700"
          >
            Novo Modelo
          </Link>
        </div>

        {/* Filtros por categoria */}
        {categories.length > 0 && (
          <div className="mb-6">
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setSelectedCategory(null)}
                className={`px-3 py-1 text-sm font-medium rounded-md ${
                  selectedCategory === null 
                    ? 'bg-indigo-100 text-indigo-700' 
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                Todos
              </button>
              {categories.map(category => (
                <button
                  key={category.id}
                  type="button"
                  onClick={() => setSelectedCategory(category.id)}
                  className={`px-3 py-1 text-sm font-medium rounded-md ${
                    selectedCategory === category.id 
                      ? 'bg-indigo-100 text-indigo-700' 
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  {category.nome}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Lista de modelos */}
        {isLoading ? (
          <div className="text-center py-10">
            <p>Carregando modelos...</p>
          </div>
        ) : error ? (
          <div className="text-center py-10 text-red-500">
            <p>{error}</p>
          </div>
        ) : filteredTemplates.length === 0 ? (
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
            <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhum modelo encontrado</h3>
            <p className="mt-1 text-sm text-gray-500">
              {selectedCategory !== null 
                ? 'Tente selecionar outra categoria ou crie um novo modelo.' 
                : 'Comece criando um novo modelo.'}
            </p>
            <div className="mt-6">
              <Link
                to="/templates/new"
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
                Novo Modelo
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filteredTemplates.map((template) => (
              <div key={template.id} className="bg-white overflow-hidden shadow rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 bg-indigo-500 rounded-md p-3">
                      <svg className="h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        {template.categoria}
                      </dt>
                      <dd className="flex items-baseline">
                        <div className="text-lg font-semibold text-gray-900">
                          {template.nome}
                        </div>
                      </dd>
                    </div>
                  </div>
                  
                  {/* Ações do modelo */}
                  <div className="mt-4 flex justify-end space-x-3">
                    <Link
                      to={`/templates/${template.id}`}
                      className="inline-flex items-center px-3 py-1 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                    >
                      Editar
                    </Link>
                    <Link
                      to={`/documents/new?template=${template.id}`}
                      className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700"
                    >
                      Usar
                    </Link>
                    {template.usuario_id === user?.id && (
                      <button
                        onClick={() => handleDeleteTemplate(template.id)}
                        className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
                      >
                        Excluir
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
  );
};

export default TemplatesList;
