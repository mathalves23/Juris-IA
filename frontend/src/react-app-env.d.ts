/// <reference types="react-scripts" />

// React types support - Allow named imports
declare module 'react' {
  export * from '@types/react';
}

declare module 'react-dom' {
  export * from '@types/react-dom';
}

// JSX support with styled-jsx
declare global {
  namespace JSX {
    interface IntrinsicElements {
      style: React.DetailedHTMLProps<React.StyleHTMLAttributes<HTMLStyleElement> & { jsx?: boolean }, HTMLStyleElement>;
    }
  }
}

// ReactQuill module declaration
declare module 'react-quill' {
  import React from 'react';
  
  export interface ReactQuillProps {
    value?: string;
    defaultValue?: string;
    placeholder?: string;
    readOnly?: boolean;
    theme?: string;
    modules?: any;
    formats?: string[];
    onChange?: (content: string, delta: any, source: any, editor: any) => void;
    onSelectionChange?: (range: any, source: any, editor: any) => void;
    onFocus?: (range: any, source: any, editor: any) => void;
    onBlur?: (previousRange: any, source: any, editor: any) => void;
    onKeyPress?: (event: any) => void;
    onKeyDown?: (event: any) => void;
    onKeyUp?: (event: any) => void;
    bounds?: string | HTMLElement;
    children?: React.ReactNode;
    style?: React.CSSProperties;
    className?: string;
    id?: string;
    preserveWhitespace?: boolean;
  }
  
  export default class ReactQuill extends React.Component<ReactQuillProps> {}
}

// Recharts complete mock
declare module 'recharts' {
  import React from 'react';

  export interface ResponsiveContainerProps {
    width?: string | number;
    height?: string | number;
    children?: React.ReactNode;
    [key: string]: any;
  }

  export interface LineChartProps {
    width?: number;
    height?: number;
    data?: any[];
    children?: React.ReactNode;
    [key: string]: any;
  }

  export interface BarChartProps {
    width?: number;
    height?: number;
    data?: any[];
    children?: React.ReactNode;
    [key: string]: any;
  }

  export interface PieChartProps {
    width?: number;
    height?: number;
    children?: React.ReactNode;
    [key: string]: any;
  }

  export const ResponsiveContainer: React.FC<ResponsiveContainerProps>;
  export const LineChart: React.FC<LineChartProps>;
  export const Line: React.FC<any>;
  export const XAxis: React.FC<any>;
  export const YAxis: React.FC<any>;
  export const CartesianGrid: React.FC<any>;
  export const Tooltip: React.FC<any>;
  export const Legend: React.FC<any>;
  export const BarChart: React.FC<BarChartProps>;
  export const Bar: React.FC<any>;
  export const PieChart: React.FC<PieChartProps>;
  export const Pie: React.FC<any>;
  export const Cell: React.FC<any>;
}

// Ant Design Upload types
declare module 'antd/es/upload' {
  export interface UploadFile<T = any> {
    uid: string;
    name: string;
    fileName?: string;
    lastModified?: number;
    lastModifiedDate?: Date;
    url?: string;
    status?: 'error' | 'success' | 'done' | 'uploading' | 'removed';
    percent?: number;
    thumbUrl?: string;
    originFileObj?: File;
    response?: T;
    error?: any;
    linkProps?: any;
    type?: string;
    size?: number;
    webkitRelativePath?: string;
  }
}

// Extended Ant Design types
declare module 'antd' {
  export interface UploadFile<T = any> {
    uid: string;
    name: string;
    fileName?: string;
    lastModified?: number;
    lastModifiedDate?: Date;
    url?: string;
    status?: 'error' | 'success' | 'done' | 'uploading' | 'removed';
    percent?: number;
    thumbUrl?: string;
    originFileObj?: File;
    response?: T;
    error?: any;
    linkProps?: any;
    type?: string;
    size?: number;
    webkitRelativePath?: string;
  }
}

// Global types
declare global {
  interface DocumentTemplate {
    id: string;
    title: string;
    category: string;
    content: string;
    variables?: string[];
    isPublic?: boolean;
    createdAt?: string;
    updatedAt?: string;
  }

  interface Window {
    React: typeof React;
  }
} 