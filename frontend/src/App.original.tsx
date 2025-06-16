import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ToastProvider } from './contexts/ToastContext';
import Loading from './components/Loading';
import Layout from './components/Layout';

// Importação de páginas
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/dashboard/Dashboard';
import TemplatesList from './pages/templates/TemplateList';
import TemplateEditor from './pages/templates/TemplateEditor';
import DocumentsList from './pages/documents/DocumentList';
import DocumentEditor from './pages/documents/DocumentEditor';
import Profile from './pages/Profile';
import Pricing from './pages/Pricing';
import AILegal from './pages/AILegal';
import UploadDocument from './pages/UploadDocument';

// Componente para rotas protegidas
const ProtectedRoute = ({ children }: any) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loading 
          size="lg" 
          text="Verificando autenticação..." 
        />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return <>{children}</>;
};

// Layout protegido
const ProtectedLayout = () => {
  return (
    <ProtectedRoute>
      <Layout>
        <Routes>
          <Route index element={<Dashboard />} />
          <Route path="profile" element={<Profile />} />
          <Route path="templates" element={<TemplatesList />} />
          <Route path="templates/new" element={<TemplateEditor />} />
          <Route path="templates/:id" element={<TemplateEditor />} />
          <Route path="templates/:id/edit" element={<TemplateEditor />} />
          <Route path="documents" element={<DocumentsList />} />
          <Route path="documents/new" element={<DocumentEditor />} />
          <Route path="documents/:id" element={<DocumentEditor />} />
          <Route path="documents/:id/edit" element={<DocumentEditor />} />
          <Route path="ai" element={<AILegal />} />
          <Route path="upload" element={<UploadDocument />} />
        </Routes>
      </Layout>
    </ProtectedRoute>
  );
};

function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <Routes>
            {/* Rotas públicas */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/pricing" element={<Pricing />} />
            
            {/* Rotas protegidas com Layout */}
            <Route path="/*" element={<ProtectedLayout />} />
            
            {/* Rota padrão - redireciona para o dashboard */}
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
      </AuthProvider>
    </ToastProvider>
  );
}

export default App;
