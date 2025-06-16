import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface UsageData {
  plan_info: {
    name: string;
    is_trial: boolean;
    days_remaining: number;
  };
  documents: {
    used: number;
    limit: number;
    percentage: number;
  };
  templates: {
    used: number;
    limit: number;
    percentage: number;
  };
  ai_requests: {
    used: number;
    limit: number;
    percentage: number;
  };
  storage: {
    limit_gb: number;
    users_limit: number;
  };
}

const SubscriptionUsage: React.FC = () => {
  const [usageData, setUsageData] = useState<UsageData | null>(null);
  const [loading, setLoading] = useState(true);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      fetchUsageData();
    }
  }, [isAuthenticated]);

  const fetchUsageData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/subscriptions/usage', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUsageData(data);
      }
    } catch (error) {
      console.error('Error fetching usage data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getProgressBarColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 75) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const formatLimit = (limit: number) => {
    return limit === -1 ? 'Ilimitado' : limit.toString();
  };

  if (!isAuthenticated || loading) {
    return null;
  }

  if (!usageData) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <p className="text-gray-500 text-sm">Dados de uso não disponíveis</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Uso da Assinatura</h3>
        {usageData.plan_info.is_trial && (
          <span className="bg-orange-100 text-orange-800 text-xs font-medium px-2.5 py-0.5 rounded">
            Trial - {usageData.plan_info.days_remaining} dias restantes
          </span>
        )}
      </div>

      <div className="mb-4">
        <p className="text-sm text-gray-600 mb-2">
          <strong>Plano:</strong> {usageData.plan_info.name}
        </p>
      </div>

      <div className="space-y-4">
        {/* Documentos */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <span className="text-sm font-medium text-gray-700">Documentos</span>
            <span className="text-sm text-gray-500">
              {usageData.documents.used} / {formatLimit(usageData.documents.limit)}
            </span>
          </div>
          {usageData.documents.limit !== -1 && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor(usageData.documents.percentage)}`}
                style={{ width: `${Math.min(usageData.documents.percentage, 100)}%` }}
              ></div>
            </div>
          )}
        </div>

        {/* Templates */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <span className="text-sm font-medium text-gray-700">Templates</span>
            <span className="text-sm text-gray-500">
              {usageData.templates.used} / {formatLimit(usageData.templates.limit)}
            </span>
          </div>
          {usageData.templates.limit !== -1 && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor(usageData.templates.percentage)}`}
                style={{ width: `${Math.min(usageData.templates.percentage, 100)}%` }}
              ></div>
            </div>
          )}
        </div>

        {/* IA Requests */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <span className="text-sm font-medium text-gray-700">Consultas IA</span>
            <span className="text-sm text-gray-500">
              {usageData.ai_requests.used} / {formatLimit(usageData.ai_requests.limit)}
            </span>
          </div>
          {usageData.ai_requests.limit !== -1 && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor(usageData.ai_requests.percentage)}`}
                style={{ width: `${Math.min(usageData.ai_requests.percentage, 100)}%` }}
              ></div>
            </div>
          )}
        </div>
      </div>

      {/* Informações adicionais */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Armazenamento:</span>
            <span className="ml-1 font-medium">{usageData.storage.limit_gb}GB</span>
          </div>
          <div>
            <span className="text-gray-600">Usuários:</span>
            <span className="ml-1 font-medium">até {usageData.storage.users_limit}</span>
          </div>
        </div>
      </div>

      {/* Alertas de limite */}
      {(usageData.documents.percentage >= 90 || 
        usageData.templates.percentage >= 90 || 
        usageData.ai_requests.percentage >= 90) && (
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <div className="flex">
            <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                Limite quase atingido
              </h3>
              <p className="text-sm text-yellow-700 mt-1">
                Você está próximo do limite mensal. Considere fazer upgrade do seu plano.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Botão de upgrade */}
      <div className="mt-4">
        <button
          onClick={() => window.location.href = '/pricing'}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          Ver Planos e Fazer Upgrade
        </button>
      </div>
    </div>
  );
};

export default SubscriptionUsage; 