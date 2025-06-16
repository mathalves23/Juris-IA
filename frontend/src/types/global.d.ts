declare module 'antd' {
  import React from 'react';
  
  export interface ColProps {
    span?: number;
    children?: React.ReactNode;
    [key: string]: any;
  }
  
  export interface LoadingProps {
    size?: string;
    text?: string;
    className?: string;
    [key: string]: any;
  }
  
  export interface LayoutProps {
    children?: React.ReactNode;
    [key: string]: any;
  }
  
  export interface CardProps {
    title?: string;
    size?: string;
    style?: React.CSSProperties;
    children?: React.ReactNode;
    extra?: React.ReactNode;
    [key: string]: any;
  }
  
  export const Col: React.FC<ColProps>;
  export const Card: React.FC<CardProps>;
  export const Layout: React.FC<LayoutProps>;
  export const Loading: React.FC<LoadingProps>;
  export const Row: React.FC<any>;
  export const Button: React.FC<any>;
  export const Space: React.FC<any>;
  export const Alert: React.FC<any>;
  export const List: React.FC<any>;
  export const Tag: React.FC<any>;
  export const Typography: any;
  export const Upload: any;
  export const Input: any;
  export const Form: any;
  export const Select: any;
  export const Tabs: any;
  export const Spin: React.FC<any>;
}

declare module 'react' {
  namespace React {
    interface StyleHTMLAttributes<T> {
      jsx?: boolean;
      [key: string]: any;
    }
  }
}

declare global {
  namespace JSX {
    interface IntrinsicElements {
      style: React.DetailedHTMLProps<React.StyleHTMLAttributes<HTMLStyleElement> & { jsx?: boolean }, HTMLStyleElement>;
    }
  }
}

// Tipos globais adicionais

// React DOM
declare module 'react-dom' {
  export function render(element: React.ReactElement, container: Element | null): void;
  export function createRoot(container: Element): {
    render(element: React.ReactElement): void;
    unmount(): void;
  };
}

// React Router
declare module 'react-router-dom' {
  export function useNavigate(): (to: string) => void;
  export function useParams<T = {}>(): T;
  export function Link(props: { to: string; children: React.ReactNode; className?: string }): React.ReactElement;
  export function BrowserRouter(props: { children: React.ReactNode }): React.ReactElement;
  export function Routes(props: { children: React.ReactNode }): React.ReactElement;
  export function Route(props: { path: string; element: React.ReactElement }): React.ReactElement;
}

// Lucide React
declare module 'lucide-react' {
  export const User: React.FC<{ size?: number; className?: string }>;
  export const Mail: React.FC<{ size?: number; className?: string }>;
  export const Phone: React.FC<{ size?: number; className?: string }>;
  export const Building: React.FC<{ size?: number; className?: string }>;
  export const Calendar: React.FC<{ size?: number; className?: string }>;
  export const Save: React.FC<{ size?: number; className?: string }>;
  export const Edit3: React.FC<{ size?: number; className?: string }>;
  export const UploadOutlined: React.FC<{ size?: number; className?: string }>;
  export const FileTextOutlined: React.FC<{ size?: number; className?: string }>;
  export const CheckCircleOutlined: React.FC<{ size?: number; className?: string }>;
  export const ExclamationCircleOutlined: React.FC<{ size?: number; className?: string }>;
  export const LoadingOutlined: React.FC<{ size?: number; className?: string }>;
  export const EyeOutlined: React.FC<{ size?: number; className?: string }>;
  export const DownloadOutlined: React.FC<{ size?: number; className?: string }>;
  export const PrinterOutlined: React.FC<{ size?: number; className?: string }>;
  export const ShareAltOutlined: React.FC<{ size?: number; className?: string }>;
}

// Ant Design expandido
declare module 'antd' {
  export const Card: React.FC<{
    children?: React.ReactNode;
    title?: string;
    className?: string;
    style?: React.CSSProperties;
    loading?: boolean;
  }>;
  
  export const Row: React.FC<{
    children?: React.ReactNode;
    gutter?: number | [number, number];
    className?: string;
  }>;
  
  export const Col: React.FC<{
    children?: React.ReactNode;
    span?: number;
    xs?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
    className?: string;
  }>;
  
  export const Button: React.FC<{
    children?: React.ReactNode;
    type?: 'primary' | 'default' | 'dashed' | 'text' | 'link';
    size?: 'large' | 'medium' | 'small';
    loading?: boolean;
    disabled?: boolean;
    onClick?: (e: React.MouseEvent) => void;
    htmlType?: 'button' | 'submit' | 'reset';
    className?: string;
    style?: React.CSSProperties;
    icon?: React.ReactNode;
  }>;
  
  export const Upload: React.FC<{
    children?: React.ReactNode;
    action?: string;
    beforeUpload?: (file: UploadFile) => boolean | Promise<boolean>;
    onChange?: (info: { file: UploadFile; fileList: UploadFile[] }) => void;
    onRemove?: (file: UploadFile) => boolean | Promise<boolean>;
    fileList?: UploadFile[];
    multiple?: boolean;
    accept?: string;
    className?: string;
  }>;
  
  export const Alert: React.FC<{
    message?: string;
    description?: string;
    type?: 'success' | 'info' | 'warning' | 'error';
    showIcon?: boolean;
    className?: string;
  }>;
  
  export const Spin: React.FC<{
    children?: React.ReactNode;
    spinning?: boolean;
    size?: 'small' | 'default' | 'large';
    className?: string;
  }>;
  
  export const Tabs: React.FC<{
    children?: React.ReactNode;
    activeKey?: string;
    onChange?: (key: string) => void;
    items?: Array<{
      key: string;
      label: string;
      children: React.ReactNode;
    }>;
    className?: string;
  }>;
  
  export const Typography: {
    Title: React.FC<{
      children?: React.ReactNode;
      level?: 1 | 2 | 3 | 4 | 5;
      className?: string;
    }>;
    Text: React.FC<{
      children?: React.ReactNode;
      type?: 'secondary' | 'success' | 'warning' | 'danger';
      className?: string;
    }>;
  };
  
  export const Space: React.FC<{
    children?: React.ReactNode;
    direction?: 'horizontal' | 'vertical';
    size?: 'small' | 'middle' | 'large' | number;
    className?: string;
  }>;
  
  export const Tag: React.FC<{
    children?: React.ReactNode;
    color?: string;
    className?: string;
  }>;
  
  export const Progress: React.FC<{
    percent?: number;
    status?: 'success' | 'exception' | 'active' | 'normal';
    showInfo?: boolean;
    className?: string;
  }>;
  
  export const message: {
    success: (content: string) => void;
    error: (content: string) => void;
    info: (content: string) => void;
    warning: (content: string) => void;
  };
  
  export const List: React.FC<{
    dataSource?: any[];
    renderItem?: (item: any, index: number) => React.ReactNode;
    className?: string;
  }>;
  
  export const Divider: React.FC<{
    className?: string;
    type?: 'horizontal' | 'vertical';
  }>;
}

// Tipos globais do Window
declare global {
  interface Window {
    gtag?: (...args: any[]) => void;
  }
}

export {}; 