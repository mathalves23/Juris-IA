declare module 'antd' {
  import * as React from 'react';

  export * from 'antd/lib';
  export { default } from 'antd/lib';

  export interface ButtonProps {
    type?: 'primary' | 'default' | 'dashed' | 'text' | 'link';
    size?: 'large' | 'middle' | 'small';
    htmlType?: 'button' | 'submit' | 'reset';
    block?: boolean;
    danger?: boolean;
    disabled?: boolean;
    ghost?: boolean;
    icon?: React.ReactNode;
    loading?: boolean;
    shape?: 'default' | 'circle' | 'round';
    children?: React.ReactNode;
    onClick?: (event: React.MouseEvent<HTMLElement>) => void;
    className?: string;
    style?: React.CSSProperties;
  }

  export interface InputProps {
    value?: string;
    defaultValue?: string;
    placeholder?: string;
    disabled?: boolean;
    size?: 'large' | 'middle' | 'small';
    prefix?: React.ReactNode;
    suffix?: React.ReactNode;
    addonBefore?: React.ReactNode;
    addonAfter?: React.ReactNode;
    allowClear?: boolean;
    bordered?: boolean;
    maxLength?: number;
    showCount?: boolean;
    status?: 'error' | 'warning';
    type?: string;
    onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onPressEnter?: (e: React.KeyboardEvent<HTMLInputElement>) => void;
    className?: string;
    style?: React.CSSProperties;
  }

  export interface CardProps {
    title?: React.ReactNode;
    extra?: React.ReactNode;
    bordered?: boolean;
    hoverable?: boolean;
    loading?: boolean;
    size?: 'default' | 'small';
    type?: 'inner';
    cover?: React.ReactNode;
    actions?: React.ReactNode[];
    bodyStyle?: React.CSSProperties;
    headStyle?: React.CSSProperties;
    children?: React.ReactNode;
    className?: string;
    style?: React.CSSProperties;
  }

  export interface UploadProps {
    accept?: string;
    action?: string;
    directory?: boolean;
    beforeUpload?: (file: UploadFile, fileList: UploadFile[]) => boolean | Promise<void>;
    customRequest?: (options: any) => void;
    data?: object | ((file: UploadFile) => object);
    defaultFileList?: UploadFile[];
    disabled?: boolean;
    fileList?: UploadFile[];
    headers?: object;
    listType?: 'text' | 'picture' | 'picture-card';
    multiple?: boolean;
    name?: string;
    previewFile?: (file: File | Blob) => Promise<string>;
    showUploadList?: boolean | object;
    supportServerRender?: boolean;
    withCredentials?: boolean;
    onChange?: (info: any) => void;
    onDrop?: (e: React.DragEvent<HTMLDivElement>) => void;
    onPreview?: (file: UploadFile) => void;
    onRemove?: (file: UploadFile) => void | boolean | Promise<void | boolean>;
    children?: React.ReactNode;
    className?: string;
    style?: React.CSSProperties;
  }

  export interface UploadFile {
    uid: string;
    name: string;
    status?: 'uploading' | 'done' | 'error' | 'removed';
    response?: string;
    linkProps?: any;
    type?: string;
    size?: number;
    thumbUrl?: string;
    url?: string;
  }

  export interface SelectProps {
    value?: any;
    defaultValue?: any;
    placeholder?: string;
    disabled?: boolean;
    allowClear?: boolean;
    bordered?: boolean;
    loading?: boolean;
    mode?: 'multiple' | 'tags';
    options?: Array<{ label: React.ReactNode; value: any; disabled?: boolean }>;
    size?: 'large' | 'middle' | 'small';
    status?: 'error' | 'warning';
    suffixIcon?: React.ReactNode;
    removeIcon?: React.ReactNode;
    clearIcon?: React.ReactNode;
    menuItemSelectedIcon?: React.ReactNode;
    onChange?: (value: any, option: any) => void;
    onSearch?: (value: string) => void;
    onFocus?: () => void;
    onBlur?: () => void;
    onClear?: () => void;
    filterOption?: boolean | ((input: string, option: any) => boolean);
    children?: React.ReactNode;
    className?: string;
    style?: React.CSSProperties;
  }

  export interface RadioProps {
    checked?: boolean;
    defaultChecked?: boolean;
    disabled?: boolean;
    value?: any;
    children?: React.ReactNode;
    onChange?: (e: any) => void;
    className?: string;
    style?: React.CSSProperties;
  }

  export interface RadioGroupProps {
    value?: any;
    defaultValue?: any;
    disabled?: boolean;
    name?: string;
    options?: Array<{ label: React.ReactNode; value: any; disabled?: boolean }>;
    optionType?: 'default' | 'button';
    buttonStyle?: 'outline' | 'solid';
    size?: 'large' | 'middle' | 'small';
    onChange?: (e: any) => void;
    children?: React.ReactNode;
    className?: string;
    style?: React.CSSProperties;
  }

  export interface TabsProps {
    activeKey?: string;
    defaultActiveKey?: string;
    hideAdd?: boolean;
    size?: 'large' | 'middle' | 'small';
    tabBarExtraContent?: React.ReactNode;
    tabBarGutter?: number;
    tabBarStyle?: React.CSSProperties;
    tabPosition?: 'top' | 'right' | 'bottom' | 'left';
    type?: 'line' | 'card' | 'editable-card';
    onChange?: (activeKey: string) => void;
    onEdit?: (targetKey: any, action: 'add' | 'remove') => void;
    onTabClick?: (key: string, event: React.MouseEvent) => void;
    children?: React.ReactNode;
    className?: string;
    style?: React.CSSProperties;
  }

  export interface TabPaneProps {
    forceRender?: boolean;
    key: string;
    tab: React.ReactNode;
    disabled?: boolean;
    closable?: boolean;
    children?: React.ReactNode;
    className?: string;
    style?: React.CSSProperties;
  }

  export interface RowProps {
    align?: 'top' | 'middle' | 'bottom';
    gutter?: number | [number, number] | object;
    justify?: 'start' | 'end' | 'center' | 'space-around' | 'space-between' | 'space-evenly';
    wrap?: boolean;
    children?: React.ReactNode;
    className?: string;
    style?: React.CSSProperties;
  }

  export interface ColProps {
    flex?: string | number;
    offset?: number;
    order?: number;
    pull?: number;
    push?: number;
    span?: number;
    xs?: number | object;
    sm?: number | object;
    md?: number | object;
    lg?: number | object;
    xl?: number | object;
    xxl?: number | object;
    children?: React.ReactNode;
    className?: string;
    style?: React.CSSProperties;
  }

  export interface SpinProps {
    delay?: number;
    indicator?: React.ReactNode;
    size?: 'small' | 'default' | 'large';
    spinning?: boolean;
    tip?: React.ReactNode;
    wrapperClassName?: string;
    children?: React.ReactNode;
    className?: string;
    style?: React.CSSProperties;
  }

  export interface AlertProps {
    action?: React.ReactNode;
    afterClose?: () => void;
    banner?: boolean;
    closable?: boolean;
    closeText?: React.ReactNode;
    description?: React.ReactNode;
    icon?: React.ReactNode;
    message?: React.ReactNode;
    showIcon?: boolean;
    type?: 'success' | 'info' | 'warning' | 'error';
    onClose?: (e: React.MouseEvent<HTMLButtonElement>) => void;
    children?: React.ReactNode;
    className?: string;
    style?: React.CSSProperties;
  }

  export interface TypographyProps {
    children?: React.ReactNode;
    className?: string;
    style?: React.CSSProperties;
  }

  export interface SpaceProps {
    align?: 'start' | 'end' | 'center' | 'baseline';
    direction?: 'vertical' | 'horizontal';
    size?: 'small' | 'middle' | 'large' | number;
    split?: React.ReactNode;
    wrap?: boolean;
    children?: React.ReactNode;
    className?: string;
    style?: React.CSSProperties;
  }

  export interface TagProps {
    closable?: boolean;
    closeIcon?: React.ReactNode;
    color?: string;
    icon?: React.ReactNode;
    visible?: boolean;
    onClose?: (e: React.MouseEvent<HTMLElement>) => void;
    children?: React.ReactNode;
    className?: string;
    style?: React.CSSProperties;
  }

  export interface ProgressProps {
    format?: (percent?: number, successPercent?: number) => React.ReactNode;
    percent?: number;
    showInfo?: boolean;
    status?: 'success' | 'exception' | 'normal' | 'active';
    strokeColor?: string | object;
    strokeLinecap?: 'round' | 'butt' | 'square';
    strokeWidth?: number;
    success?: object;
    trailColor?: string;
    type?: 'line' | 'circle' | 'dashboard';
    size?: 'default' | 'small';
    steps?: number;
    className?: string;
    style?: React.CSSProperties;
  }

  export interface ListProps {
    bordered?: boolean;
    dataSource?: any[];
    footer?: React.ReactNode;
    grid?: object;
    header?: React.ReactNode;
    itemLayout?: 'horizontal' | 'vertical';
    loading?: boolean | object;
    loadMore?: React.ReactNode;
    locale?: object;
    pagination?: boolean | object;
    renderItem?: (item: any, index: number) => React.ReactNode;
    rowKey?: string | ((item: any) => string);
    size?: 'default' | 'large' | 'small';
    split?: boolean;
    className?: string;
    style?: React.CSSProperties;
  }

  export interface DividerProps {
    dashed?: boolean;
    orientation?: 'left' | 'right' | 'center';
    orientationMargin?: string | number;
    plain?: boolean;
    style?: React.CSSProperties;
    type?: 'horizontal' | 'vertical';
    children?: React.ReactNode;
    className?: string;
  }

  export const Button: React.FC<ButtonProps>;
  export const Input: React.FC<InputProps> & {
    TextArea: React.FC<any>;
    Password: React.FC<InputProps>;
    Search: React.FC<any>;
    Group: React.FC<any>;
  };
  export const Card: React.FC<CardProps>;
  export const Upload: React.FC<UploadProps> & {
    Dragger: React.FC<UploadProps>;
  };
  export const Select: React.FC<SelectProps> & {
    Option: React.FC<any>;
  };
  export const Radio: React.FC<RadioProps> & {
    Group: React.FC<RadioGroupProps>;
    Button: React.FC<RadioProps>;
  };
  export const Tabs: React.FC<TabsProps> & {
    TabPane: React.FC<TabPaneProps>;
  };
  export const Row: React.FC<RowProps>;
  export const Col: React.FC<ColProps>;
  export const Spin: React.FC<SpinProps>;
  export const Alert: React.FC<AlertProps>;
  export const Typography: React.FC<TypographyProps> & {
    Text: React.FC<any>;
    Title: React.FC<any>;
    Paragraph: React.FC<any>;
  };
  export const Space: React.FC<SpaceProps>;
  export const Tag: React.FC<TagProps>;
  export const Progress: React.FC<ProgressProps>;
  export const List: React.FC<ListProps> & {
    Item: React.FC<any>;
  };
  export const Divider: React.FC<DividerProps>;

  export const message: {
    success: (content: React.ReactNode, duration?: number) => void;
    error: (content: React.ReactNode, duration?: number) => void;
    info: (content: React.ReactNode, duration?: number) => void;
    warning: (content: React.ReactNode, duration?: number) => void;
    warn: (content: React.ReactNode, duration?: number) => void;
    loading: (content: React.ReactNode, duration?: number) => void;
    open: (config: any) => void;
    config: (options: any) => void;
    destroy: () => void;
  };
}

declare module '@ant-design/icons' {
  export * from '@ant-design/icons/lib';
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