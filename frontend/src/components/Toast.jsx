import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';

const ToastContext = createContext();

export const useToast = () => useContext(ToastContext);

// Icons
const SuccessIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
    <polyline points="22 4 12 14.01 9 11.01"></polyline>
  </svg>
);

const ErrorIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"></circle>
    <line x1="15" y1="9" x2="9" y2="15"></line>
    <line x1="9" y1="9" x2="15" y2="15"></line>
  </svg>
);

const WarningIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
    <line x1="12" y1="9" x2="12" y2="13"></line>
    <line x1="12" y1="17" x2="12.01" y2="17"></line>
  </svg>
);

const InfoIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"></circle>
    <line x1="12" y1="16" x2="12" y2="12"></line>
    <line x1="12" y1="8" x2="12.01" y2="8"></line>
  </svg>
);

const CloseIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18"></line>
    <line x1="6" y1="6" x2="18" y2="18"></line>
  </svg>
);

const typeStyles = {
  success: { color: '#10b981', glow: 'rgba(16, 185, 129, 0.2)', icon: <SuccessIcon /> },
  error: { color: '#f43f5e', glow: 'rgba(244, 63, 94, 0.2)', icon: <ErrorIcon /> },
  warning: { color: '#f59e0b', glow: 'rgba(245, 158, 11, 0.2)', icon: <WarningIcon /> },
  info: { color: '#2dd4bf', glow: 'rgba(45, 212, 191, 0.2)', icon: <InfoIcon /> }
};

const Toast = ({ id, message, type, onClose }) => {
  const [isLeaving, setIsLeaving] = useState(false);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLeaving(true);
      setTimeout(() => onClose(id), 300); // Wait for animation to finish
    }, 4000);
    return () => clearTimeout(timer);
  }, [id, onClose]);

  const handleClose = () => {
    setIsLeaving(true);
    setTimeout(() => onClose(id), 300);
  };

  const style = typeStyles[type] || typeStyles.info;

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      width: '320px',
      backgroundColor: 'rgba(17, 17, 17, 0.95)',
      backdropFilter: 'blur(16px)',
      WebkitBackdropFilter: 'blur(16px)',
      border: '1px solid rgba(255, 255, 255, 0.06)',
      borderRadius: '12px',
      boxShadow: `0 8px 32px 0 ${style.glow}`,
      marginBottom: '12px',
      overflow: 'hidden',
      color: '#e8e8e8',
      fontFamily: 'Inter, system-ui, sans-serif',
      fontSize: '14px',
      animation: `${isLeaving ? 'toastSlideOut 0.3s forwards' : 'toastSlideIn 0.3s forwards'}`,
      transformOrigin: 'bottom right'
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', padding: '16px' }}>
        <div style={{ color: style.color, marginRight: '12px', display: 'flex', alignItems: 'center', marginTop: '2px' }}>
          {style.icon}
        </div>
        <div style={{ flex: 1, lineHeight: '1.4' }}>
          {message}
        </div>
        <button 
          onClick={handleClose}
          style={{ 
            background: 'none', border: 'none', color: '#a0a0a0', cursor: 'pointer',
            padding: '2px', marginLeft: '8px', display: 'flex', alignItems: 'center'
          }}
          onMouseOver={(e) => e.currentTarget.style.color = '#e8e8e8'}
          onMouseOut={(e) => e.currentTarget.style.color = '#a0a0a0'}
        >
          <CloseIcon />
        </button>
      </div>
      <div style={{ height: '3px', width: '100%', backgroundColor: 'rgba(255,255,255,0.1)' }}>
        <div style={{ 
          height: '100%', 
          backgroundColor: style.color,
          animation: 'toastProgress 4s linear forwards'
        }} />
      </div>
    </div>
  );
};

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    if (!document.getElementById('toast-styles')) {
      const style = document.createElement('style');
      style.id = 'toast-styles';
      style.innerHTML = `
        @keyframes toastSlideIn {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
        @keyframes toastSlideOut {
          from { transform: translateX(0); opacity: 1; }
          to { transform: translateX(100%); opacity: 0; }
        }
        @keyframes toastProgress {
          from { width: 100%; }
          to { width: 0%; }
        }
      `;
      document.head.appendChild(style);
    }
  }, []);

  const addToast = useCallback((message, type = 'info') => {
    setToasts(prev => {
      const newToast = { id: Date.now() + Math.random(), message, type };
      const nextToasts = [...prev, newToast];
      if (nextToasts.length > 5) {
        return nextToasts.slice(nextToasts.length - 5);
      }
      return nextToasts;
    });
  }, []);

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      {typeof document !== 'undefined' && createPortal(
        <div style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          zIndex: 9999,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-end',
          pointerEvents: 'none'
        }}>
          {toasts.map(toast => (
            <div key={toast.id} style={{ pointerEvents: 'auto' }}>
              <Toast 
                id={toast.id} 
                message={toast.message} 
                type={toast.type} 
                onClose={removeToast} 
              />
            </div>
          ))}
        </div>,
        document.body
      )}
    </ToastContext.Provider>
  );
};
