import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Select,
  Radio,
  Divider,
  Alert,
  Typography,
  Row,
  Col,
  Spin,
  Modal,
  Steps,
  Space,
  Tag
} from 'antd';
import {
  CreditCardOutlined,
  SafetyOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  BankOutlined,
  PixOutlined
} from '@ant-design/icons';
import { loadStripe } from '@stripe/stripe-js';
import {
  Elements,
  CardElement,
  useStripe,
  useElements
} from '@stripe/react-stripe-js';
import axios from 'axios';
import './StripePayment.css';

const { Title, Text } = Typography;
const { Step } = Steps;

// Configurar Stripe
const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLIC_KEY || 'pk_test_...');

interface Plan {
  id: string;
  name: string;
  price: number;
  interval: 'month' | 'year';
  features: string[];
  recommended?: boolean;
  discount?: number;
}

interface PaymentProps {
  selectedPlan?: Plan;
  onSuccess?: (subscription: any) => void;
  onError?: (error: string) => void;
}

const PLANS: Plan[] = [
  {
    id: 'basic',
    name: 'Básico',
    price: 99.90,
    interval: 'month',
    features: [
      'Até 50 documentos/mês',
      'Editor IA básico',
      'Templates padrão',
      'Suporte por email'
    ]
  },
  {
    id: 'professional',
    name: 'Profissional',
    price: 199.90,
    interval: 'month',
    recommended: true,
    features: [
      'Documentos ilimitados',
      'IA Assistant avançado',
      'Templates premium',
      'Análise de contratos',
      'Dashboard analytics',
      'Suporte prioritário'
    ]
  },
  {
    id: 'enterprise',
    name: 'Empresarial',
    price: 399.90,
    interval: 'month',
    features: [
      'Tudo do Profissional',
      'Multi-usuários',
      'API personalizada',
      'Integração customizada',
      'Suporte 24/7',
      'Treinamento incluído'
    ]
  },
  {
    id: 'professional-yearly',
    name: 'Profissional Anual',
    price: 1999.90,
    interval: 'year',
    discount: 20,
    features: [
      'Tudo do Profissional',
      '20% de desconto',
      'Suporte premium'
    ]
  }
];

const PAYMENT_METHODS = [
  {
    id: 'stripe',
    name: 'Cartão de Crédito',
    icon: <CreditCardOutlined />,
    description: 'Visa, Mastercard, American Express'
  },
  {
    id: 'pix',
    name: 'PIX',
    icon: <PixOutlined />,
    description: 'Pagamento instantâneo'
  },
  {
    id: 'boleto',
    name: 'Boleto Bancário',
    icon: <BankOutlined />,
    description: 'Vencimento em 3 dias úteis'
  }
];

// Componente principal de pagamento
const StripePayment: React.FC<PaymentProps> = ({ selectedPlan, onSuccess, onError }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState<Plan | null>(selectedPlan || null);
  const [paymentMethod, setPaymentMethod] = useState('stripe');
  const [customerInfo, setCustomerInfo] = useState({
    name: '',
    email: '',
    phone: '',
    document: '',
    address: {
      street: '',
      number: '',
      complement: '',
      district: '',
      city: '',
      state: '',
      zipCode: ''
    }
  });

  const steps = [
    { title: 'Plano', description: 'Escolha seu plano' },
    { title: 'Dados', description: 'Informações pessoais' },
    { title: 'Pagamento', description: 'Método de pagamento' },
    { title: 'Confirmação', description: 'Finalizar assinatura' }
  ];

  const handlePlanSelect = (selectedPlan: Plan) => {
    setPlan(selectedPlan);
    setCurrentStep(1);
  };

  const handleCustomerInfo = (values: any) => {
    setCustomerInfo(values);
    setCurrentStep(2);
  };

  const handlePaymentMethodSelect = (method: string) => {
    setPaymentMethod(method);
    if (method !== 'stripe') {
      setCurrentStep(3);
    }
  };

  return (
    <div className="stripe-payment-container">
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={16}>
          <Card>
            <Steps current={currentStep} items={steps} />
            <Divider />

            {/* Etapa 1: Seleção de Plano */}
            {currentStep === 0 && (
              <PlanSelection
                plans={PLANS}
                selectedPlan={plan}
                onSelect={handlePlanSelect}
              />
            )}

            {/* Etapa 2: Informações do Cliente */}
            {currentStep === 1 && (
              <CustomerInfoForm
                initialValues={customerInfo}
                onSubmit={handleCustomerInfo}
                onBack={() => setCurrentStep(0)}
              />
            )}

            {/* Etapa 3: Método de Pagamento */}
            {currentStep === 2 && (
              <PaymentMethodSelection
                methods={PAYMENT_METHODS}
                selected={paymentMethod}
                onSelect={handlePaymentMethodSelect}
                onBack={() => setCurrentStep(1)}
              />
            )}

            {/* Etapa 4: Confirmação e Pagamento */}
            {currentStep === 3 && (
              <Elements stripe={stripePromise}>
                <PaymentConfirmation
                  plan={plan!}
                  customerInfo={customerInfo}
                  paymentMethod={paymentMethod}
                  onSuccess={onSuccess}
                  onError={onError}
                  onBack={() => setCurrentStep(2)}
                />
              </Elements>
            )}
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <PaymentSummary plan={plan} />
        </Col>
      </Row>
    </div>
  );
};

