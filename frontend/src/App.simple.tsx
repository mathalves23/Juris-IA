import React from 'react';

function App() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            🏛️ JurisIA
          </h1>
          <p className="text-gray-600 mb-6">
            Plataforma Jurídica com Inteligência Artificial
          </p>
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h2 className="text-lg font-semibold text-green-800 mb-2">
                ✅ Frontend Funcionando
              </h2>
              <p className="text-green-700">
                O React está compilando e executando corretamente!
              </p>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h2 className="text-lg font-semibold text-blue-800 mb-2">
                🔧 Próximos Passos
              </h2>
              <ul className="text-blue-700 text-left space-y-1">
                <li>• Corrigir problemas de tipos TypeScript</li>
                <li>• Restaurar funcionalidades completas</li>
                <li>• Testar integração com backend</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App; 