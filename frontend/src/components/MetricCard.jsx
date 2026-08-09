import React, { useState, useEffect } from 'react';

export default function MetricCard({ title, value, subtitle, icon, trend, color = 'blue' }) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    // Simple counter animation
    const targetValue = typeof value === 'number' ? value : parseFloat(value?.toString().replace(/,/g, '') || 0);
    if (isNaN(targetValue)) {
      setDisplayValue(value);
      return;
    }
    
    let start = 0;
    const duration = 1000;
    const increment = targetValue / (duration / 16);
    
    const timer = setInterval(() => {
      start += increment;
      if (start >= targetValue) {
        setDisplayValue(value); // Set exact value at end
        clearInterval(timer);
      } else {
        setDisplayValue(Math.floor(start).toLocaleString());
      }
    }, 16);

    return () => clearInterval(timer);
  }, [value]);

  const colorMap = {
    blue: 'var(--accent-blue)',
    emerald: 'var(--accent-emerald)',
    amber: 'var(--accent-amber)',
    rose: 'var(--accent-rose)',
    violet: 'var(--accent-violet)',
  };

  const cssColor = colorMap[color] || colorMap.blue;

  return (
    <div className="glass-card flex flex-col relative overflow-hidden group">
      {/* Accent strip */}
      <div 
        className="absolute top-0 left-0 w-full h-1 transition-all duration-300 group-hover:h-2"
        style={{ backgroundColor: cssColor }}
      />
      
      <div className="flex justify-between items-start mt-2">
        <div>
          <p className="text-sm text-secondary font-medium uppercase tracking-wide">{title}</p>
          <h3 className="text-3xl font-bold mt-2" style={{ color: cssColor }}>
            {displayValue}
          </h3>
        </div>
        <div className="text-2xl p-2 rounded-lg bg-surface opacity-80 border border-glass group-hover:scale-110 transition-transform">
          {icon}
        </div>
      </div>
      
      {(subtitle || trend) && (
        <div className="mt-4 flex items-center gap-2 text-sm text-muted">
          {trend && (
            <span className={trend === 'up' ? 'text-accent-emerald' : trend === 'down' ? 'text-accent-rose' : ''}>
              {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
            </span>
          )}
          <span>{subtitle}</span>
        </div>
      )}
    </div>
  );
}
