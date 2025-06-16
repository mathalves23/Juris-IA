import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.js';

export const Layout = (props) => {
  const { user, logout, subscription } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const { children } = props;

  return React.createElement('div', {
    className: "min-h-screen bg-gray-100"
  }, [
    // Barra de navegação
    React.createElement('nav', {
      key: 'nav',
      className: "bg-white shadow-sm"
    }, React.createElement('div', {
      className: "max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"
    }, React.createElement('div', {
      className: "flex justify-between h-16"
    }, [
      // Logo e menu principal
      React.createElement('div', {
        key: 'main-menu',
        className: "flex"
      }, [
        React.createElement('div', {
          key: 'logo',
          className: "flex-shrink-0 flex items-center"
        }, React.createElement(Link, {
          to: "/",
          className: "text-xl font-bold text-indigo-600"
        }, "Juris IA")),
        React.createElement('div', {
          key: 'nav-links',
          className: "hidden sm:ml-6 sm:flex sm:space-x-8"
        }, [
          React.createElement(Link, {
            key: 'dashboard',
            to: "/",
            className: "border-indigo-500 text-gray-900 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
          }, "Dashboard"),
          React.createElement(Link, {
            key: 'documents',
            to: "/documents",
            className: "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
          }, "Meus Documentos"),
          React.createElement(Link, {
            key: 'templates',
            to: "/templates",
            className: "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
          }, "Modelos"),
          React.createElement(Link, {
            key: 'contract-analyzer',
            to: "/contract-analyzer",
            className: "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
          }, "🤖 Análise de Contratos"),
          React.createElement(Link, {
            key: 'ai-legal',
            to: "/ai",
            className: "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
          }, "💡 Assistente IA")
        ])
      ]),
      // Menu do usuário
      React.createElement('div', {
        key: 'user-menu',
        className: "hidden sm:ml-6 sm:flex sm:items-center"
      }, [
        // Contador de documentos
        subscription?.plano === 'Editor IA' && React.createElement('div', {
          key: 'doc-counter',
          className: "mr-4 text-sm text-gray-500"
        }, [
          React.createElement('span', { key: 'used', className: "font-medium" }, subscription.documentos_utilizados),
          React.createElement('span', { key: 'sep1' }, " / "),
          React.createElement('span', { key: 'limit', className: "font-medium" }, subscription.limite_documentos),
          React.createElement('span', { key: 'label' }, " documentos")
        ]),
        // Dropdown do perfil
        React.createElement('div', {
          key: 'profile-dropdown',
          className: "ml-3 relative"
        }, [
          React.createElement('div', {
            key: 'profile-button-container'
          }, React.createElement('button', {
            type: "button",
            className: "bg-white rounded-full flex text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500",
            onClick: () => setIsMenuOpen(!isMenuOpen)
          }, [
            React.createElement('span', { key: 'sr', className: "sr-only" }, "Abrir menu do usuário"),
            user?.foto_url ? 
              React.createElement('img', {
                key: 'avatar-img',
                className: "h-8 w-8 rounded-full",
                src: user.foto_url,
                alt: user?.nome
              }) :
              React.createElement('div', {
                key: 'avatar-placeholder',
                className: "h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center"
              }, React.createElement('span', {
                className: "text-indigo-800 font-medium"
              }, user?.nome?.charAt(0)))
          ])),
          isMenuOpen && React.createElement('div', {
            key: 'dropdown-menu',
            className: "origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-white ring-1 ring-black ring-opacity-5 focus:outline-none"
          }, [
            React.createElement('div', {
              key: 'user-info',
              className: "px-4 py-2 text-sm text-gray-700 border-b"
            }, [
              React.createElement('p', { key: 'name', className: "font-medium" }, user?.nome),
              React.createElement('p', { key: 'email', className: "text-gray-500" }, user?.email)
            ]),
            React.createElement(Link, {
              key: 'profile-link',
              to: "/profile",
              className: "block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
            }, "Perfil"),
            React.createElement('button', {
              key: 'logout-btn',
              onClick: handleLogout,
              className: "w-full text-left block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
            }, "Sair")
          ])
        ])
      ]),
      // Menu mobile button
      React.createElement('div', {
        key: 'mobile-menu-btn',
        className: "-mr-2 flex items-center sm:hidden"
      }, React.createElement('button', {
        type: "button",
        className: "inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500",
        onClick: () => setIsMenuOpen(!isMenuOpen)
      }, [
        React.createElement('span', { key: 'sr', className: "sr-only" }, "Abrir menu principal"),
        React.createElement('svg', {
          key: 'icon',
          className: "h-6 w-6",
          xmlns: "http://www.w3.org/2000/svg",
          fill: "none",
          viewBox: "0 0 24 24",
          stroke: "currentColor"
        }, React.createElement('path', {
          strokeLinecap: "round",
          strokeLinejoin: "round",
          strokeWidth: "2",
          d: "M4 6h16M4 12h16M4 18h16"
        }))
      ]))
    ]))),
    // Menu mobile expandido
    isMenuOpen && React.createElement('div', {
      key: 'mobile-menu',
      className: "sm:hidden"
    }, [
      React.createElement('div', {
        key: 'mobile-nav',
        className: "pt-2 pb-3 space-y-1"
      }, [
        React.createElement(Link, {
          key: 'mobile-dashboard',
          to: "/",
          className: "bg-indigo-50 border-indigo-500 text-indigo-700 block pl-3 pr-4 py-2 border-l-4 text-base font-medium"
        }, "Dashboard"),
        React.createElement(Link, {
          key: 'mobile-documents',
          to: "/documents",
          className: "border-transparent text-gray-500 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-700 block pl-3 pr-4 py-2 border-l-4 text-base font-medium"
        }, "Meus Documentos"),
        React.createElement(Link, {
          key: 'mobile-templates',
          to: "/templates",
          className: "border-transparent text-gray-500 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-700 block pl-3 pr-4 py-2 border-l-4 text-base font-medium"
        }, "Modelos"),
        React.createElement(Link, {
          key: 'mobile-contract-analyzer',
          to: "/contract-analyzer",
          className: "border-transparent text-gray-500 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-700 block pl-3 pr-4 py-2 border-l-4 text-base font-medium"
        }, "🤖 Análise de Contratos"),
        React.createElement(Link, {
          key: 'mobile-ai-legal',
          to: "/ai",
          className: "border-transparent text-gray-500 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-700 block pl-3 pr-4 py-2 border-l-4 text-base font-medium"
        }, "💡 Assistente IA")
      ]),
      React.createElement('div', {
        key: 'mobile-user',
        className: "pt-4 pb-3 border-t border-gray-200"
      }, [
        React.createElement('div', {
          key: 'mobile-user-info',
          className: "flex items-center px-4"
        }, [
          user?.foto_url ? 
            React.createElement('img', {
              key: 'mobile-avatar-img',
              className: "h-10 w-10 rounded-full",
              src: user.foto_url,
              alt: user?.nome
            }) :
            React.createElement('div', {
              key: 'mobile-avatar-placeholder',
              className: "h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center"
            }, React.createElement('span', {
              className: "text-indigo-800 font-medium"
            }, user?.nome?.charAt(0))),
          React.createElement('div', {
            key: 'mobile-user-details',
            className: "ml-3"
          }, [
            React.createElement('div', {
              key: 'mobile-name',
              className: "text-base font-medium text-gray-800"
            }, user?.nome),
            React.createElement('div', {
              key: 'mobile-email',
              className: "text-sm font-medium text-gray-500"
            }, user?.email)
          ])
        ]),
        React.createElement('div', {
          key: 'mobile-actions',
          className: "mt-3 space-y-1"
        }, [
          React.createElement(Link, {
            key: 'mobile-profile',
            to: "/profile",
            className: "block px-4 py-2 text-base font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100"
          }, "Perfil"),
          React.createElement('button', {
            key: 'mobile-logout',
            onClick: handleLogout,
            className: "w-full text-left block px-4 py-2 text-base font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100"
          }, "Sair")
        ])
      ])
    ]),
    // Conteúdo principal
    React.createElement('main', {
      key: 'main'
    }, React.createElement('div', {
      className: "max-w-7xl mx-auto py-6 sm:px-6 lg:px-8"
    }, children))
  ]);
}; 