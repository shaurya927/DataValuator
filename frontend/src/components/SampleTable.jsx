import React, { useState } from 'react';

export default function SampleTable({ samples, onRowClick, selectable = false, selectedIndices = new Set(), onSelectionChange }) {
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
            {selectable && (
              <th className="w-10">
                <input 
                  type="checkbox" 
                  checked={samples.length > 0 && selectedIndices.size === samples.length}
                  onChange={(e) => {
                    if (e.target.checked) {
                      onSelectionChange(new Set(samples.map(s => s.sample_index ?? s.index)));
                    } else {
                      onSelectionChange(new Set());
                    }
                  }}
                  className="accent-accent-blue"
                />
              </th>
            )}
            <th onClick={() => requestSort('sample_index')}>Index {sortConfig.key === 'sample_index' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
            <th onClick={() => requestSort('category')}>Category {sortConfig.key === 'category' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
            <th onClick={() => requestSort('unified_score')}>Unified Score {sortConfig.key === 'unified_score' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
            <th onClick={() => requestSort('forgetting_count')}>Forgetting {sortConfig.key === 'forgetting_count' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
            <th onClick={() => requestSort('aum_score')}>AUM {sortConfig.key === 'aum_score' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
            <th onClick={() => requestSort('avg_loss')}>Avg Loss {sortConfig.key === 'avg_loss' && (sortConfig.direction === 'asc' ? '↑' : '↓')}</th>
          </tr>
        </thead>
        <tbody>
          {sortedSamples.map((sample) => {
            const index = sample.sample_index ?? sample.index;
            const isSelected = selectedIndices.has(index);
            return (
              <tr 
                key={index} 
                onClick={() => onRowClick && onRowClick(sample)}
                className={onRowClick ? 'cursor-pointer' : ''}
                style={isSelected ? { backgroundColor: 'rgba(59, 130, 246, 0.1)' } : undefined}
              >
                {selectable && (
                  <td onClick={(e) => e.stopPropagation()}>
                    <input 
                      type="checkbox"
                      checked={isSelected}
                      onChange={(e) => {
                        const newSelected = new Set(selectedIndices);
                        if (e.target.checked) {
                          newSelected.add(index);
                        } else {
                          newSelected.delete(index);
                        }
                        onSelectionChange(newSelected);
                      }}
                      className="accent-accent-blue"
                    />
                  </td>
                )}
                <td className="font-mono text-muted">#{index}</td>
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
              <td className="font-mono">{sample.forgetting_count ?? sample.forgetting}</td>
              <td className="font-mono">{sample.aum_score?.toFixed(3) ?? sample.aum?.toFixed(3) ?? '-'}</td>
              <td className="font-mono">{sample.avg_loss?.toFixed(3) ?? '-'}</td>
            </tr>
          )})}
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
