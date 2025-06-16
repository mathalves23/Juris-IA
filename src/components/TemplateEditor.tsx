import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { templateService, aiService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';

const TemplateEditor: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [template, setTemplate] = useState<any>({
    nome: '',
    conteudo: '',
    categoria_id: '',
    variaveis: {}
  });
  const [categories, setCategories] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(id ? true : false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [showAIPanel, setShowAIPanel] = useState(false);
  const [aiPrompt, setAIPrompt] = useState('');
  const [aiResponse, setAIResponse] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [extractedVariables, setExtractedVariables] = useState<any>({});
  const quillRef = useRef<ReactQuill>(null);

  // Módulos e formatos do editor Quill
  const modules = {
    toolbar: [
      [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
      ['bold', 'italic', 'underline', 'strike'],
      [{ 'list': 'ordered'}, { 'list': 'bullet' }],
      [{ 'indent': '-1'}, { 'indent': '+1' }],
      [{ 'align': [] }],
      ['link'],
      ['clean']
    ],
  };

  const formats = [
    'header',
    'bold', 'italic', 'underline', 'strike',
    'list', 'bullet', 'indent',
    'align',
    'link'
  ];

  // Carregar template existente ou categorias para novo template
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Carregar categorias em qualquer caso
        const { categories: cats } = await templateService.getCategories();
        setCategories(cats);
        
        if (id) {
          // Carregar template existente
          const { template: temp } = await templateService.getTemplate(Number(id));
          setTemplate(temp);
        }
      } catch (err) {
        console.error('Erro ao carregar dados:', err);
        setError('Erro ao carregar dados. Tente novamente.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [id]);

  // Salvar template
  const handleSave = async () => {
    if (!template.nome.trim()) {
      setError('O nome do modelo é obrigatório');
      return;
    }

    if (!template.categoria_id) {
      setError('Selecione uma categoria');
      return;
    }

    setIsSaving(true);
    setError('');

    try {
      let response;
      if (id) {
        // Atualizar template existente
        response = await templateService.updateTemplate(Number(id), template);
      } else {
        // Criar novo template
        response = await templateService.createTemplate(template);
        navigate(`/templates/${response.template.id}`);
      }

      setTemplate(response.template);
      alert('Modelo salvo com sucesso!');
    } catch (err) {
      console.error('Erro ao salvar modelo:', err);
      setError('Erro ao salvar modelo. Tente novamente.');
    } finally {
      setIsSaving(false);
    }
  };

  // Gerar texto com IA
  const handleGenerateText = async () => {
    if (!aiPrompt.trim()) {
      setError('Digite uma instrução para a IA');
      return;
    }

    setIsGenerating(true);
    setError('');

    try {
      const promptData = {
        prompt: aiPrompt,
        context: template.conteudo
      };

      const { generated_text } = await aiService.generateText(promptData);
      setAIResponse(generated_text);
    } catch (err) {
      console.error('Erro ao gerar texto:', err);
      setError('Erro ao gerar texto. Tente novamente.');
    } finally {
      setIsGenerating(false);
    }
  };

  // Inserir texto gerado pela IA no template
  const handleInsertAIText = () => {
    if (!aiResponse) return;
    
    const editor = quillRef.current?.getEditor();
    if (editor) {
      const range = editor.getSelection();
      const position = range ? range.index : editor.getText().length;
      editor.insertText(position, aiResponse);
      setTemplate({
        ...template,
        conteudo: editor.root.innerHTML
      });
    }
    
    setAIResponse('');
    setAIPrompt('');
    setShowAIPanel(false);
  };

  // Extrair variáveis do template
  const handleExtractVariables = async () => {
    if (!template.conteudo) {
      setError('O modelo precisa ter conteúdo para extrair variáveis');
      return;
    }

    try {
      const { variables } = await aiService.extractVariables(template.conteudo);
      setExtractedVariables(variables);
      
      // Atualizar variáveis do template
      setTemplate({
        ...template,
        variaveis: variables
      });
      
      alert('Variáveis extraídas com sucesso!');
    } catch (err) {
      console.error('Erro ao extrair variáveis:', err);
      setError('Erro ao extrair variáveis. Tente novamente.');
    }
  };

  // Renderização condicional baseada no estado
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <p>Carregando...</p>
      </div>
    );
  }

  return (
    <div className="px-4 py-6 sm:px-0">
        {error && (
          <div className="mb-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
            <span className="block sm:inline">{error}</span>
          </div>
        )}
        
        <div className="flex flex-col space-y-4">
          {/* Cabeçalho do editor */}
          <div className="bg-white shadow sm:rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                <div className="flex-1">
                  <input
                    type="text"
                    value={template.nome}
                    onChange={(e) => setTemplate({ ...template, nome: e.target.value })}
                    placeholder="Nome do modelo"
                    className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-lg border-gray-300 rounded-md"
                  />
                  
                  <div className="mt-4">
                    <label htmlFor="category" className="block text-sm font-medium text-gray-700">
                      Categoria
                    </label>
                    <select
                      id="category"
                      value={template.categoria_id}
                      onChange={(e) => setTemplate({ ...template, categoria_id: e.target.value })}
                      className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                    >
                      <option value="">Selecione uma categoria</option>
                      {categories.map((category) => (
                        <option key={category.id} value={category.id}>
                          {category.nome}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="mt-4 sm:mt-0 sm:ml-6 flex space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowAIPanel(!showAIPanel)}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    Assistente IA
                  </button>
                  <button
                    type="button"
                    onClick={handleExtractVariables}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    Extrair Variáveis
                  </button>
                  <button
                    type="button"
                    onClick={handleSave}
                    disabled={isSaving}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    {isSaving ? 'Salvando...' : 'Salvar Modelo'}
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          {/* Painel de IA */}
          {showAIPanel && (
            <div className="bg-white shadow sm:rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Assistente IA</h3>
                <div className="space-y-4">
                  <div>
                    <label htmlFor="ai-prompt" className="block text-sm font-medium text-gray-700">
                      O que você deseja que a IA faça?
                    </label>
                    <div className="mt-1">
                      <textarea
                        id="ai-prompt"
                        rows={3}
                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                        placeholder="Ex: Crie um modelo de petição inicial para ação de cobrança"
                        value={aiPrompt}
                        onChange={(e) => setAIPrompt(e.target.value)}
                      />
                    </div>
                    <p className="mt-2 text-sm text-gray-500">
                      Seja específico sobre o tipo de modelo que você precisa criar.
                    </p>
                  </div>
                  
                  <div className="flex justify-end">
                    <button
                      type="button"
                      onClick={handleGenerateText}
                      disabled={isGenerating || !aiPrompt.trim()}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      {isGenerating ? 'Gerando...' : 'Gerar texto'}
                    </button>
                  </div>
                  
                  {aiResponse && (
                    <div className="mt-4">
                      <label className="block text-sm font-medium text-gray-700">
                        Texto gerado
                      </label>
                      <div className="mt-1 p-4 border border-gray-300 rounded-md bg-gray-50">
                        <p className="text-sm text-gray-900 whitespace-pre-wrap">{aiResponse}</p>
                      </div>
                      <div className="mt-4 flex justify-end space-x-3">
                        <button
                          type="button"
                          onClick={() => setAIResponse('')}
                          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                        >
                          Descartar
                        </button>
                        <button
                          type="button"
                          onClick={handleInsertAIText}
                          className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                        >
                          Inserir no modelo
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
          
          {/* Editor de texto */}
          <div className="bg-white shadow sm:rounded-lg flex-grow">
            <div className="px-4 py-5 sm:p-6">
              <div className="min-h-[500px]">
                <ReactQuill
                  ref={quillRef}
                  theme="snow"
                  value={template.conteudo}
                  onChange={(content) => setTemplate({ ...template, conteudo: content })}
                  modules={modules}
                  formats={formats}
                  placeholder="Comece a escrever seu modelo..."
                  style={{ height: '450px' }}
                />
              </div>
            </div>
          </div>
          
          {/* Painel de variáveis */}
          {Object.keys(template.variaveis || {}).length > 0 && (
            <div className="bg-white shadow sm:rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Variáveis Detectadas</h3>
                <div className="bg-gray-50 p-4 rounded-md">
                  <p className="text-sm text-gray-500 mb-4">
                    Estas variáveis serão substituídas quando o usuário criar um documento baseado neste modelo.
                  </p>
                  <ul className="divide-y divide-gray-200">
                    {Object.entries(template.variaveis || {}).map(([key, value]: [string, any]) => (
                      <li key={key} className="py-3 flex justify-between">
                        <div className="text-sm font-medium text-indigo-600">{key}</div>
                        <div className="text-sm text-gray-500">{value}</div>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
  );
};

export default TemplateEditor;
