import React from 'react';
import { Brain, Send, MessageSquare, Sparkles } from 'lucide-react';

const AIAssistant = () => {
  const [message, setMessage] = React.useState('');
  const [messages, setMessages] = React.useState([
    {
      id: 1,
      type: 'assistant',
      content: 'Olá! Sou seu assistente IA jurídico. Como posso ajudá-lo hoje?',
      timestamp: new Date()
    }
  ]);

  const handleSendMessage = () => {
    if (!message.trim()) return;

    const newMessage = {
      id: messages.length + 1,
      type: 'user',
      content: message,
      timestamp: new Date()
    };

    setMessages([...messages, newMessage]);
    setMessage('');

    // Simulate AI response
    setTimeout(() => {
      const aiResponse = {
        id: messages.length + 2,
        type: 'assistant',
        content: 'Esta é uma resposta simulada. No MVP completo, aqui seria integrada a API da OpenAI para fornecer respostas jurídicas inteligentes.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, aiResponse]);
    }, 1000);
  };

  const suggestions = [
    'Como redigir uma petição inicial?',
    'Quais cláusulas incluir em um contrato?',
    'Como estruturar uma defesa administrativa?',
    'Modelos de recurso para multa de trânsito'
  ];

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Brain className="h-6 w-6 text-purple-600" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-gray-900">
              Assistente IA Jurídico
            </h1>
            <p className="text-sm text-gray-600">
              Obtenha ajuda inteligente para seus documentos
            </p>
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                msg.type === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <p className="text-sm">{msg.content}</p>
              <p className={`text-xs mt-1 ${
                msg.type === 'user' ? 'text-blue-100' : 'text-gray-500'
              }`}>
                {msg.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Suggestions */}
      {messages.length <= 1 && (
        <div className="px-6 py-4 border-t border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-3">
            Sugestões para começar:
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => setMessage(suggestion)}
                className="text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg text-sm text-gray-700 transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Message Input */}
      <div className="bg-white border-t border-gray-200 p-6">
        <div className="flex space-x-4">
          <div className="flex-1">
            <div className="relative">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Digite sua pergunta jurídica..."
                className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
              <button
                onClick={handleSendMessage}
                disabled={!message.trim()}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 text-purple-600 hover:text-purple-700 disabled:text-gray-400"
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* MVP Info */}
      <div className="bg-purple-50 border-t border-purple-200 p-4">
        <div className="flex items-start space-x-3">
          <Sparkles className="h-5 w-5 text-purple-600 mt-0.5" />
          <div className="text-sm">
            <p className="text-purple-800 font-medium mb-1">
              Assistente IA em Desenvolvimento
            </p>
            <p className="text-purple-700">
              No MVP completo, este assistente será integrado com OpenAI para fornecer:
              análise de documentos, sugestões de redação, correções automáticas e
              aprendizado do seu estilo de escrita.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIAssistant; 