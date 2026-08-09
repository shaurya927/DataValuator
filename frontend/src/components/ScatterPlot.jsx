import React from 'react';
import Plot from 'react-plotly.js';

export default function ScatterPlot({ data, onPointClick }) {
  // Map categories to design system colors
  const colorMap = {
    high_value: '#10B981',
    normal: '#3B82F6',
    redundant: '#F59E0B',
    harmful: '#F43F5E',
    suspicious: '#8B5CF6'
  };

  const traces = Object.keys(colorMap).map(category => {
    const catData = data.filter(d => d.category === category);
    return {
      x: catData.map(d => d.x),
      y: catData.map(d => d.y),
      text: catData.map(d => `Index: ${d.index}<br>Category: ${category}`),
      mode: 'markers',
      type: 'scatter',
      name: category.replace('_', ' '),
      marker: {
        color: colorMap[category],
        size: 6,
        opacity: 0.7,
        line: { width: 0 }
      },
      customdata: catData.map(d => d.index)
    };
  });

  const layout = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#94A3B8', family: 'Inter' },
    margin: { l: 40, r: 20, t: 30, b: 40 },
    xaxis: { 
      gridcolor: 'rgba(148, 163, 184, 0.1)',
      zerolinecolor: 'rgba(148, 163, 184, 0.2)'
    },
    yaxis: { 
      gridcolor: 'rgba(148, 163, 184, 0.1)',
      zerolinecolor: 'rgba(148, 163, 184, 0.2)'
    },
    legend: {
      orientation: 'h',
      y: -0.15,
      x: 0.5,
      xanchor: 'center',
      font: { color: '#F8FAFC' }
    },
    hovermode: 'closest'
  };

  const handleClick = (e) => {
    if (e.points && e.points[0] && onPointClick) {
      const index = e.points[0].customdata;
      onPointClick(index);
    }
  };

  return (
    <div className="glass-panel w-full h-[500px] overflow-hidden">
      <Plot
        data={traces}
        layout={layout}
        config={{ displayModeBar: true, responsive: true }}
        onClick={handleClick}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler={true}
      />
    </div>
  );
}
