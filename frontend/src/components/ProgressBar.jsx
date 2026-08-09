import React from 'react';

export default function ProgressBar({ progress, epoch, totalEpochs, loss, accuracy, eta }) {
  // Determine color based on progress (blue -> emerald)
  const isComplete = progress >= 100;
  
  return (
    <div className="glass-panel p-5">
      <div className="flex justify-between items-end mb-3">
        <div>
          <h4 className="text-sm font-medium text-secondary uppercase tracking-wider mb-1">
            Training Progress
          </h4>
          <div className="text-2xl font-semibold flex items-baseline gap-2">
            {progress.toFixed(1)}%
            {epoch && totalEpochs && (
              <span className="text-sm font-normal text-muted">
                (Epoch {epoch}/{totalEpochs})
              </span>
            )}
          </div>
        </div>
        <div className="flex gap-6 text-sm text-right">
          {loss !== undefined && (
            <div>
              <div className="text-muted">Loss</div>
              <div className="font-mono">{loss.toFixed(4)}</div>
            </div>
          )}
          {accuracy !== undefined && (
            <div>
              <div className="text-muted">Accuracy</div>
              <div className="font-mono text-accent-emerald">{(accuracy * 100).toFixed(2)}%</div>
            </div>
          )}
          {eta && !isComplete && (
            <div>
              <div className="text-muted">ETA</div>
              <div className="font-mono">{eta}</div>
            </div>
          )}
        </div>
      </div>
      
      <div className="relative w-full h-3 bg-surface rounded-full overflow-hidden border border-glass shadow-inner">
        <div 
          className={`absolute top-0 left-0 h-full rounded-full transition-all duration-500 ease-out ${
            !isComplete ? 'animate-pulse' : ''
          }`}
          style={{ 
            width: `${Math.min(100, Math.max(0, progress))}%`,
            background: isComplete 
              ? 'var(--accent-emerald)' 
              : 'linear-gradient(90deg, var(--accent-blue) 0%, var(--accent-violet) 100%)',
            boxShadow: '0 0 10px rgba(59, 130, 246, 0.5)'
          }}
        />
      </div>
    </div>
  );
}
