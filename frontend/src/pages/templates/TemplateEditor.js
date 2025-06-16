import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import { templateService, aiService } from '../../services/api';

const TemplateEditor = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [template, setTemplate] = React.useState({
    nome: '',
    categoria_id: '',
    conteudo: '',
    variaveis: {}
  });
  
  const [categories, setCategories] = React.useState([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [isSaving, setIsSaving] = React.useState(false);
  const [error, setError] = React.useState('');
  const [showAIPanel, setShowAIPanel] = React.useState(false);
  const [aiPrompt, setAIPrompt] = React.useState('');
  const [aiResponse, setAIResponse] = React.useState('');
  const [isGenerating, setIsGenerating] = React.useState(false);

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

  // Carregar template existente ou categorias para novo template
  React.useEffect(() => {
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
        // Title and category
        React.createElement('div', {
          key: 'title-section',
          className: "flex flex-col sm:flex-row sm:items-center sm:justify-between"
        }, [
          React.createElement('div', {
            key: 'title-input',
            className: "flex-1"
          }, [
            React.createElement('input', {
              key: 'title',
              type: "text",
              value: template.nome,
              onChange: (e) => setTemplate({ ...template, nome: e.target.value }),
              placeholder: "Nome do modelo",
              className: "shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-lg border-gray-300 rounded-md"
            }),
            
            React.createElement('div', {
              key: 'category-section',
              className: "mt-4"
            }, [
              React.createElement('label', {
                key: 'category-label',
                htmlFor: "category",
                className: "block text-sm font-medium text-gray-700"
              }, 'Categoria'),
              React.createElement('select', {
                key: 'category-select',
                id: "category",
                value: template.categoria_id,
                onChange: (e) => setTemplate({ ...template, categoria_id: e.target.value }),
                className: "mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
              }, [
                React.createElement('option', {
                  key: 'empty',
                  value: ""
                }, 'Selecione uma categoria'),
                ...categories.map((category) => 
                  React.createElement('option', {
                    key: category.id,
                    value: category.id
                  }, category.nome)
                )
              ])
            ])
          ]),
          
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
            
            React.createElement('button', {
              key: 'extract-button',
              onClick: handleExtractVariables,
              className: "inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            }, '📝 Extrair Variáveis'),
            
            React.createElement('button', {
              key: 'save-button',
              onClick: handleSave,
              disabled: isSaving,
              className: `inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white ${isSaving ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500`
            }, isSaving ? 'Salvando...' : 'Salvar')
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
          }, 'Inserir no Modelo')
        ])
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
        value: template.conteudo,
        onChange: (content) => setTemplate({ ...template, conteudo: content }),
        modules: modules,
        formats: formats,
        placeholder: "Digite o conteúdo do modelo...",
        style: { height: '400px', marginBottom: '50px' }
      })))
    ])
  ]);
};

export default TemplateEditor; 