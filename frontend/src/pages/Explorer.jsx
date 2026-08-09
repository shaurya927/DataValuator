import React, { useState, useEffect, useMemo } from 'react';
import ScatterPlot from '../components/ScatterPlot';
import SampleTable from '../components/SampleTable';
import SampleCard from '../components/SampleCard';
import { CursorClickIcon } from '../components/Icons';
import { api } from '../api/client';

export default function Explorer() {
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedSample, setSelectedSample] = useState(null);
  
  const [filters, setFilters] = useState({
    high_value: true,
    normal: true,
    redundant: true,
    harmful: true,
    suspicious: true
  });

  // Fetch runs on mount
  useEffect(() => {
    api.getTrainingHistory().then(res => {
      // Filter for completed runs that have valuations
      const completedRuns = res.filter(r => r.status === 'completed');
      setRuns(completedRuns);
      if (completedRuns.length > 0) {
        setSelectedRun(completedRuns[0]);
      }
    });
  }, []);

  // Fetch valuations when run changes
  useEffect(() => {
    if (selectedRun) {
      setLoading(true);
      setSelectedSample(null);
      api.getValuationSamples(selectedRun.id, { per_page: 2000 })
        .then(res => setData(res.samples || []))
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [selectedRun]);

  const handlePointClick = (index) => {
    const sample = data.find(d => d.sample_index === index);
    if (sample) setSelectedSample(sample);
  };

  const toggleFilter = (cat) => {
    setFilters(prev => ({ ...prev, [cat]: !prev[cat] }));
  };

  const handlePrune = async () => {
    if (!selectedRun) return;
    try {
      await api.startPruneExperiment({
        run_id: selectedRun.id,
        type: 'prune',
        exclude_categories: ['harmful', 'redundant']
      });
      alert('Pruning experiment started! Check the backend logs or experiments page.');
    } catch (e) {
      alert('Failed to start experiment: ' + e.message);
    }
  };

  const handleExport = () => {
    if (selectedRun) {
      api.exportRefinedDataset(selectedRun.id);
    }
  };

  const filteredData = useMemo(() => {
    return data.filter(d => filters[d.category]);
  }, [data, filters]);

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Top Bar: Run Selector & Actions */}
      <div className="flex gap-4 mb-4 items-center">
        <select 
          className="input-field max-w-xs"
          value={selectedRun?.id || ''}
          onChange={(e) => setSelectedRun(runs.find(r => r.id === e.target.value))}
        >
          <option value="" disabled>Select a Training Run...</option>
          {runs.map(run => (
            <option key={run.id} value={run.id}>
              {run.model_name} (Acc: {run.val_accuracy?.toFixed(3)}) - {new Date(run.started_at).toLocaleString()}
            </option>
          ))}
        </select>

        <div className="ml-auto flex gap-2">
          <button onClick={handleExport} className="btn btn-secondary">
            Download Cleaned Dataset
          </button>
          <button onClick={handlePrune} className="btn btn-primary">
            Run Pruning Experiment
          </button>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="glass-panel p-4 mb-4 flex gap-4 items-center">
        <span className="text-sm font-medium text-secondary">Filters:</span>
        {Object.keys(filters).map(cat => (
          <label key={cat} className="flex items-center gap-2 text-sm cursor-pointer hover:text-primary transition-colors">
            <input 
              type="checkbox" 
              checked={filters[cat]} 
              onChange={() => toggleFilter(cat)}
              className="accent-accent-blue" 
            />
            <span className={`badge badge-${cat}`}>{cat.replace('_', ' ')}</span>
          </label>
        ))}
        {loading && <span className="ml-4 text-sm text-accent-blue animate-pulse">Loading data...</span>}
      </div>

      <div className="flex-1 flex gap-4 min-h-0">
        {/* Main Area: Scatter + Table */}
        <div className="flex-1 flex flex-col gap-4 min-w-0">
          <div className="h-2/3 relative">
            {loading ? (
              <div className="absolute inset-0 flex items-center justify-center glass-panel">Loading Plot...</div>
            ) : (
              <ScatterPlot data={filteredData} onPointClick={handlePointClick} />
            )}
          </div>
          <div className="h-1/3 overflow-hidden rounded-xl border border-glass">
            <div className="h-full overflow-y-auto custom-scrollbar bg-glass">
              <SampleTable samples={filteredData.slice(0, 100)} onRowClick={setSelectedSample} />
            </div>
          </div>
        </div>

        {/* Sidebar: Sample Details */}
        <div className="w-80 shrink-0">
          {selectedSample ? (
            <SampleCard 
              sample={selectedSample} 
              datasetId={selectedRun?.dataset_id}
              onClose={() => setSelectedSample(null)} 
            />
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
