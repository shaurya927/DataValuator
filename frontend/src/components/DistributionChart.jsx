import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export default function DistributionChart({ data, title, color = '#3B82F6' }) {
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-surface border border-glass p-3 rounded-lg shadow-lg">
          <p className="text-secondary text-sm mb-1">{`Score: ${label}`}</p>
          <p className="text-primary font-medium">{`Count: ${payload[0].value}`}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="glass-panel p-5 h-64 flex flex-col">
      {title && <h3 className="text-sm font-medium text-secondary uppercase mb-4">{title}</h3>}
      <div className="flex-1 w-full min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" vertical={false} />
            <XAxis 
              dataKey="bin" 
              stroke="#64748B" 
              fontSize={12}
              tickLine={false}
              axisLine={false}
              tickFormatter={(val) => val.toFixed(1)}
            />
            <YAxis 
              stroke="#64748B" 
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
            <Bar 
              dataKey="count" 
              fill={color} 
              radius={[4, 4, 0, 0]} 
              animationDuration={1000}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
