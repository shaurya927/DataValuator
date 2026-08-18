import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';

export default React.memo(function ScatterPlot({ data, onPointClick }) {
  // Map categories to design system colors
  const colorMap = {
    high_value: '#34d399',
    normal: '#007BFF',
    redundant: '#fbbf24',
    harmful: '#fb7185',
    suspicious: '#a78bfa'
  };

  const traces = useMemo(() => {
    return Object.keys(colorMap).map(category => {
      const catData = data.filter(d => d.category === category);
      return {
        x: catData.map(d => d.embedding_x ?? d.x),
        y: catData.map(d => d.embedding_y ?? d.y),
        text: catData.map(d => `Index: ${d.sample_index ?? d.index}<br>Category: ${category}`),
        mode: 'markers',
        type: 'scatter',
        name: category.replace('_', ' '),
        marker: {
          color: colorMap[category],
          size: 6,
          opacity: 0.7,
          line: { width: 0 }
        },
        customdata: catData.map(d => d.sample_index ?? d.index)
      };
    });
  }, [data]);

  const layout = useMemo(() => ({
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#a0a0a0', family: 'Inter' },
    margin: { l: 40, r: 20, t: 30, b: 40 },
    xaxis: { 
      gridcolor: 'rgba(255, 255, 255, 0.04)',
      zerolinecolor: 'rgba(255, 255, 255, 0.06)'
    },
    yaxis: { 
      gridcolor: 'rgba(255, 255, 255, 0.04)',
      zerolinecolor: 'rgba(255, 255, 255, 0.06)'
    },
    legend: {
      orientation: 'h',
      y: -0.15,
      x: 0.5,
      xanchor: 'center',
      font: { color: '#e8e8e8' }
    },
    hovermode: 'closest'
  }), []);

  const handleClick = (e) => {
    if (e.points && e.points[0] && onPointClick) {
      const index = e.points[0].customdata;
      onPointClick(index);
    }
  };

  return (
    <div className="glass-panel w-full overflow-hidden" style={{ height: '100%', minHeight: '400px' }}>
      <Plot
        data={traces}
        layout={{ ...layout, datarevision: data.length }}
        revision={data.length}
        config={{ displayModeBar: true, responsive: true }}
        onClick={handleClick}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler={true}
      />
    </div>
  );
});
