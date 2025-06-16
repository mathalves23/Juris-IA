import React, { forwardRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Eye, EyeOff, AlertCircle, Check } from 'lucide-react';
import { clsx } from 'clsx';

interface InputProps {
  label?: string;
  placeholder?: string;
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url';
  value?: string;
  defaultValue?: string;
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void;
  error?: string;
  success?: boolean;
  disabled?: boolean;
  required?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  className?: string;
  helperText?: string;
  maxLength?: number;
  autoComplete?: string;
  autoFocus?: boolean;
}

const Input = forwardRef<HTMLInputElement, InputProps>(({
  label,
  placeholder,
  type = 'text',
  value,
  defaultValue,
  onChange,
  onBlur,
  onFocus,
  error,
  success,
  disabled,
  required,
  icon,
  iconPosition = 'left',
  size = 'md',
  fullWidth = false,
  className,
  helperText,
  maxLength,
  autoComplete,
  autoFocus
}, ref) => {
  const [showPassword, setShowPassword] = useState(false);
  const [isFocused, setIsFocused] = useState(false);

  const isPassword = type === 'password';
  const inputType = isPassword && showPassword ? 'text' : type;

  const baseClasses = [
    'block w-full rounded-lg border transition-all duration-200',
    'focus:outline-none focus:ring-2 focus:ring-offset-1',
    'disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-50'
  ];

  const sizeClasses = {
    sm: 'px-3 py-2 text-sm',
    md: 'px-4 py-3 text-base',
    lg: 'px-5 py-4 text-lg'
  };

  const stateClasses = error
    ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
    : success
    ? 'border-green-300 focus:border-green-500 focus:ring-green-500'
    : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500';

  const iconSizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6'
  };

  const paddingWithIcon = {
    sm: iconPosition === 'left' ? 'pl-10' : 'pr-10',
    md: iconPosition === 'left' ? 'pl-12' : 'pr-12',
    lg: iconPosition === 'left' ? 'pl-14' : 'pr-14'
  };

  const inputClasses = clsx(
    baseClasses,
    sizeClasses[size],
    stateClasses,
    (icon || isPassword) && paddingWithIcon[size],
    fullWidth ? 'w-full' : 'w-auto',
    className
  );

  const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
    setIsFocused(true);
    onFocus?.(e);
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    setIsFocused(false);
    onBlur?.(e);
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <div className={clsx('relative', fullWidth && 'w-full')}>
      {label && (
        <motion.label
          className={clsx(
            'block text-sm font-medium mb-2 transition-colors duration-200',
            error ? 'text-red-700' : success ? 'text-green-700' : 'text-gray-700',
            disabled && 'opacity-50'
          )}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
        >
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </motion.label>
      )}

      <div className="relative">
        {/* Left Icon */}
        {icon && iconPosition === 'left' && (
          <div className={clsx(
            'absolute left-3 top-1/2 transform -translate-y-1/2 pointer-events-none',
            error ? 'text-red-400' : success ? 'text-green-400' : 'text-gray-400'
          )}>
            <span className={iconSizeClasses[size]}>{icon}</span>
          </div>
        )}

        {/* Input Field */}
        <motion.input
          ref={ref}
          type={inputType}
          value={value}
          defaultValue={defaultValue}
          onChange={onChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          maxLength={maxLength}
          autoComplete={autoComplete}
          autoFocus={autoFocus}
          className={inputClasses}
          whileFocus={{ scale: 1.01 }}
          transition={{ duration: 0.1 }}
        />

        {/* Right Icon or Password Toggle */}
        {(icon && iconPosition === 'right') || isPassword || success || error ? (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
            {/* Success Icon */}
            {success && !error && (
              <Check className={clsx(iconSizeClasses[size], 'text-green-500')} />
            )}

            {/* Error Icon */}
            {error && (
              <AlertCircle className={clsx(iconSizeClasses[size], 'text-red-500')} />
            )}

            {/* Password Toggle */}
            {isPassword && (
              <button
                type="button"
                onClick={togglePasswordVisibility}
                className={clsx(
                  'text-gray-400 hover:text-gray-600 focus:outline-none',
                  'transition-colors duration-200'
                )}
                disabled={disabled}
              >
                {showPassword ? (
                  <EyeOff className={iconSizeClasses[size]} />
                ) : (
                  <Eye className={iconSizeClasses[size]} />
                )}
              </button>
            )}

            {/* Right Icon */}
            {icon && iconPosition === 'right' && !isPassword && (
              <span className={clsx(
                iconSizeClasses[size],
                error ? 'text-red-400' : success ? 'text-green-400' : 'text-gray-400'
              )}>
                {icon}
              </span>
            )}
          </div>
        ) : null}

        {/* Focus Ring Animation */}
        {isFocused && (
          <motion.div
            className={clsx(
              'absolute inset-0 rounded-lg pointer-events-none',
              error ? 'ring-2 ring-red-500' : success ? 'ring-2 ring-green-500' : 'ring-2 ring-blue-500'
            )}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.15 }}
          />
        )}
      </div>

      {/* Helper Text or Error Message */}
      {(helperText || error) && (
        <motion.div
          className="mt-2"
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
        >
          {error ? (
            <p className="text-sm text-red-600 flex items-center">
              <AlertCircle className="w-4 h-4 mr-1" />
              {error}
            </p>
          ) : helperText ? (
            <p className="text-sm text-gray-500">{helperText}</p>
          ) : null}
        </motion.div>
      )}

      {/* Character Count */}
      {maxLength && value && (
        <motion.div
          className="mt-1 text-right"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.2 }}
        >
          <span className={clsx(
            'text-xs',
            value.length > maxLength * 0.9 ? 'text-red-500' : 'text-gray-400'
          )}>
            {value.length}/{maxLength}
          </span>
        </motion.div>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input; 