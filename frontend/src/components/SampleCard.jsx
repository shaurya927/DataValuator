import React from 'react';
import { ImageIcon } from './Icons';

export default function SampleCard({ sample, onClose }) {
  if (!sample) return null;

  return (
    <div className="glass-card flex flex-col h-full overflow-y-auto">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-bold">Sample #{sample.index}</h3>
          <div className="mt-1">
            <span className={`badge badge-${sample.category}`}>
              {sample.category.replace('_', ' ')}
            </span>
          </div>
        </div>
        {onClose && (
          <button onClick={onClose} className="text-muted hover:text-primary p-1">
            ✕
          </button>
        )}
      </div>

      {/* Image / Data Preview Placeholder */}
      <div className="w-full aspect-square bg-surface rounded-lg mb-6 flex items-center justify-center border border-glass overflow-hidden relative">
        {sample.imageUrl ? (
          <img src={sample.imageUrl} alt={`Sample ${sample.index}`} className="w-full h-full object-cover" />
        ) : (
          <div className="text-4xl text-muted opacity-50"><ImageIcon size={40} /></div>
        )}
        <div className="absolute bottom-0 left-0 w-full bg-black/50 backdrop-blur-sm p-2 flex justify-between text-xs font-mono">
          <span>True: <span className="text-accent-emerald">{sample.trueLabel || 'cat'}</span></span>
          <span>Pred: <span className={sample.trueLabel === sample.predLabel ? 'text-accent-emerald' : 'text-accent-rose'}>
            {sample.predLabel || 'dog'}
          </span></span>
        </div>
      </div>

      <div className="space-y-4">
        <h4 className="text-sm font-medium text-secondary uppercase border-b border-glass pb-1">Valuation Metrics</h4>
        
        <MetricRow label="Unified Score" value={sample.unified_score} isHighlight />
        <MetricRow label="Forgetting Events" value={sample.forgetting} max={10} isInteger />
        <MetricRow label="Area Under Margin" value={sample.aum} max={2} />
        <MetricRow label="TracIn Influence" value={sample.tracin} max={1} />
      </div>
    </div>
  );
}

function MetricRow({ label, value, max = 1, isHighlight, isInteger }) {
  const displayValue = isInteger ? value : value?.toFixed(3) || '0.000';
  const percentage = Math.min(100, Math.max(0, ((value || 0) / max) * 100));
  
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-muted">{label}</span>
        <span className={`font-mono ${isHighlight ? 'text-accent-blue font-bold' : ''}`}>{displayValue}</span>
      </div>
      <div className="w-full h-1.5 bg-surface rounded-full overflow-hidden">
        <div 
          className={`h-full rounded-full ${isHighlight ? 'bg-accent-blue' : 'bg-secondary'}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
