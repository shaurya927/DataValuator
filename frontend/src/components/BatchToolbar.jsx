import React from 'react';

export default function BatchToolbar({ visible, selectedCount, onExport, onMarkCategory, onDeselectAll }) {
  if (!visible) return null;

  return (
    <div 
      className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-4 px-6 py-3 rounded-full shadow-2xl animate-[slideUp_0.3s_ease-out]"
      style={{ 
        backgroundColor: 'rgba(30, 41, 59, 0.8)', 
        backdropFilter: 'blur(12px)',
        border: '1px solid rgba(148, 163, 184, 0.2)',
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
      
      <span className="text-sm font-medium text-white bg-blue-500/20 px-3 py-1 rounded-full">
        {selectedCount} sample{selectedCount !== 1 ? 's' : ''} selected
      </span>
      
      <div className="w-px h-6 bg-gray-700" />
      
      <button 
        className="text-sm hover:text-white transition-colors"
        onClick={onExport}
      >
        Export CSV
      </button>
      
      <button 
        className="text-sm text-rose-400 hover:text-rose-300 transition-colors"
        onClick={() => onMarkCategory('harmful')}
      >
        Mark as Harmful
      </button>
      
      <button 
        className="text-sm text-emerald-400 hover:text-emerald-300 transition-colors"
        onClick={() => onMarkCategory('high_value')}
      >
        Mark as High Value
      </button>

      <div className="w-px h-6 bg-gray-700" />
      
      <button 
        className="text-sm text-gray-400 hover:text-white transition-colors"
        onClick={onDeselectAll}
      >
        Deselect All
      </button>
    </div>
  );
}
