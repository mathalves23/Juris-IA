import React from 'react';
import { useLocation } from 'react-router-dom';
import AuthLayout from '../layouts/AuthLayout';
import { Layout as DashboardLayout } from '../layouts/DashboardLayout.js';

interface LayoutProps {
  children: any;
}

const Layout = ({ children }: LayoutProps) => {
  const location = useLocation();
  
  // Páginas que usam AuthLayout
  const authPages = ['/login', '/register', '/forgot-password'];
  
  if (authPages.includes(location.pathname)) {
    // AuthLayout usa Outlet, então retornamos apenas o children
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-blue-600 mb-2">
              LegalAI
            </h1>
            <p className="text-lg text-gray-600">
              Editor IA para Documentos Jurídicos
            </p>
          </div>
        </div>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
            {children}
          </div>
        </div>

        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500">
            Crie e edite documentos jurídicos com assistência de inteligência artificial
          </p>
        </div>
      </div>
    );
  }
  
  // Por padrão, usa DashboardLayout
  return <DashboardLayout>{children}</DashboardLayout>;
};

export default Layout; 