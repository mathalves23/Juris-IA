import React from 'react';
import { useToast } from '../contexts/ToastContext.js';
import { authService } from '../services/api';
import { User, Mail, Phone, Building, Calendar, Save, Edit3 } from 'lucide-react';
import Loading, { ButtonLoading } from '../components/Loading';

interface UserProfile {
  id: number;
  nome: string;
  email: string;
  telefone?: string;
  empresa?: string;
  cargo?: string;
  created_at: string;
  subscription?: {
    plano: string;
    status: string;
    expires_at?: string;
  };
}

const Profile = () => {
  const { success, error } = useToast();
  const [profile, setProfile] = React.useState<UserProfile | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [editing, setEditing] = React.useState(false);
  const [formData, setFormData] = React.useState({
    nome: '',
    email: '',
    telefone: '',
    empresa: '',
    cargo: ''
  });

  const loadProfile = useCallback(async () => {
    try {
      setLoading(true);
      const response = await authService.getUserInfo();
      setProfile(response.user);
      setFormData({
        nome: response.user.nome || '',
        email: response.user.email || '',
        telefone: response.user.telefone || '',
        empresa: response.user.empresa || '',
        cargo: response.user.cargo || ''
      });
    } catch (err) {
      error('Erro ao carregar perfil');
    } finally {
      setLoading(false);
    }
  }, [error]);

  React.useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  const handleSave = async () => {
    try {
      setSaving(true);
      await authService.updateUser(formData);
      setProfile(prev => prev ? { ...prev, ...formData } : null);
      setEditing(false);
      success('Perfil atualizado com sucesso!');
    } catch (err) {
      error('Erro ao atualizar perfil');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    if (profile) {
      setFormData({
        nome: profile.nome || '',
        email: profile.email || '',
        telefone: profile.telefone || '',
        empresa: profile.empresa || '',
        cargo: profile.cargo || ''
      });
    }
    setEditing(false);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <Loading size="lg" text="Carregando perfil..." />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <p className="text-gray-500">Erro ao carregar perfil</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Meu Perfil</h1>
                <p className="text-gray-600">Gerencie suas informações pessoais</p>
              </div>
              <div className="flex space-x-3">
                {!editing ? (
                  <button
                    onClick={() => setEditing(true)}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <Edit3 className="w-4 h-4 mr-2" />
                    Editar
                  </button>
                ) : (
                  <div className="flex space-x-2">
                    <button
                      onClick={handleCancel}
                      className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      Cancelar
                    </button>
                    <button
                      onClick={handleSave}
                      disabled={saving}
                      className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                    >
                      {saving ? (
                        <ButtonLoading text="Salvando..." />
                      ) : (
                        <>
                          <Save className="w-4 h-4 mr-2" />
                          Salvar
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Informações Pessoais */}
          <div className="px-6 py-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Informações Pessoais</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <User className="w-4 h-4 inline mr-1" />
                  Nome Completo
                </label>
                {editing ? (
                  <input
                    type="text"
                    value={formData.nome}
                    onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                ) : (
                  <p className="text-gray-900">{profile.nome}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Mail className="w-4 h-4 inline mr-1" />
                  Email
                </label>
                {editing ? (
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                ) : (
                  <p className="text-gray-900">{profile.email}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Phone className="w-4 h-4 inline mr-1" />
                  Telefone
                </label>
                {editing ? (
                  <input
                    type="tel"
                    value={formData.telefone}
                    onChange={(e) => setFormData({ ...formData, telefone: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="(11) 99999-9999"
                  />
                ) : (
                  <p className="text-gray-900">{profile.telefone || 'Não informado'}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Building className="w-4 h-4 inline mr-1" />
                  Empresa
                </label>
                {editing ? (
                  <input
                    type="text"
                    value={formData.empresa}
                    onChange={(e) => setFormData({ ...formData, empresa: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Nome da empresa"
                  />
                ) : (
                  <p className="text-gray-900">{profile.empresa || 'Não informado'}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Cargo
                </label>
                {editing ? (
                  <input
                    type="text"
                    value={formData.cargo}
                    onChange={(e) => setFormData({ ...formData, cargo: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Seu cargo"
                  />
                ) : (
                  <p className="text-gray-900">{profile.cargo || 'Não informado'}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Calendar className="w-4 h-4 inline mr-1" />
                  Membro desde
                </label>
                <p className="text-gray-900">{formatDate(profile.created_at)}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Informações da Assinatura */}
        {profile.subscription && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">Assinatura</h2>
            </div>
            <div className="px-6 py-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Plano</label>
                  <p className="text-gray-900 capitalize">{profile.subscription.plano}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    profile.subscription.status === 'ativo' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {profile.subscription.status}
                  </span>
                </div>
                {profile.subscription.expires_at && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Expira em</label>
                    <p className="text-gray-900">{formatDate(profile.subscription.expires_at)}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
  );
};

export default Profile; 