// Componente de seleção de planos
const PlanSelection: React.FC<{
  plans: Plan[];
  selectedPlan: Plan | null;
  onSelect: (plan: Plan) => void;
}> = ({ plans, selectedPlan, onSelect }) => {
  return (
    <div className="plan-selection">
      <Title level={3}>Escolha seu Plano</Title>
      <Row gutter={[16, 16]}>
        {plans.map((plan) => (
          <Col xs={24} md={12} lg={6} key={plan.id}>
            <Card
              className={`plan-card ${selectedPlan?.id === plan.id ? 'selected' : ''} ${plan.recommended ? 'recommended' : ''}`}
              hoverable
              onClick={() => onSelect(plan)}
            >
              {plan.recommended && (
                <Tag color="gold" className="recommended-tag">
                  Recomendado
                </Tag>
              )}
              
              <div className="plan-header">
                <Title level={4}>{plan.name}</Title>
                <div className="plan-price">
                  <span className="price-currency">R$</span>
                  <span className="price-value">{plan.price.toFixed(2)}</span>
                  <span className="price-period">/{plan.interval === 'month' ? 'mês' : 'ano'}</span>
                </div>
                {plan.discount && (
                  <Text type="success">Economize {plan.discount}%</Text>
                )}
              </div>

              <Divider />

              <div className="plan-features">
                {plan.features.map((feature, index) => (
                  <div key={index} className="feature-item">
                    <CheckCircleOutlined className="feature-icon" />
                    <Text>{feature}</Text>
                  </div>
                ))}
              </div>

              <Button
                type={plan.recommended ? 'primary' : 'default'}
                size="large"
                block
                className="select-plan-btn"
              >
                Selecionar Plano
              </Button>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};

// Formulário de informações do cliente
const CustomerInfoForm: React.FC<{
  initialValues: any;
  onSubmit: (values: any) => void;
  onBack: () => void;
}> = ({ initialValues, onSubmit, onBack }) => {
  const [form] = Form.useForm();

  const handleSubmit = (values: any) => {
    onSubmit(values);
  };

  return (
    <div className="customer-info-form">
      <Title level={3}>Informações Pessoais</Title>
      
      <Form
        form={form}
        layout="vertical"
        initialValues={initialValues}
        onFinish={handleSubmit}
      >
        <Row gutter={16}>
          <Col xs={24} md={12}>
            <Form.Item
              name="name"
              label="Nome Completo"
              rules={[{ required: true, message: 'Nome é obrigatório' }]}
            >
              <Input placeholder="Seu nome completo" />
            </Form.Item>
          </Col>
          
          <Col xs={24} md={12}>
            <Form.Item
              name="email"
              label="E-mail"
              rules={[
                { required: true, message: 'E-mail é obrigatório' },
                { type: 'email', message: 'E-mail inválido' }
              ]}
            >
              <Input placeholder="seu@email.com" />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col xs={24} md={12}>
            <Form.Item
              name="phone"
              label="Telefone"
              rules={[{ required: true, message: 'Telefone é obrigatório' }]}
            >
              <Input placeholder="(11) 99999-9999" />
            </Form.Item>
          </Col>
          
          <Col xs={24} md={12}>
            <Form.Item
              name="document"
              label="CPF/CNPJ"
              rules={[{ required: true, message: 'Documento é obrigatório' }]}
            >
              <Input placeholder="000.000.000-00" />
            </Form.Item>
          </Col>
        </Row>

        <Divider orientation="left">Endereço</Divider>

        <Row gutter={16}>
          <Col xs={24} md={16}>
            <Form.Item name={['address', 'street']} label="Rua">
              <Input placeholder="Nome da rua" />
            </Form.Item>
          </Col>
          
          <Col xs={24} md={8}>
            <Form.Item name={['address', 'number']} label="Número">
              <Input placeholder="Nº" />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col xs={24} md={12}>
            <Form.Item name={['address', 'city']} label="Cidade">
              <Input placeholder="Cidade" />
            </Form.Item>
          </Col>
          
          <Col xs={24} md={12}>
            <Form.Item name={['address', 'state']} label="Estado">
              <Select placeholder="Selecione o estado">
                <Select.Option value="SP">São Paulo</Select.Option>
                <Select.Option value="RJ">Rio de Janeiro</Select.Option>
                <Select.Option value="MG">Minas Gerais</Select.Option>
                {/* Adicionar outros estados */}
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <div className="form-actions">
          <Button onClick={onBack}>Voltar</Button>
          <Button type="primary" htmlType="submit">
            Continuar
          </Button>
        </div>
      </Form>
    </div>
  );
};

// Seleção de método de pagamento
const PaymentMethodSelection: React.FC<{
  methods: any[];
  selected: string;
  onSelect: (method: string) => void;
  onBack: () => void;
}> = ({ methods, selected, onSelect, onBack }) => {
  return (
    <div className="payment-method-selection">
      <Title level={3}>Método de Pagamento</Title>
      
      <Radio.Group
        value={selected}
        onChange={(e) => onSelect(e.target.value)}
        className="payment-methods"
      >
        {methods.map((method) => (
          <Card
            key={method.id}
            className={`payment-method-card ${selected === method.id ? 'selected' : ''}`}
            hoverable
          >
            <Radio value={method.id}>
              <div className="payment-method-content">
                <div className="payment-method-icon">
                  {method.icon}
                </div>
                <div className="payment-method-info">
                  <Title level={5}>{method.name}</Title>
                  <Text type="secondary">{method.description}</Text>
                </div>
              </div>
            </Radio>
          </Card>
        ))}
      </Radio.Group>

      <div className="form-actions">
        <Button onClick={onBack}>Voltar</Button>
        <Button 
          type="primary" 
          onClick={() => onSelect(selected)}
          disabled={!selected}
        >
          Continuar
        </Button>
      </div>
    </div>
  );
};

// Confirmação e processamento do pagamento
const PaymentConfirmation: React.FC<{
  plan: Plan;
  customerInfo: any;
  paymentMethod: string;
  onSuccess?: (subscription: any) => void;
  onError?: (error: string) => void;
  onBack: () => void;
}> = ({ plan, customerInfo, paymentMethod, onSuccess, onError, onBack }) => {
  const stripe = useStripe();
  const elements = useElements();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handlePayment = async () => {
    if (!stripe || !elements) return;

    setLoading(true);
    setError('');

    try {
      if (paymentMethod === 'stripe') {
        await processStripePayment();
      } else if (paymentMethod === 'pix') {
        await processPixPayment();
      } else if (paymentMethod === 'boleto') {
        await processBoletoPayment();
      }
    } catch (err: any) {
      setError(err.message || 'Erro ao processar pagamento');
      onError?.(err.message);
    } finally {
      setLoading(false);
    }
  };

  const processStripePayment = async () => {
    const cardElement = elements!.getElement(CardElement);
    if (!cardElement) return;

    // Criar PaymentMethod
    const { error, paymentMethod: stripePaymentMethod } = await stripe!.createPaymentMethod({
      type: 'card',
      card: cardElement,
      billing_details: {
        name: customerInfo.name,
        email: customerInfo.email,
        phone: customerInfo.phone,
      },
    });

    if (error) {
      throw new Error(error.message);
    }

    // Criar assinatura no backend
    const response = await axios.post('/api/subscriptions/create', {
      paymentMethodId: stripePaymentMethod!.id,
      planId: plan.id,
      customerInfo
    });

    if (response.data.requiresAction) {
      // Confirmar pagamento se necessário (3D Secure)
      const { error: confirmError } = await stripe!.confirmCardPayment(
        response.data.paymentIntent.client_secret
      );

      if (confirmError) {
        throw new Error(confirmError.message);
      }
    }

    onSuccess?.(response.data.subscription);
  };

  const processPixPayment = async () => {
    const response = await axios.post('/api/payments/pix', {
      planId: plan.id,
      customerInfo,
      amount: plan.price
    });

    // Mostrar QR Code do PIX
    Modal.info({
      title: 'Pagamento via PIX',
      content: (
        <div>
          <img src={response.data.qrCode} alt="QR Code PIX" />
          <p>Escaneie o QR Code ou copie o código PIX</p>
          <Input.TextArea value={response.data.pixCode} readOnly />
        </div>
      ),
    });
  };

  const processBoletoPayment = async () => {
    const response = await axios.post('/api/payments/boleto', {
      planId: plan.id,
      customerInfo,
      amount: plan.price
    });

    window.open(response.data.boletoUrl, '_blank');
    onSuccess?.(response.data);
  };

  return (
    <div className="payment-confirmation">
      <Title level={3}>Confirmação</Title>
      
      {error && (
        <Alert
          message="Erro no Pagamento"
          description={error}
          type="error"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      <Card className="order-summary">
        <Title level={4}>Resumo do Pedido</Title>
        <div className="summary-item">
          <Text>Plano: {plan.name}</Text>
          <Text strong>R$ {plan.price.toFixed(2)}</Text>
        </div>
        <Divider />
        <div className="summary-total">
          <Text strong>Total: R$ {plan.price.toFixed(2)}</Text>
        </div>
      </Card>

      {paymentMethod === 'stripe' && (
        <Card title="Dados do Cartão" className="card-details">
          <CardElement
            options={{
              style: {
                base: {
                  fontSize: '16px',
                  color: '#424770',
                  '::placeholder': {
                    color: '#aab7c4',
                  },
                },
              },
            }}
          />
        </Card>
      )}

      <div className="security-info">
        <SafetyOutlined />
        <Text type="secondary">
          Seus dados estão protegidos com criptografia SSL
        </Text>
      </div>

      <div className="form-actions">
        <Button onClick={onBack} disabled={loading}>
          Voltar
        </Button>
        <Button
          type="primary"
          size="large"
          loading={loading}
          onClick={handlePayment}
          icon={loading ? <LoadingOutlined /> : <CreditCardOutlined />}
        >
          {loading ? 'Processando...' : 'Finalizar Pagamento'}
        </Button>
      </div>
    </div>
  );
};

// Resumo do pagamento (sidebar)
const PaymentSummary: React.FC<{ plan: Plan | null }> = ({ plan }) => {
  if (!plan) return null;

  return (
    <Card title="Resumo" className="payment-summary">
      <div className="summary-item">
        <Text>Plano</Text>
        <Text strong>{plan.name}</Text>
      </div>
      
      <div className="summary-item">
        <Text>Período</Text>
        <Text>{plan.interval === 'month' ? 'Mensal' : 'Anual'}</Text>
      </div>
      
      {plan.discount && (
        <div className="summary-item discount">
          <Text>Desconto</Text>
          <Text type="success">-{plan.discount}%</Text>
        </div>
      )}
      
      <Divider />
      
      <div className="summary-total">
        <Text strong>Total</Text>
        <Title level={4} type="primary">
          R$ {plan.price.toFixed(2)}
        </Title>
      </div>

      <div className="summary-features">
        <Title level={5}>Incluído no plano:</Title>
        {plan.features.map((feature, index) => (
          <div key={index} className="feature-item">
            <CheckCircleOutlined />
            <Text>{feature}</Text>
          </div>
        ))}
      </div>
    </Card>
  );
};

export default StripePayment; 