import React, { useState } from 'react';

const METRICS = [
  { key: 'forgetting', label: 'Forgetting', tooltip: 'Impact of catastrophic forgetting', color: 'rgb(245, 158, 11)' },
  { key: 'loss', label: 'Loss', tooltip: 'Average loss contribution', color: 'rgb(244, 63, 94)' },
  { key: 'aum', label: 'AUM', tooltip: 'Area under the margin', color: 'rgb(59, 130, 246)' },
  { key: 'tracin', label: 'TracIn', tooltip: 'Gradient-based influence', color: 'rgb(16, 185, 129)' },
  { key: 'rarity', label: 'Rarity', tooltip: 'Data rarity score', color: 'rgb(139, 92, 246)' }
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
        backgroundColor: 'rgba(30, 41, 59, 0.6)', 
        borderColor: 'rgba(148, 163, 184, 0.1)',
        borderRadius: '12px'
      }}
    >
      <div 
        className="flex items-center justify-between cursor-pointer" 
        onClick={() => setCollapsed(!collapsed)}
      >
        <h3 className="text-sm font-medium">Scoring Weights</h3>
        <svg 
          className={`w-5 h-5 transition-transform ${collapsed ? '' : 'rotate-180'}`} 
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
                className="px-3 py-1 text-sm rounded bg-transparent border border-glass hover:bg-glass"
                onClick={handleReset}
              >
                Reset to Defaults
              </button>
              <button 
                className="px-3 py-1 text-sm rounded bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50"
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
                  className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                  style={{ accentColor: color }}
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
