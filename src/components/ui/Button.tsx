import React from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { clsx } from 'clsx';

interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
  disabled?: boolean;
  className?: string;
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  type?: 'button' | 'submit' | 'reset';
  children: React.ReactNode;
}

const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  iconPosition = 'left',
  fullWidth = false,
  disabled,
  className,
  onClick,
  type = 'button',
  children
}) => {
  const baseClasses = [
    'inline-flex items-center justify-center font-medium rounded-lg',
    'transition-all duration-200 ease-in-out',
    'focus:outline-none focus:ring-2 focus:ring-offset-2',
    'disabled:opacity-50 disabled:cursor-not-allowed',
    'relative overflow-hidden'
  ];

  const variantClasses = {
    primary: [
      'bg-blue-600 text-white shadow-sm',
      'hover:bg-blue-700 hover:shadow-md',
      'focus:ring-blue-500',
      'active:bg-blue-800'
    ],
    secondary: [
      'bg-gray-100 text-gray-900 shadow-sm',
      'hover:bg-gray-200 hover:shadow-md',
      'focus:ring-gray-500',
      'active:bg-gray-300'
    ],
    danger: [
      'bg-red-600 text-white shadow-sm',
      'hover:bg-red-700 hover:shadow-md',
      'focus:ring-red-500',
      'active:bg-red-800'
    ],
    ghost: [
      'bg-transparent text-gray-700',
      'hover:bg-gray-100',
      'focus:ring-gray-500'
    ],
    outline: [
      'border-2 border-gray-300 bg-transparent text-gray-700',
      'hover:border-gray-400 hover:bg-gray-50',
      'focus:ring-gray-500'
    ]
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm gap-1.5',
    md: 'px-4 py-2 text-sm gap-2',
    lg: 'px-6 py-3 text-base gap-2.5',
    xl: 'px-8 py-4 text-lg gap-3'
  };

  const iconSizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
    xl: 'w-6 h-6'
  };

  const classes = clsx(
    baseClasses,
    variantClasses[variant],
    sizeClasses[size],
    fullWidth && 'w-full',
    className
  );

  const iconElement = loading ? (
    <Loader2 className={clsx(iconSizeClasses[size], 'animate-spin')} />
  ) : icon ? (
    <span className={iconSizeClasses[size]}>{icon}</span>
  ) : null;

  return (
    <motion.button
      className={classes}
      disabled={disabled || loading}
      onClick={onClick}
      type={type}
      whileHover={{ scale: disabled || loading ? 1 : 1.02 }}
      whileTap={{ scale: disabled || loading ? 1 : 0.98 }}
    >
      {/* Ripple effect */}
      <motion.span
        className="absolute inset-0 bg-white opacity-0 rounded-lg"
        initial={false}
        whileTap={{ opacity: 0.1 }}
        transition={{ duration: 0.1 }}
      />
      
      {iconElement && iconPosition === 'left' && iconElement}
      
      <span className={loading ? 'opacity-0' : 'opacity-100'}>
        {children}
      </span>
      
      {iconElement && iconPosition === 'right' && iconElement}
      
      {loading && (
        <span className="absolute inset-0 flex items-center justify-center">
          <Loader2 className={clsx(iconSizeClasses[size], 'animate-spin')} />
        </span>
      )}
    </motion.button>
  );
};

export default Button; 