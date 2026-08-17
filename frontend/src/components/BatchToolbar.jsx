import React from 'react';

export default function BatchToolbar({ visible, selectedCount, onExport, onMarkCategory, onDeselectAll }) {
  if (!visible) return null;

  return (
    <div 
      className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-4 px-6 py-3 rounded-full shadow-2xl animate-[slideUp_0.3s_ease-out]"
      style={{ 
        backgroundColor: 'var(--bg-surface)', 
        backdropFilter: 'blur(12px)',
        border: '1px solid var(--border-glass)',
      }}
    >
      <style>
        {`
          @keyframes slideUp {
            from { transform: translate(-50%, 100%) scale(0.9); opacity: 0; }
            to { transform: translate(-50%, 0) scale(1); opacity: 1; }
          }
        `}
      </style>
      
      <span className="text-sm font-medium text-primary px-3 py-1 rounded-full" style={{ backgroundColor: 'var(--accent-blue-alpha)' }}>
        {selectedCount} sample{selectedCount !== 1 ? 's' : ''} selected
      </span>
      
      <div className="w-px h-6 bg-gray-700" />
      
      <button 
        className="btn btn-secondary"
        onClick={onExport}
      >
        Export CSV
      </button>
      
      <button 
        className="btn" 
        style={{ backgroundColor: 'var(--cat-harmful-bg)', color: 'var(--accent-rose)', border: '1px solid rgba(251, 113, 133, 0.3)' }}
        onClick={() => onMarkCategory('harmful')}
      >
        Mark as Harmful
      </button>
      
      <button 
        className="btn" 
        style={{ backgroundColor: 'rgba(52, 211, 153, 0.1)', color: 'var(--accent-emerald)', border: '1px solid rgba(52, 211, 153, 0.3)' }}
        onClick={() => onMarkCategory('high_value')}
      >
        Mark as High Value
      </button>

      <div className="w-px h-6 bg-gray-700" />
      
      <button 
        className="btn btn-secondary"
        onClick={onDeselectAll}
      >
        Deselect All
      </button>
    </div>
  );
}
