import React, { useState, useEffect } from 'react';
import ScatterPlot from '../components/ScatterPlot';
import SampleTable from '../components/SampleTable';
import SampleCard from '../components/SampleCard';
import { CursorClickIcon } from '../components/Icons';

export default function Explorer() {
  const [selectedSample, setSelectedSample] = useState(null);
  const [data, setData] = useState([]);
  
  useEffect(() => {
    // Generate mock scatter data
    const categories = ['high_value', 'normal', 'redundant', 'harmful', 'suspicious'];
    const mockData = Array.from({ length: 1000 }).map((_, i) => ({
      index: i,
      x: Math.random() * 20 - 10,
      y: Math.random() * 20 - 10,
      category: categories[Math.floor(Math.random() * categories.length)],
      unified_score: Math.random(),
      forgetting: Math.floor(Math.random() * 10),
      aum: Math.random() * 2 - 1,
      avg_loss: Math.random() * 2
    }));
    setData(mockData);
  }, []);

  const handlePointClick = (index) => {
    const sample = data.find(d => d.index === index);
    if (sample) setSelectedSample(sample);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Filters Bar */}
      <div className="glass-panel p-4 mb-4 flex gap-4 items-center">
        <span className="text-sm font-medium text-secondary">Filters:</span>
        {['high_value', 'normal', 'redundant', 'harmful', 'suspicious'].map(cat => (
          <label key={cat} className="flex items-center gap-2 text-sm cursor-pointer hover:text-primary transition-colors">
            <input type="checkbox" defaultChecked className="accent-accent-blue" />
            <span className={`badge badge-${cat}`}>{cat.replace('_', ' ')}</span>
          </label>
        ))}
        <div className="ml-auto">
          <select className="input-field py-1 text-sm bg-surface">
            <option>Color by: Category</option>
            <option>Color by: Score</option>
            <option>Color by: Forgetting</option>
          </select>
        </div>
      </div>

      <div className="flex-1 flex gap-4 min-h-0">
        {/* Main Area: Scatter + Table */}
        <div className="flex-1 flex flex-col gap-4 min-w-0">
          <div className="h-2/3">
            <ScatterPlot data={data} onPointClick={handlePointClick} />
          </div>
          <div className="h-1/3 overflow-hidden rounded-xl border border-glass">
            <div className="h-full overflow-y-auto custom-scrollbar bg-glass">
              <SampleTable samples={data.slice(0, 100)} onRowClick={setSelectedSample} />
            </div>
          </div>
        </div>

        {/* Sidebar: Sample Details */}
        <div className="w-80 shrink-0">
          {selectedSample ? (
            <SampleCard sample={selectedSample} onClose={() => setSelectedSample(null)} />
          ) : (
            <div className="glass-card h-full flex flex-col items-center justify-center text-center p-6 text-muted border-dashed border-2 bg-transparent">
              <div className="text-4xl mb-4 opacity-50"><CursorClickIcon size={40} /></div>
              <p>Click a point on the scatter plot or a row in the table to view sample details.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
