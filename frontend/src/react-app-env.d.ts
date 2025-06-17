/// <reference types="react-scripts" />

// React types support - Allow named imports
declare module 'react' {
  export * from '@types/react';
  export { default } from '@types/react';
}

declare module 'react-dom' {
  export * from '@types/react-dom';
  export { default } from '@types/react-dom';
}

declare module 'react-dom/client' {
  export * from '@types/react-dom/client';
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
    __REDUX_DEVTOOLS_EXTENSION_COMPOSE__?: typeof compose;
  }
}

// Definições para módulos CSS
declare module '*.module.css' {
  const classes: { readonly [key: string]: string };
  export default classes;
}

declare module '*.module.scss' {
  const classes: { readonly [key: string]: string };
  export default classes;
}

// Definições para imagens
declare module '*.png' {
  const src: string;
  export default src;
}

declare module '*.jpg' {
  const src: string;
  export default src;
}

declare module '*.jpeg' {
  const src: string;
  export default src;
}

declare module '*.gif' {
  const src: string;
  export default src;
}

declare module '*.svg' {
  const src: string;
  export default src;
}

// Definições para WebSocket
declare global {
  interface WebSocket {
    readyState: number;
  }
}

// Definições para API de notificações
declare global {
  interface Notification {
    new(title: string, options?: NotificationOptions): Notification;
    permission: 'granted' | 'denied' | 'default';
    requestPermission(): Promise<'granted' | 'denied' | 'default'>;
  }
}

// Definições para localStorage
declare global {
  interface Storage {
    getItem(key: string): string | null;
    setItem(key: string, value: string): void;
    removeItem(key: string): void;
    clear(): void;
  }
}

// Definições para PDF
declare module 'html2pdf.js' {
  interface Html2PdfOptions {
    margin?: number | [number, number, number, number];
    filename?: string;
    image?: { type?: string; quality?: number };
    html2canvas?: any;
    jsPDF?: any;
  }

  interface Html2Pdf {
    from(element: HTMLElement): Html2Pdf;
    set(options: Html2PdfOptions): Html2Pdf;
    save(): Promise<void>;
    output(type: string): Promise<any>;
    outputPdf(type?: string): any;
  }

  function html2pdf(): Html2Pdf;
  export = html2pdf;
}

// Definições para Mammoth
declare module 'mammoth' {
  interface ConvertToHtmlOptions {
    styleMap?: string[];
  }

  interface ConvertResult {
    value: string;
    messages: Array<{ type: string; message: string }>;
  }

  export function convertToHtml(input: { arrayBuffer: ArrayBuffer }, options?: ConvertToHtmlOptions): Promise<ConvertResult>;
}

// Definições para File Saver
declare module 'file-saver' {
  export function saveAs(data: Blob | File, filename?: string, options?: { autoBom?: boolean }): void;
}

// Definições para React Query
declare module '@tanstack/react-query' {
  export * from '@tanstack/react-query/types';
}

// Definições para Axios
declare module 'axios' {
  export * from 'axios/index';
  export { default } from 'axios/index';
}

// Definições para TinyMCE
declare module '@tinymce/tinymce-react' {
  import { Component } from 'react';
  
  export interface EditorProps {
    apiKey?: string;
    id?: string;
    init?: any;
    initialValue?: string;
    value?: string;
    onEditorChange?: (content: string, editor: any) => void;
    onInit?: (evt: any, editor: any) => void;
    plugins?: string;
    toolbar?: string;
    height?: number;
    menubar?: boolean;
  }
  
  export class Editor extends Component<EditorProps> {}
}

// Extensões de tipos React para melhor compatibilidade
declare global {
  namespace React {
    export import FC = React.FunctionComponent;
    export import Component = React.Component;
    export import PureComponent = React.PureComponent;
    export import createElement = React.createElement;
    export import createContext = React.createContext;
    export import useState = React.useState;
    export import useEffect = React.useEffect;
    export import useContext = React.useContext;
    export import useMemo = React.useMemo;
    export import useCallback = React.useCallback;
    export import useRef = React.useRef;
    export import useReducer = React.useReducer;
    export import useLayoutEffect = React.useLayoutEffect;
    export import forwardRef = React.forwardRef;
    export import memo = React.memo;
    export import lazy = React.lazy;
    export import Suspense = React.Suspense;
    export import Fragment = React.Fragment;
    export import StrictMode = React.StrictMode;
  }
}

export {}; 