import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { Toast, ToastType } from '../components/ui/Toast';
import { ConfirmationModal } from '../components/ui/ConfirmationModal';

interface NotificationContextType {
  showToast: (message: string, type: ToastType) => void;
  showConfirm: (options: ConfirmOptions) => void;
}

interface ConfirmOptions {
  title: string;
  message: string;
  onConfirm: () => void;
  confirmText?: string;
  cancelText?: string;
  isDanger?: boolean;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const NotificationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [toast, setToast] = useState<{ message: string; type: ToastType } | null>(null);
  const [confirm, setConfirm] = useState<ConfirmOptions & { isOpen: boolean } | null>(null);

  const showToast = useCallback((message: string, type: ToastType) => {
    setToast({ message, type });
  }, []);

  const hideToast = useCallback(() => {
    setToast(null);
  }, []);

  const showConfirm = useCallback((options: ConfirmOptions) => {
    setConfirm({ ...options, isOpen: true });
  }, []);

  const handleConfirm = useCallback(() => {
    if (confirm?.onConfirm) confirm.onConfirm();
    setConfirm(null);
  }, [confirm]);

  const handleCancel = useCallback(() => {
    setConfirm(null);
  }, []);

  return (
    <NotificationContext.Provider value={{ showToast, showConfirm }}>
      {children}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={hideToast}
        />
      )}
      {confirm && (
        <ConfirmationModal
          isOpen={confirm.isOpen}
          title={confirm.title}
          message={confirm.message}
          onConfirm={handleConfirm}
          onCancel={handleCancel}
          confirmText={confirm.confirmText}
          cancelText={confirm.cancelText}
          isDanger={confirm.isDanger}
        />
      )}
    </NotificationContext.Provider>
  );
};

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};
