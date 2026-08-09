import React from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from 'recharts';

export default function ComparisonChart({ data }) {
  // data format: [{ epoch: 1, original: 85.2, pruned: 84.9 }, ...]
  
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-surface border border-glass p-3 rounded-lg shadow-lg">
          <p className="text-secondary text-sm mb-2">{`Epoch ${label}`}</p>
          {payload.map((entry, index) => (
            <div key={index} className="flex items-center gap-2 mb-1">
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
              <span className="text-sm text-primary">{entry.name}:</span>
              <span className="font-mono text-sm">{entry.value.toFixed(2)}%</span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="glass-panel p-5 h-80 flex flex-col">
      <h3 className="text-sm font-medium text-secondary uppercase mb-4">Accuracy Comparison</h3>
      <div className="flex-1 w-full min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 20, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
            <XAxis 
              dataKey="epoch" 
              stroke="#64748B" 
              fontSize={12}
              tickLine={false}
            />
            <YAxis 
              stroke="#64748B" 
              fontSize={12}
              tickLine={false}
              domain={['auto', 'auto']}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: '12px', color: '#94A3B8' }} />
            <Line 
              type="monotone" 
              dataKey="original" 
              name="Original Model" 
              stroke="#3B82F6" 
              strokeWidth={3}
              dot={false}
              activeDot={{ r: 6 }}
            />
            <Line 
              type="monotone" 
              dataKey="pruned" 
              name="Optimized (Pruned)" 
              stroke="#10B981" 
              strokeWidth={3}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
