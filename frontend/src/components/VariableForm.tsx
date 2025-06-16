import React from 'react';

interface Variable {
  name: string;
  value: string;
  type: 'text' | 'number' | 'date';
}

interface VariableFormProps {
  variables?: Variable[];
  content?: string;
  onSubmit?: (variables: Variable[]) => void;
  onContentChange?: (newContent: string, variables: Record<string, string>) => void;
  onCancel?: () => void;
  onClose: () => void;
}

const VariableForm = ({ 
  variables = [], 
  content = '', 
  onSubmit, 
  onContentChange, 
  onCancel, 
  onClose 
}: VariableFormProps) => {
  const [formVariables, setFormVariables] = React.useState<Variable[]>(variables);

  React.useEffect(() => {
    if (content && variables.length === 0) {
      // Extrair variáveis do conteúdo se não foram fornecidas
      const extractedVars = extractVariablesFromContent(content);
      setFormVariables(extractedVars);
    }
  }, [content, variables]);

  const extractVariablesFromContent = (text: string): Variable[] => {
    const regex = /\{\{([^}]+)\}\}/g;
    const matches = [...text.matchAll(regex)];
    const uniqueVars = [...new Set(matches.map(match => match[1].trim()))];
    
    return uniqueVars.map(varName => ({
      name: varName,
      value: '',
      type: 'text' as const
    }));
  };

  const handleVariableChange = (index: number, value: string) => {
    const updatedVariables = [...formVariables];
    updatedVariables[index].value = value;
    setFormVariables(updatedVariables);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (onContentChange && content) {
      let newContent = content;
      const variableRecord: Record<string, string> = {};
      
      formVariables.forEach(variable => {
        const placeholder = `{{${variable.name}}}`;
        newContent = newContent.replace(new RegExp(placeholder, 'g'), variable.value);
        variableRecord[variable.name] = variable.value;
      });
      
      onContentChange(newContent, variableRecord);
    } else if (onSubmit) {
      onSubmit(formVariables);
    }
    
    onClose();
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75" onClick={handleCancel}></div>
        </div>

        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <form onSubmit={handleSubmit} className="bg-white px-4 pt-5 pb-4 sm:p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Preencher Variáveis do Template
            </h3>
            
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {formVariables.map((variable, index) => (
                <div key={index} className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    {variable.name}
                  </label>
                  <input
                    type={variable.type}
                    value={variable.value}
                    onChange={(e) => handleVariableChange(index, e.target.value)}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder={`Digite ${variable.name.toLowerCase()}`}
                    required
                  />
                </div>
              ))}
            </div>
            
            <div className="flex justify-end space-x-3 pt-6 border-t mt-6">
              <button
                type="button"
                onClick={handleCancel}
                className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Aplicar Variáveis
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default VariableForm; 