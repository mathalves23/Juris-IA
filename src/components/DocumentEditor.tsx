import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { documentService, aiService, templateService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';

const DocumentEditor: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { subscription } = useAuth();
  const [document, setDocument] = useState<any>({
    titulo: '',
    conteudo: '',
    status: 'Rascunho',
    variaveis_preenchidas: {}
  });
  const [isLoading, setIsLoading] = useState(id ? true : false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [templates, setTemplates] = useState<any[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<any>(null);
  const [showAIPanel, setShowAIPanel] = useState(false);
  const [aiPrompt, setAIPrompt] = useState('');
  const [aiResponse, setAIResponse] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [versions, setVersions] = useState<any[]>([]);
  const [showVersions, setShowVersions] = useState(false);
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

  // Carregar documento existente ou templates disponíveis
  useEffect(() => {
    const fetchData = async () => {
      try {
        if (id) {
          // Carregar documento existente
          const { document: doc } = await documentService.getDocument(Number(id));
          setDocument(doc);
          
          // Carregar versões do documento
          const { versions: vers } = await documentService.getDocumentVersions(Number(id));
          setVersions(vers);
        } else {
          // Carregar templates disponíveis para novo documento
          const { templates: temps } = await templateService.getTemplates();
          setTemplates(temps);
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

  // Selecionar template
  const handleTemplateSelect = async (templateId: number) => {
    try {
      const { template } = await templateService.getTemplate(templateId);
      setSelectedTemplate(template);
      setDocument({
        ...document,
        titulo: `Baseado em: ${template.nome}`,
        conteudo: template.conteudo,
        template_id: template.id
      });
    } catch (err) {
      console.error('Erro ao carregar template:', err);
      setError('Erro ao carregar template. Tente novamente.');
    }
  };

  // Salvar documento
  const handleSave = async (status = document.status) => {
    if (!document.titulo.trim()) {
      setError('O título do documento é obrigatório');
      return;
    }

    setIsSaving(true);
    setError('');

    try {
      const documentData = {
        ...document,
        status
      };

      let response;
      if (id) {
        // Atualizar documento existente
        response = await documentService.updateDocument(Number(id), documentData);
        
        // Atualizar lista de versões
        const { versions: vers } = await documentService.getDocumentVersions(Number(id));
        setVersions(vers);
      } else {
        // Verificar limite de documentos para plano Editor IA
        if (subscription?.plano === 'Editor IA' && 
            (subscription?.documentos_utilizados || 0) >= (subscription?.limite_documentos || 0)) {
          setError('Você atingiu o limite de documentos do seu plano. Faça upgrade para continuar.');
          setIsSaving(false);
          return;
        }
        
        // Criar novo documento
        response = await documentService.createDocument(documentData);
        navigate(`/documents/${response.document.id}`);
      }

      setDocument(response.document);
      alert(status === 'Finalizado' ? 'Documento finalizado com sucesso!' : 'Documento salvo com sucesso!');
    } catch (err) {
      console.error('Erro ao salvar documento:', err);
      setError('Erro ao salvar documento. Tente novamente.');
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
        context: document.conteudo,
        document_id: id ? Number(id) : undefined
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

  // Inserir texto gerado pela IA no documento
  const handleInsertAIText = () => {
    if (!aiResponse) return;
    
    const editor = quillRef.current?.getEditor();
    if (editor) {
      const range = editor.getSelection();
      const position = range ? range.index : editor.getText().length;
      editor.insertText(position, aiResponse);
      setDocument({
        ...document,
        conteudo: editor.root.innerHTML
      });
    }
    
    setAIResponse('');
    setAIPrompt('');
    setShowAIPanel(false);
  };

  // Restaurar versão anterior
  const handleRestoreVersion = async (versionId: number) => {
    if (window.confirm('Tem certeza que deseja restaurar esta versão? As alterações não salvas serão perdidas.')) {
      try {
        const { document: restoredDoc } = await documentService.restoreDocumentVersion(Number(id), versionId);
        setDocument(restoredDoc);
        
        // Atualizar lista de versões
        const { versions: vers } = await documentService.getDocumentVersions(Number(id));
        setVersions(vers);
        
        setShowVersions(false);
        alert('Versão restaurada com sucesso!');
      } catch (err) {
        console.error('Erro ao restaurar versão:', err);
        setError('Erro ao restaurar versão. Tente novamente.');
      }
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

  // Tela de seleção de template para novo documento
  if (!id && !selectedTemplate) {
    return (
      <div className="px-4 py-6 sm:px-0">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-semibold text-gray-900">Novo Documento</h1>
          </div>
          
          {error && (
            <div className="mb-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
              <span className="block sm:inline">{error}</span>
            </div>
          )}
          
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <div className="px-4 py-5 sm:p-6">
              <h2 className="text-lg leading-6 font-medium text-gray-900 mb-4">Escolha uma opção para começar</h2>
              
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div 
                  className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500 cursor-pointer"
                  onClick={() => {
                    setSelectedTemplate({});
                    setDocument({
                      ...document,
                      titulo: 'Novo documento',
                      conteudo: ''
                    });
                  }}
                >
                  <div className="flex-shrink-0">
                    <svg className="h-10 w-10 text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <a href="#" className="focus:outline-none">
                      <span className="absolute inset-0" aria-hidden="true"></span>
                      <p className="text-sm font-medium text-gray-900">Documento em branco</p>
                      <p className="text-sm text-gray-500">Comece do zero com um documento vazio</p>
                    </a>
                  </div>
                </div>
                
                <div 
                  className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500 cursor-pointer"
                  onClick={() => setShowAIPanel(true)}
                >
                  <div className="flex-shrink-0">
                    <svg className="h-10 w-10 text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <a href="#" className="focus:outline-none">
                      <span className="absolute inset-0" aria-hidden="true"></span>
                      <p className="text-sm font-medium text-gray-900">Gerar com IA</p>
                      <p className="text-sm text-gray-500">Crie um documento com assistência de IA</p>
                    </a>
                  </div>
                </div>
              </div>
              
              {templates.length > 0 && (
                <>
                  <h3 className="text-lg leading-6 font-medium text-gray-900 mt-8 mb-4">Ou use um modelo</h3>
                  <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {templates.map((template) => (
                      <li key={template.id}>
                        <div 
                          className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500 cursor-pointer"
                          onClick={() => handleTemplateSelect(template.id)}
                        >
                          <div className="flex-shrink-0">
                            <svg className="h-10 w-10 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                          </div>
                          <div className="flex-1 min-w-0">
                            <a href="#" className="focus:outline-none">
                              <span className="absolute inset-0" aria-hidden="true"></span>
                              <p className="text-sm font-medium text-gray-900">{template.nome}</p>
                              <p className="text-sm text-gray-500">{template.categoria}</p>
                            </a>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          </div>
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
                    value={document.titulo}
                    onChange={(e) => setDocument({ ...document, titulo: e.target.value })}
                    placeholder="Título do documento"
                    className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-lg border-gray-300 rounded-md"
                  />
                </div>
                <div className="mt-4 sm:mt-0 sm:ml-6 flex space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowVersions(!showVersions)}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    disabled={!id}
                  >
                    Versões ({versions.length})
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowAIPanel(!showAIPanel)}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    Assistente IA
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSave('Rascunho')}
                    disabled={isSaving}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    {isSaving ? 'Salvando...' : 'Salvar'}
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSave('Finalizado')}
                    disabled={isSaving}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    {isSaving ? 'Finalizando...' : 'Finalizar'}
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          {/* Painel de versões */}
          {showVersions && (
            <div className="bg-white shadow sm:rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Histórico de versões</h3>
                {versions.length === 0 ? (
                  <p className="text-sm text-gray-500">Nenhuma versão anterior disponível.</p>
                ) : (
                  <ul className="divide-y divide-gray-200">
                    {versions.map((version) => (
                      <li key={version.id} className="py-4 flex justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-900">Versão {version.numero_versao}</p>
                          <p className="text-sm text-gray-500">
                            {new Date(version.data_criacao).toLocaleString('pt-BR')}
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleRestoreVersion(version.id)}
                          className="inline-flex items-center px-3 py-1 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                        >
                          Restaurar
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}
          
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
                        placeholder="Ex: Escreva uma introdução sobre responsabilidade civil"
                        value={aiPrompt}
                        onChange={(e) => setAIPrompt(e.target.value)}
                      />
                    </div>
                    <p className="mt-2 text-sm text-gray-500">
                      Seja específico sobre o que você precisa. A IA usará o contexto do seu documento atual.
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
                          Inserir no documento
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
                  value={document.conteudo}
                  onChange={(content) => setDocument({ ...document, conteudo: content })}
                  modules={modules}
                  formats={formats}
                  placeholder="Comece a escrever seu documento..."
                  style={{ height: '450px' }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
  );
};

export default DocumentEditor;
