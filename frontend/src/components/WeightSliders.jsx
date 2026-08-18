import React, { useState } from 'react';

const METRICS = [
  { key: 'forgetting', label: 'Forgetting', tooltip: 'Impact of catastrophic forgetting', color: '#fbbf24' },
  { key: 'loss', label: 'Loss', tooltip: 'Average loss contribution', color: '#fb7185' },
  { key: 'aum', label: 'AUM', tooltip: 'Area under the margin', color: '#007BFF' },
  { key: 'tracin', label: 'TracIn', tooltip: 'Gradient-based influence', color: '#34d399' },
  { key: 'rarity', label: 'Rarity', tooltip: 'Data rarity score', color: '#a78bfa' }
];

const DEFAULT_WEIGHTS = { forgetting: 0.2, loss: 0.15, aum: 0.25, tracin: 0.2, rarity: 0.2 };

export default function WeightSliders({ onApply, loading }) {
  const [collapsed, setCollapsed] = useState(true);
  const [weights, setWeights] = useState(DEFAULT_WEIGHTS);
  const [autoNormalize, setAutoNormalize] = useState(true);

  const handleWeightChange = (key, val) => {
    let newWeights = { ...weights, [key]: val };
    
    if (autoNormalize) {
      const otherKeys = Object.keys(weights).filter(k => k !== key);
      const otherSum = otherKeys.reduce((sum, k) => sum + weights[k], 0);
      const targetOtherSum = 1.0 - val;
      
      if (otherSum === 0) {
        const even = targetOtherSum / otherKeys.length;
        otherKeys.forEach(k => newWeights[k] = even);
      } else {
        const scale = targetOtherSum / otherSum;
        otherKeys.forEach(k => newWeights[k] = weights[k] * scale);
      }
    }
    
    setWeights(newWeights);
  };

  const handleReset = () => {
    setWeights(DEFAULT_WEIGHTS);
  };

  return (
    <div 
      className="glass-panel p-4 mb-4" 
      style={{ 
        backgroundColor: 'var(--bg-surface)', 
        borderColor: 'var(--border-glass)',
        borderRadius: '12px'
      }}
    >
      <div 
        className="flex items-center justify-between cursor-pointer" 
        onClick={() => setCollapsed(!collapsed)}
      >
        <h3 className="text-sm font-medium">Scoring Weights</h3>
        <svg 
          className="transition-transform" 
          style={{ width: 20, height: 20, transform: collapsed ? 'rotate(0deg)' : 'rotate(180deg)', transition: 'transform 0.2s ease' }}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>

      {!collapsed && (
        <div className="mt-4 flex flex-col gap-4">
          <div className="flex items-center justify-between mb-2 text-sm">
            <label className="flex items-center gap-2 cursor-pointer">
              <input 
                type="checkbox" 
                checked={autoNormalize}
                onChange={(e) => setAutoNormalize(e.target.checked)}
                className="accent-accent-blue"
              />
              Auto-normalize (sum to 1.0)
            </label>
            <div className="flex gap-2">
              <button 
                className="btn btn-secondary"
                onClick={handleReset}
              >
                Reset to Defaults
              </button>
              <button 
                className="btn btn-primary"
                style={{ opacity: loading ? 0.5 : 1 }}
                onClick={() => onApply(weights)}
                disabled={loading}
              >
                {loading ? 'Recomputing...' : 'Apply Weights'}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
            {METRICS.map(({ key, label, tooltip, color }) => (
              <div key={key} className="flex flex-col gap-1 group">
                <div className="flex justify-between items-center text-xs text-secondary relative">
                  <span className="font-medium cursor-help" title={tooltip}>{label}</span>
                  <span>{(weights[key] * 100).toFixed(1)}%</span>
                </div>
                <input 
                  type="range" 
                  min="0" 
                  max="1" 
                  step="0.01" 
                  value={weights[key]}
                  onChange={(e) => handleWeightChange(key, parseFloat(e.target.value))}
                  style={{ width: '100%', height: '4px', backgroundColor: 'var(--bg-surface-elevated)', borderRadius: '9999px', appearance: 'none', cursor: 'pointer', accentColor: color }}
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
