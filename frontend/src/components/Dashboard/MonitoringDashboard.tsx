import React from 'react';
import { motion } from 'framer-motion';
import { 
  Activity, 
  AlertTriangle, 
  Shield, 
  Users, 
  Server, 
  Clock,
  TrendingUp,
  TrendingDown,
  Eye,
  Download,
  RefreshCw
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';

// Registrar componentes do Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

interface SystemMetrics {
  timestamp: string;
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  active_connections: number;
  response_time_avg: number;
  error_rate: number;
  requests_per_minute: number;
}

interface HealthCheck {
  status: 'healthy' | 'warning' | 'critical';
  timestamp: string;
  checks: {
    [key: string]: {
      status: 'healthy' | 'warning' | 'critical';
      value: number;
      threshold: number;
    };
  };
}

interface SecuritySummary {
  period_days: number;
  total_events: number;
  risk_summary: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  suspicious_ips: Array<{
    ip_address: string;
    count: number;
  }>;
  failed_logins: number;
  generated_at: string;
}

interface Alert {
  timestamp: string;
  type: string;
  status: 'warning' | 'critical';
  value: number;
  threshold: number;
  message: string;
}

const MonitoringDashboard = () => {
  const [refreshInterval, setRefreshInterval] = React.useState(30000); // 30 segundos
  const [autoRefresh, setAutoRefresh] = React.useState(true);

  // Queries para dados de monitoramento
  const { data: healthData, refetch: refetchHealth } = useQuery<HealthCheck>({
    queryKey: ['health'],
    queryFn: async () => {
      const response = await fetch('/api/health');
      if (!response.ok) throw new Error('Failed to fetch health data');
      return response.json();
    },
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  const { data: metricsData, refetch: refetchMetrics } = useQuery<SystemMetrics>({
    queryKey: ['metrics'],
    queryFn: async () => {
      const response = await fetch('/api/metrics');
      if (!response.ok) throw new Error('Failed to fetch metrics');
      return response.json();
    },
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  const { data: alertsData, refetch: refetchAlerts } = useQuery<{ alerts: Alert[]; total: number }>({
    queryKey: ['alerts'],
    queryFn: async () => {
      const response = await fetch('/api/alerts');
      if (!response.ok) throw new Error('Failed to fetch alerts');
      return response.json();
    },
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  const { data: securityData, refetch: refetchSecurity } = useQuery<SecuritySummary>({
    queryKey: ['security-summary'],
    queryFn: async () => {
      const response = await fetch('/api/audit/security-summary?days=7');
      if (!response.ok) throw new Error('Failed to fetch security summary');
      return response.json();
    },
    refetchInterval: autoRefresh ? 60000 : false, // 1 minuto para dados de segurança
  });

  const handleManualRefresh = () => {
    refetchHealth();
    refetchMetrics();
    refetchAlerts();
    refetchSecurity();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'critical': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <Activity className="w-5 h-5" />;
      case 'warning': return <AlertTriangle className="w-5 h-5" />;
      case 'critical': return <AlertTriangle className="w-5 h-5" />;
      default: return <Activity className="w-5 h-5" />;
    }
  };

  // Configurações dos gráficos
  const systemMetricsChartData = {
    labels: ['CPU', 'Memória', 'Disco'],
    datasets: [
      {
        label: 'Uso do Sistema (%)',
        data: [
          metricsData?.cpu_percent || 0,
          metricsData?.memory_percent || 0,
          metricsData?.disk_percent || 0,
        ],
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)',
        ],
        borderColor: [
          'rgba(59, 130, 246, 1)',
          'rgba(16, 185, 129, 1)',
          'rgba(245, 158, 11, 1)',
        ],
        borderWidth: 2,
      },
    ],
  };

  const securityRiskChartData = {
    labels: ['Baixo', 'Médio', 'Alto', 'Crítico'],
    datasets: [
      {
        label: 'Eventos de Segurança',
        data: [
          securityData?.risk_summary.low || 0,
          securityData?.risk_summary.medium || 0,
          securityData?.risk_summary.high || 0,
          securityData?.risk_summary.critical || 0,
        ],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(127, 29, 29, 0.8)',
        ],
        borderColor: [
          'rgba(34, 197, 94, 1)',
          'rgba(245, 158, 11, 1)',
          'rgba(239, 68, 68, 1)',
          'rgba(127, 29, 29, 1)',
        ],
        borderWidth: 2,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
      },
    },
  };

  const doughnutOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
    },
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard de Monitoramento</h1>
            <p className="text-gray-600 mt-2">
              Monitoramento em tempo real do sistema JurisSaaS
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <label className="text-sm text-gray-600">Auto-refresh:</label>
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`px-3 py-1 rounded-full text-xs font-medium ${
                  autoRefresh 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {autoRefresh ? 'ON' : 'OFF'}
              </button>
            </div>
            
            <button
              onClick={handleManualRefresh}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Atualizar</span>
            </button>
          </div>
        </div>

        {/* Status Geral */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Status do Sistema</p>
                <p className={`text-lg font-semibold capitalize ${
                  healthData?.status === 'healthy' ? 'text-green-600' :
                  healthData?.status === 'warning' ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {healthData?.status || 'Carregando...'}
                </p>
              </div>
              <div className={`p-3 rounded-full ${getStatusColor(healthData?.status || 'unknown')}`}>
                {getStatusIcon(healthData?.status || 'unknown')}
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Tempo de Resposta</p>
                <p className="text-lg font-semibold text-blue-600">
                  {metricsData?.response_time_avg?.toFixed(0) || 0}ms
                </p>
              </div>
              <div className="p-3 rounded-full bg-blue-100 text-blue-600">
                <Clock className="w-5 h-5" />
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Taxa de Erro</p>
                <p className="text-lg font-semibold text-red-600">
                  {metricsData?.error_rate?.toFixed(1) || 0}%
                </p>
              </div>
              <div className="p-3 rounded-full bg-red-100 text-red-600">
                <AlertTriangle className="w-5 h-5" />
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Requests/min</p>
                <p className="text-lg font-semibold text-green-600">
                  {metricsData?.requests_per_minute || 0}
                </p>
              </div>
              <div className="p-3 rounded-full bg-green-100 text-green-600">
                <TrendingUp className="w-5 h-5" />
              </div>
            </div>
          </motion.div>
        </div>

        {/* Gráficos */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Uso de Recursos do Sistema
            </h3>
            <div className="h-64">
              <Bar data={systemMetricsChartData} options={chartOptions} />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Eventos de Segurança (7 dias)
            </h3>
            <div className="h-64">
              <Doughnut data={securityRiskChartData} options={doughnutOptions} />
            </div>
          </motion.div>
        </div>

        {/* Alertas e Segurança */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Alertas Recentes */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Alertas Recentes</h3>
              <span className="text-sm text-gray-500">
                {alertsData?.total || 0} total
              </span>
            </div>
            
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {alertsData?.alerts?.slice(0, 5).map((alert, index) => (
                <div
                  key={index}
                  className={`p-3 rounded-lg border-l-4 ${
                    alert.status === 'critical' 
                      ? 'border-red-500 bg-red-50' 
                      : 'border-yellow-500 bg-yellow-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <AlertTriangle className={`w-4 h-4 ${
                        alert.status === 'critical' ? 'text-red-600' : 'text-yellow-600'
                      }`} />
                      <span className="font-medium text-gray-900">
                        {alert.type.toUpperCase()}
                      </span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {new Date(alert.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    {alert.message}
                  </p>
                </div>
              )) || (
                <div className="text-center text-gray-500 py-8">
                  <Shield className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>Nenhum alerta recente</p>
                </div>
              )}
            </div>
          </motion.div>

          {/* IPs Suspeitos */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">IPs Suspeitos</h3>
              <span className="text-sm text-gray-500">
                Últimos 7 dias
              </span>
            </div>
            
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {securityData?.suspicious_ips?.slice(0, 5).map((ip, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-red-50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                    <span className="font-mono text-sm text-gray-900">
                      {ip.ip_address}
                    </span>
                  </div>
                  <span className="text-sm font-medium text-red-600">
                    {ip.count} eventos
                  </span>
                </div>
              )) || (
                <div className="text-center text-gray-500 py-8">
                  <Eye className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>Nenhum IP suspeito detectado</p>
                </div>
              )}
            </div>
          </motion.div>
        </div>

        {/* Detalhes dos Checks de Saúde */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl shadow-sm p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Detalhes dos Checks de Saúde
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {healthData?.checks && Object.entries(healthData.checks).map(([key, check]) => (
              <div
                key={key}
                className={`p-4 rounded-lg border ${
                  check.status === 'healthy' 
                    ? 'border-green-200 bg-green-50' 
                    : check.status === 'warning'
                    ? 'border-yellow-200 bg-yellow-50'
                    : 'border-red-200 bg-red-50'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-900 capitalize">
                    {key.replace('_', ' ')}
                  </span>
                  <div className={`w-3 h-3 rounded-full ${
                    check.status === 'healthy' ? 'bg-green-500' :
                    check.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                  }`}></div>
                </div>
                
                <div className="text-lg font-semibold text-gray-900">
                  {check.value.toFixed(1)}%
                </div>
                
                <div className="text-xs text-gray-500">
                  Limite: {check.threshold}%
                </div>
                
                <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      check.status === 'healthy' ? 'bg-green-500' :
                      check.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${Math.min(check.value, 100)}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Footer com informações de atualização */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>
            Última atualização: {healthData?.timestamp ? 
              new Date(healthData.timestamp).toLocaleString() : 
              'Carregando...'
            }
          </p>
          <p className="mt-1">
            Auto-refresh: {autoRefresh ? `${refreshInterval/1000}s` : 'Desabilitado'}
          </p>
        </div>
      </div>
    </div>
  );
};

export default MonitoringDashboard; 