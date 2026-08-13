import React, { useState, useEffect } from 'react';
import { ImageIcon } from './Icons';

export default function SampleCard({ sample, datasetId, onClose }) {
  const [previewData, setPreviewData] = useState(null);
  const [previewType, setPreviewType] = useState('loading'); // 'loading', 'image', 'tabular', 'error'
  const imageUrl = datasetId ? `/api/datasets/${datasetId}/data/${sample?.sample_index}` : null;

  useEffect(() => {
    if (!datasetId || !sample) return;
    
    let isMounted = true;
    const fetchPreview = async () => {
      setPreviewType('loading');
      try {
        const res = await fetch(`/api/datasets/${datasetId}/data/${sample.sample_index}`);
        if (!res.ok) throw new Error('Failed to fetch');
        
        const contentType = res.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          const json = await res.json();
          if (isMounted) {
            setPreviewData(json.data);
            setPreviewType('tabular');
          }
        } else {
          if (isMounted) setPreviewType('image');
        }
      } catch (e) {
        if (isMounted) setPreviewType('error');
      }
    };
    
    fetchPreview();
    return () => { isMounted = false; };
  }, [datasetId, sample]);

  if (!sample) return null;

  return (
    <div className="glass-card flex flex-col h-full overflow-y-auto">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-bold">Sample #{sample.sample_index}</h3>
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
      <div className="w-full bg-surface rounded-lg mb-6 flex items-center justify-center border border-glass overflow-hidden relative" style={{ aspectRatio: '1 / 1' }}>
        {previewType === 'loading' && <div className="text-muted animate-pulse">Loading preview...</div>}
        {previewType === 'error' && <div className="text-4xl text-muted opacity-50"><ImageIcon size={40} /></div>}
        {previewType === 'image' && imageUrl && (
          <img src={imageUrl} alt={`Sample ${sample.sample_index}`} className="w-full h-full object-cover" />
        )}
        {previewType === 'tabular' && previewData && (
          <div className="w-full h-full overflow-y-auto p-4 text-xs font-mono bg-black/20 custom-scrollbar pb-10 text-left">
            {typeof previewData === 'object' ? Object.entries(previewData).map(([k, v]) => (
              <div key={k} className="flex flex-col mb-2 border-b border-glass pb-1">
                <span className="text-muted">{k}</span>
                <span className="truncate text-secondary" title={String(v)}>{String(v)}</span>
              </div>
            )) : (
              <div className="text-secondary">{String(previewData)}</div>
            )}
          </div>
        )}
      </div>

      <div className="space-y-4">
        <h4 className="text-sm font-medium text-secondary uppercase border-b border-glass pb-1">Valuation Metrics</h4>
        
        <MetricRow label="Unified Score" value={sample.unified_score} isHighlight />
        <MetricRow label="Forgetting Events" value={sample.forgetting_count} max={10} isInteger />
        <MetricRow label="Area Under Margin" value={sample.aum_score} max={2} />
        <MetricRow label="TracIn Influence" value={sample.tracin_score} max={1} />
      </div>
    </div>
  );
}

function MetricRow({ label, value, max = 1, isHighlight, isInteger }) {
  const displayValue = isInteger ? value : value?.toFixed(3) || '0.000';
  const percentage = Math.min(100, Math.max(0, ((value || 0) / max) * 100));
  
  return (
    <div>
      <div className="flex justify-between text-sm mb-1 gap-2">
        <span className="text-muted truncate" title={label}>{label}</span>
        <span className={`font-mono shrink-0 ${isHighlight ? 'text-accent-blue font-bold' : ''}`}>{displayValue}</span>
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
