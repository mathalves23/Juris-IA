import React from 'react';

const Dashboard = () => {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          🏛️ JurisIA - Dashboard
        </h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">
              Clientes Ativos
            </h3>
            <p className="text-3xl font-bold text-blue-600">24</p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">
              Processos
            </h3>
            <p className="text-3xl font-bold text-green-600">156</p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">
              Tarefas Pendentes
            </h3>
            <p className="text-3xl font-bold text-yellow-600">18</p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">
              Documentos IA
            </h3>
            <p className="text-3xl font-bold text-purple-600">342</p>
          </div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Quadros Kanban */}
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              📋 Quadros Kanban
            </h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <span className="font-medium">Processos Cíveis</span>
                <span className="text-sm text-blue-600">8 tarefas</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <span className="font-medium">Processos Trabalhistas</span>
                <span className="text-sm text-green-600">5 tarefas</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                <span className="font-medium">Família</span>
                <span className="text-sm text-yellow-600">3 tarefas</span>
              </div>
            </div>
          </div>
          
          {/* Wiki/Memória */}
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              📚 Wiki/Memória Operacional
            </h2>
            <div className="space-y-3">
              <div className="p-3 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-sm">Prazos Processuais</h4>
                <p className="text-xs text-gray-600 mt-1">Atualizado há 2 dias</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-sm">Modelos de Petição</h4>
                <p className="text-xs text-gray-600 mt-1">Atualizado há 1 semana</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-sm">Jurisprudência STJ</h4>
                <p className="text-xs text-gray-600 mt-1">Atualizado há 3 dias</p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Ações Rápidas */}
        <div className="mt-8 bg-white p-6 rounded-lg shadow-sm border">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            ⚡ Ações Rápidas
          </h2>
          <div className="flex flex-wrap gap-4">
            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              + Novo Cliente
            </button>
            <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
              + Novo Processo
            </button>
            <button className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
              + Criar Documento IA
            </button>
            <button className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors">
              + Quadro Kanban
            </button>
          </div>
        </div>
        
        {/* Status do Sistema */}
        <div className="mt-8 bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">
            🚀 Sistema JurisIA Ativo
          </h2>
          <p className="text-blue-100">
            Plataforma jurídica completa com IA, Kanban, Wiki e muito mais.
            Versão 1.0.0 - Pronto para produção!
          </p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 