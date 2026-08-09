import React, { useState } from 'react';

export default function SampleTable({ samples, onRowClick }) {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

  const requestSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const getScoreColor = (score) => {
    // Heatmap style logic based on score 0-1
    if (score > 0.8) return 'rgba(16, 185, 129, 0.2)'; // green
    if (score > 0.5) return 'rgba(59, 130, 246, 0.2)'; // blue
    if (score > 0.3) return 'rgba(245, 158, 11, 0.2)'; // amber
    return 'rgba(244, 63, 94, 0.2)'; // red
  };

  const sortedSamples = [...samples].sort((a, b) => {
    if (!sortConfig.key) return 0;
    const aVal = a[sortConfig.key];
    const bVal = b[sortConfig.key];
    if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
    return 0;
  });

  return (
    <div className="table-container">
      <table className="table">
        <thead>
          <tr>
            <th onClick={() => requestSort('index')}>Index {sortConfig.key === 'index' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
            <th onClick={() => requestSort('category')}>Category {sortConfig.key === 'category' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
            <th onClick={() => requestSort('unified_score')}>Unified Score {sortConfig.key === 'unified_score' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
            <th onClick={() => requestSort('forgetting')}>Forgetting {sortConfig.key === 'forgetting' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
            <th onClick={() => requestSort('aum')}>AUM {sortConfig.key === 'aum' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
            <th onClick={() => requestSort('avg_loss')}>Avg Loss {sortConfig.key === 'avg_loss' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
          </tr>
        </thead>
        <tbody>
          {sortedSamples.map((sample) => (
            <tr 
              key={sample.index} 
              onClick={() => onRowClick && onRowClick(sample)}
              className={onRowClick ? 'cursor-pointer' : ''}
            >
              <td className="font-mono text-muted">#{sample.index}</td>
              <td>
                <span className={`badge badge-${sample.category}`}>
                  {sample.category.replace('_', ' ')}
                </span>
              </td>
              <td>
                <div className="score-cell" style={{ backgroundColor: getScoreColor(sample.unified_score) }}>
                  {sample.unified_score.toFixed(3)}
                </div>
              </td>
              <td className="font-mono">{sample.forgetting}</td>
              <td className="font-mono">{sample.aum?.toFixed(3) || '-'}</td>
              <td className="font-mono">{sample.avg_loss?.toFixed(3) || '-'}</td>
            </tr>
          ))}
          {sortedSamples.length === 0 && (
            <tr>
              <td colSpan="6" className="text-center py-8 text-muted">
                No samples found
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
