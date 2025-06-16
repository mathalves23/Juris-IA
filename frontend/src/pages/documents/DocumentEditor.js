import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import { documentService, templateService, aiService } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext.js';

const DocumentEditor = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { subscription } = useAuth();
  
  const [document, setDocument] = React.useState({
    titulo: '',
    conteudo: '',
    template_id: null,
    status: 'Rascunho',
    variaveis_preenchidas: {}
  });
  
  const [templates, setTemplates] = React.useState([]);
  const [selectedTemplate, setSelectedTemplate] = React.useState(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [isSaving, setIsSaving] = React.useState(false);
  const [error, setError] = React.useState('');
  const [showAIPanel, setShowAIPanel] = React.useState(false);
  const [aiPrompt, setAIPrompt] = React.useState('');
  const [aiResponse, setAIResponse] = React.useState('');
  const [isGenerating, setIsGenerating] = React.useState(false);
  const [versions, setVersions] = React.useState([]);
  const [showVersions, setShowVersions] = React.useState(false);
  const [showVariableForm, setShowVariableForm] = React.useState(false);
  
  const quillRef = React.useRef(null);

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
  React.useEffect(() => {
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
  const handleTemplateSelect = async (templateId) => {
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

  // Handler para variáveis
  const handleVariableContentChange = (newContent, variables) => {
    setDocument({
      ...document,
      conteudo: newContent,
      variaveis_preenchidas: variables
    });
  };

  // Restaurar versão anterior
  const handleRestoreVersion = async (versionId) => {
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
    return React.createElement('div', {
      className: "flex justify-center items-center h-64"
    }, React.createElement('p', null, 'Carregando...'));
  }

  return React.createElement('div', {
    className: "px-4 py-6 sm:px-0"
  }, [
    // Error message
    error && React.createElement('div', {
      key: 'error',
      className: "mb-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative",
      role: "alert"
    }, React.createElement('span', {
      className: "block sm:inline"
    }, error)),

    // Template selection for new document
    !id && React.createElement('div', {
      key: 'template-selection',
      className: "mb-6 bg-white shadow sm:rounded-lg"
    }, React.createElement('div', {
      className: "px-4 py-5 sm:p-6"
    }, [
      React.createElement('h3', {
        key: 'template-title',
        className: "text-lg leading-6 font-medium text-gray-900 mb-4"
      }, 'Selecionar Modelo (Opcional)'),
      React.createElement('div', {
        key: 'template-grid',
        className: "grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
      }, templates.map((template) => 
        React.createElement('div', {
          key: template.id,
          onClick: () => handleTemplateSelect(template.id),
          className: "relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500 cursor-pointer"
        }, [
          React.createElement('div', {
            key: 'template-info',
            className: "flex-1 min-w-0"
          }, [
            React.createElement('span', {
              key: 'template-name',
              className: "absolute inset-0",
              'aria-hidden': "true"
            }),
            React.createElement('p', {
              key: 'template-title',
              className: "text-sm font-medium text-gray-900"
            }, template.nome),
            React.createElement('p', {
              key: 'template-category',
              className: "text-sm text-gray-500 truncate"
            }, template.categoria)
          ])
        ])
      ))
    ])),
    
    // Main editor container
    React.createElement('div', {
      key: 'editor',
      className: "flex flex-col space-y-4"
    }, [
      // Header section
      React.createElement('div', {
        key: 'header',
        className: "bg-white shadow sm:rounded-lg"
      }, React.createElement('div', {
        className: "px-4 py-5 sm:p-6"
      }, [
        // Title input
        React.createElement('div', {
          key: 'title-section',
          className: "flex flex-col sm:flex-row sm:items-center sm:justify-between"
        }, [
          React.createElement('div', {
            key: 'title-input',
            className: "flex-1"
          }, React.createElement('input', {
            type: "text",
            value: document.titulo,
            onChange: (e) => setDocument({ ...document, titulo: e.target.value }),
            placeholder: "Título do documento",
            className: "shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-lg border-gray-300 rounded-md"
          })),
          
          // Action buttons
          React.createElement('div', {
            key: 'action-buttons',
            className: "mt-4 sm:mt-0 sm:ml-4 flex space-x-2"
          }, [
            React.createElement('button', {
              key: 'ai-button',
              onClick: () => setShowAIPanel(!showAIPanel),
              className: "inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            }, '🤖 IA Assistente'),
            
            id && React.createElement('button', {
              key: 'versions-button',
              onClick: () => setShowVersions(!showVersions),
              className: "inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            }, '📋 Versões'),
            
            React.createElement('button', {
              key: 'save-draft-button',
              onClick: () => handleSave('Rascunho'),
              disabled: isSaving,
              className: `inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 ${isSaving ? 'opacity-50 cursor-not-allowed' : ''}`
            }, isSaving ? 'Salvando...' : 'Salvar Rascunho'),
            
            React.createElement('button', {
              key: 'finalize-button',
              onClick: () => handleSave('Finalizado'),
              disabled: isSaving,
              className: `inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white ${isSaving ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500`
            }, isSaving ? 'Finalizando...' : 'Finalizar')
          ])
        ])
      ])),
      
      // AI Panel
      showAIPanel && React.createElement('div', {
        key: 'ai-panel',
        className: "bg-blue-50 border border-blue-200 rounded-lg p-4"
      }, [
        React.createElement('h3', {
          key: 'ai-title',
          className: "text-lg font-medium text-blue-900 mb-4"
        }, 'Assistente de IA'),
        
        React.createElement('textarea', {
          key: 'ai-prompt',
          value: aiPrompt,
          onChange: (e) => setAIPrompt(e.target.value),
          placeholder: "Digite uma instrução para a IA gerar texto...",
          className: "w-full p-3 border border-gray-300 rounded-md resize-none",
          rows: 3
        }),
        
        React.createElement('div', {
          key: 'ai-buttons',
          className: "flex space-x-2 mt-3"
        }, [
          React.createElement('button', {
            key: 'generate-button',
            onClick: handleGenerateText,
            disabled: isGenerating,
            className: `px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 ${isGenerating ? 'cursor-not-allowed' : ''}`
          }, isGenerating ? 'Gerando...' : 'Gerar'),
          
          React.createElement('button', {
            key: 'close-button',
            onClick: () => setShowAIPanel(false),
            className: "px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
          }, 'Fechar')
        ]),
        
        // AI Response
        aiResponse && React.createElement('div', {
          key: 'ai-response',
          className: "mt-4 p-3 bg-white border border-gray-200 rounded-md"
        }, [
          React.createElement('h4', {
            key: 'response-title',
            className: "font-medium text-gray-900 mb-2"
          }, 'Texto Gerado:'),
          React.createElement('p', {
            key: 'response-text',
            className: "text-gray-700 mb-3"
          }, aiResponse),
          React.createElement('button', {
            key: 'insert-button',
            onClick: handleInsertAIText,
            className: "px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
          }, 'Inserir no Documento')
        ])
      ]),
      
      // Versions panel
      showVersions && React.createElement('div', {
        key: 'versions-panel',
        className: "bg-gray-50 border border-gray-200 rounded-lg p-4"
      }, [
        React.createElement('h3', {
          key: 'versions-title',
          className: "text-lg font-medium text-gray-900 mb-4"
        }, 'Versões do Documento'),
        
        React.createElement('div', {
          key: 'versions-list',
          className: "space-y-2"
        }, versions.map((version, index) => 
          React.createElement('div', {
            key: version.id,
            className: "flex items-center justify-between p-3 bg-white border border-gray-200 rounded-md"
          }, [
            React.createElement('div', {
              key: 'version-info'
            }, [
              React.createElement('p', {
                key: 'version-date',
                className: "text-sm font-medium text-gray-900"
              }, `Versão ${index + 1} - ${new Date(version.created_at).toLocaleString()}`),
              React.createElement('p', {
                key: 'version-status',
                className: "text-sm text-gray-500"
              }, version.status)
            ]),
            React.createElement('button', {
              key: 'restore-button',
              onClick: () => handleRestoreVersion(version.id),
              className: "px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
            }, 'Restaurar')
          ])
        ))
      ]),
      
      // Main editor
      React.createElement('div', {
        key: 'main-editor',
        className: "bg-white shadow sm:rounded-lg"
      }, React.createElement('div', {
        className: "px-4 py-5 sm:p-6"
      }, React.createElement(ReactQuill, {
        ref: quillRef,
        theme: "snow",
        value: document.conteudo,
        onChange: (content) => setDocument({ ...document, conteudo: content }),
        modules: modules,
        formats: formats,
        placeholder: "Digite o conteúdo do documento...",
        style: { height: '400px', marginBottom: '50px' }
      })))
    ])
  ]);
};

export default DocumentEditor; 