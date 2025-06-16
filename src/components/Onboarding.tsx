import React, { useState } from 'react';
import { X, ChevronLeft, ChevronRight, FileText, Wand2, Download, Upload } from 'lucide-react';
import Modal from './Modal';

interface OnboardingProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: () => void;
}

const Onboarding: React.FC<OnboardingProps> = ({ isOpen, onClose, onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    {
      title: 'Bem-vindo ao LegalAI!',
      description: 'Sua plataforma completa para automação jurídica com IA',
      icon: <FileText className="w-16 h-16 text-blue-600" />,
      content: (
        <div className="text-center space-y-4">
          <p className="text-gray-600">
            O LegalAI é uma plataforma inovadora que combina inteligência artificial 
            com ferramentas jurídicas para acelerar seu trabalho.
          </p>
          <div className="bg-blue-50 p-4 rounded-lg">
            <p className="text-blue-800 font-medium">
              ✨ Crie documentos jurídicos profissionais em minutos
            </p>
          </div>
        </div>
      )
    },
    {
      title: 'Templates Jurídicos',
      description: 'Acesse nossa biblioteca de modelos profissionais',
      icon: <FileText className="w-16 h-16 text-green-600" />,
      content: (
        <div className="space-y-4">
          <p className="text-gray-600">
            Temos templates pré-configurados para os principais tipos de documentos jurídicos:
          </p>
          <ul className="space-y-2 text-sm">
            <li className="flex items-center">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
              Petições Iniciais
            </li>
            <li className="flex items-center">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
              Contestações
            </li>
            <li className="flex items-center">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
              Recursos de Apelação
            </li>
            <li className="flex items-center">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
              Habeas Corpus
            </li>
            <li className="flex items-center">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
              Mandados de Segurança
            </li>
          </ul>
        </div>
      )
    },
    {
      title: 'Inteligência Artificial',
      description: 'Use IA para gerar conteúdo jurídico personalizado',
      icon: <Wand2 className="w-16 h-16 text-purple-600" />,
      content: (
        <div className="space-y-4">
          <p className="text-gray-600">
            Nossa IA pode ajudar você a:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-purple-50 p-3 rounded-lg">
              <h4 className="font-medium text-purple-800">Gerar Cláusulas</h4>
              <p className="text-sm text-purple-600">Cláusulas específicas para contratos</p>
            </div>
            <div className="bg-purple-50 p-3 rounded-lg">
              <h4 className="font-medium text-purple-800">Fundamentação</h4>
              <p className="text-sm text-purple-600">Argumentos jurídicos sólidos</p>
            </div>
            <div className="bg-purple-50 p-3 rounded-lg">
              <h4 className="font-medium text-purple-800">Introduções</h4>
              <p className="text-sm text-purple-600">Aberturas profissionais</p>
            </div>
            <div className="bg-purple-50 p-3 rounded-lg">
              <h4 className="font-medium text-purple-800">Pedidos</h4>
              <p className="text-sm text-purple-600">Solicitações bem estruturadas</p>
            </div>
          </div>
        </div>
      )
    },
    {
      title: 'Upload e Variáveis',
      description: 'Importe documentos e use variáveis dinâmicas',
      icon: <Upload className="w-16 h-16 text-orange-600" />,
      content: (
        <div className="space-y-4">
          <p className="text-gray-600">
            Funcionalidades avançadas para otimizar seu fluxo de trabalho:
          </p>
          <div className="space-y-3">
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                <Upload className="w-4 h-4 text-orange-600" />
              </div>
              <div>
                <h4 className="font-medium">Upload de Documentos</h4>
                <p className="text-sm text-gray-600">Importe arquivos PDF e DOCX existentes</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                <span className="text-orange-600 font-bold text-sm">{'{}'}</span>
              </div>
              <div>
                <h4 className="font-medium">Variáveis Dinâmicas</h4>
                <p className="text-sm text-gray-600">Use {'{NOME}'}, {'{DATA}'} para personalização automática</p>
              </div>
            </div>
          </div>
        </div>
      )
    },
    {
      title: 'Exportação',
      description: 'Exporte seus documentos em PDF ou DOCX',
      icon: <Download className="w-16 h-16 text-indigo-600" />,
      content: (
        <div className="space-y-4">
          <p className="text-gray-600">
            Quando terminar de editar, exporte seus documentos:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border border-gray-200 rounded-lg p-4 text-center">
              <div className="w-12 h-12 bg-red-100 rounded-lg mx-auto mb-2 flex items-center justify-center">
                <span className="text-red-600 font-bold text-sm">PDF</span>
              </div>
              <h4 className="font-medium">Formato PDF</h4>
              <p className="text-sm text-gray-600">Para visualização e impressão</p>
            </div>
            <div className="border border-gray-200 rounded-lg p-4 text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-lg mx-auto mb-2 flex items-center justify-center">
                <span className="text-blue-600 font-bold text-xs">DOCX</span>
              </div>
              <h4 className="font-medium">Formato DOCX</h4>
              <p className="text-sm text-gray-600">Para edição adicional</p>
            </div>
          </div>
        </div>
      )
    }
  ];

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = () => {
    onComplete();
    onClose();
  };

  const currentStepData = steps[currentStep];

  const footer = (
    <div className="flex items-center justify-between w-full">
      <button
        onClick={prevStep}
        disabled={currentStep === 0}
        className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <ChevronLeft className="w-4 h-4 mr-1" />
        Anterior
      </button>

      <div className="flex space-x-2">
        {steps.map((_, index) => (
          <div
            key={index}
            className={`w-2 h-2 rounded-full ${
              index === currentStep ? 'bg-blue-600' : 'bg-gray-300'
            }`}
          />
        ))}
      </div>

      <button
        onClick={nextStep}
        className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        {currentStep === steps.length - 1 ? 'Começar' : 'Próximo'}
        {currentStep < steps.length - 1 && <ChevronRight className="w-4 h-4 ml-1" />}
      </button>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title=""
      size="lg"
      showCloseButton={true}
      closeOnOverlayClick={false}
      footer={footer}
    >
      <div className="text-center space-y-6">
        {/* Ícone */}
        <div className="flex justify-center">
          {currentStepData.icon}
        </div>

        {/* Título e descrição */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            {currentStepData.title}
          </h2>
          <p className="text-gray-600">
            {currentStepData.description}
          </p>
        </div>

        {/* Conteúdo */}
        <div className="text-left">
          {currentStepData.content}
        </div>

        {/* Indicador de progresso */}
        <div className="bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
          />
        </div>
      </div>
    </Modal>
  );
};

export default Onboarding; 