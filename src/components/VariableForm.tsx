import React, { useState, useEffect } from 'react';

interface Variable {
  name: string;
  placeholder: string;
  value: string;
  required?: boolean;
  type?: 'text' | 'date' | 'number' | 'email';
}

interface VariableFormProps {
  content: string;
  onContentChange: (newContent: string, variables: Record<string, string>) => void;
  onClose: () => void;
}

const VariableForm: React.FC<VariableFormProps> = ({ content, onContentChange, onClose }) => {
  const [variables, setVariables] = useState<Variable[]>([]);
  const [values, setValues] = useState<Record<string, string>>({});

  // Extrair variáveis do conteúdo
  useEffect(() => {
    const variablePattern = /\{([^}]+)\}/g;
    const foundVariables: Variable[] = [];
    const matches = content.matchAll(variablePattern);
    
    for (const match of matches) {
      const varName = match[1];
      if (!foundVariables.find(v => v.name === varName)) {
        // Determinar tipo baseado no nome da variável
        let type: 'text' | 'date' | 'number' | 'email' = 'text';
        let placeholder = varName.replace(/_/g, ' ').toLowerCase();
        
        if (varName.includes('DATA') || varName.includes('DATE')) {
          type = 'date';
          placeholder = 'Selecione uma data';
        } else if (varName.includes('EMAIL')) {
          type = 'email';
          placeholder = 'exemplo@email.com';
        } else if (varName.includes('VALOR') || varName.includes('PRECO') || varName.includes('NUMERO')) {
          type = 'number';
          placeholder = '0';
        } else {
          placeholder = `Digite ${placeholder}`;
        }
        
        foundVariables.push({
          name: varName,
          placeholder: placeholder,
          value: '',
          required: true,
          type: type
        });
      }
    }
    
    setVariables(foundVariables);
    
    // Inicializar valores vazios
    const initialValues: Record<string, string> = {};
    foundVariables.forEach(variable => {
      initialValues[variable.name] = '';
    });
    setValues(initialValues);
  }, [content]);

  // Atualizar valor de uma variável
  const handleValueChange = (varName: string, value: string) => {
    setValues(prev => ({
      ...prev,
      [varName]: value
    }));
  };

  // Aplicar variáveis ao conteúdo
  const handleApply = () => {
    let updatedContent = content;
    
    // Substituir cada variável pelo seu valor
    Object.entries(values).forEach(([varName, value]) => {
      const regex = new RegExp(`\\{${varName}\\}`, 'g');
      updatedContent = updatedContent.replace(regex, value || `{${varName}}`);
    });
    
    onContentChange(updatedContent, values);
    onClose();
  };

  // Verificar se há campos obrigatórios não preenchidos
  const hasRequiredEmpty = variables.some(variable => 
    variable.required && !values[variable.name]?.trim()
  );

  if (variables.length === 0) {
    return (
      <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
        <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
          <div className="mt-3">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Nenhuma variável encontrada
            </h3>
            <p className="text-sm text-gray-500 mb-4">
              Este documento não contém variáveis para preenchimento.
            </p>
            <div className="flex justify-end">
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border max-w-2xl shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Preencher Variáveis do Documento
          </h3>
          <p className="text-sm text-gray-500 mb-6">
            Preencha os campos abaixo para personalizar seu documento:
          </p>
          
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {variables.map((variable) => (
              <div key={variable.name} className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  {variable.name.replace(/_/g, ' ').toLowerCase()}
                  {variable.required && <span className="text-red-500 ml-1">*</span>}
                </label>
                
                {variable.type === 'date' ? (
                  <input
                    type="date"
                    value={values[variable.name] || ''}
                    onChange={(e) => handleValueChange(variable.name, e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    required={variable.required}
                  />
                ) : variable.type === 'number' ? (
                  <input
                    type="number"
                    value={values[variable.name] || ''}
                    onChange={(e) => handleValueChange(variable.name, e.target.value)}
                    placeholder={variable.placeholder}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    required={variable.required}
                  />
                ) : variable.type === 'email' ? (
                  <input
                    type="email"
                    value={values[variable.name] || ''}
                    onChange={(e) => handleValueChange(variable.name, e.target.value)}
                    placeholder={variable.placeholder}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    required={variable.required}
                  />
                ) : (
                  <textarea
                    value={values[variable.name] || ''}
                    onChange={(e) => handleValueChange(variable.name, e.target.value)}
                    placeholder={variable.placeholder}
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    required={variable.required}
                  />
                )}
                
                <p className="text-xs text-gray-500">
                  Variável: {`{${variable.name}}`}
                </p>
              </div>
            ))}
          </div>
          
          <div className="flex justify-end space-x-3 mt-6 pt-4 border-t">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
            >
              Cancelar
            </button>
            <button
              onClick={handleApply}
              disabled={hasRequiredEmpty}
              className={`px-4 py-2 rounded-md ${
                hasRequiredEmpty
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-indigo-600 text-white hover:bg-indigo-700'
              }`}
            >
              Aplicar Variáveis
            </button>
          </div>
          
          {hasRequiredEmpty && (
            <p className="text-xs text-red-500 mt-2 text-center">
              Por favor, preencha todos os campos obrigatórios
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default VariableForm; 