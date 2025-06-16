import { useEffect, useRef, useCallback } from 'react';
import { useToast } from '../contexts/ToastContext';

interface UseAutoSaveOptions {
  data: any;
  onSave: (data: any) => Promise<void>;
  delay?: number;
  enabled?: boolean;
  onError?: (error: any) => void;
}

export const useAutoSave = ({
  data,
  onSave,
  delay = 3000, // 3 segundos por padrão
  enabled = true,
  onError
}: UseAutoSaveOptions) => {
  const { info, error: showError } = useToast();
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastSavedDataRef = useRef<string>('');
  const isSavingRef = useRef(false);

  const saveData = useCallback(async () => {
    if (isSavingRef.current) return;

    const currentDataString = JSON.stringify(data);
    
    // Não salvar se os dados não mudaram
    if (currentDataString === lastSavedDataRef.current) {
      return;
    }

    try {
      isSavingRef.current = true;
      await onSave(data);
      lastSavedDataRef.current = currentDataString;
      info('Documento salvo automaticamente');
    } catch (error) {
      console.error('Erro no salvamento automático:', error);
      if (onError) {
        onError(error);
      } else {
        showError('Erro ao salvar automaticamente');
      }
    } finally {
      isSavingRef.current = false;
    }
  }, [data, onSave, info, showError, onError]);

  useEffect(() => {
    if (!enabled) return;

    // Limpar timeout anterior
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Configurar novo timeout
    timeoutRef.current = setTimeout(() => {
      saveData();
    }, delay);

    // Cleanup
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [data, delay, enabled, saveData]);

  // Cleanup no unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  // Função para forçar salvamento imediato
  const forceSave = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    return saveData();
  }, [saveData]);

  return {
    forceSave,
    isSaving: isSavingRef.current
  };
}; 