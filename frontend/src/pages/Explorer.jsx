import React, { useState, useEffect, useMemo, useCallback } from 'react';
import ScatterPlot from '../components/ScatterPlot';
import SampleTable from '../components/SampleTable';
import SampleCard from '../components/SampleCard';
import WeightSliders from '../components/WeightSliders';
import BatchToolbar from '../components/BatchToolbar';
import { CursorClickIcon } from '../components/Icons';
import { api } from '../api/client';
import { useToast } from '../components/Toast';

export default function Explorer() {
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedSample, setSelectedSample] = useState(null);
  const [selectedIndices, setSelectedIndices] = useState(new Set());
  const [weightsLoading, setWeightsLoading] = useState(false);
  const { addToast } = useToast();
  
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
    }).catch(() => addToast('Failed to load training runs', 'error'));
  }, []);

  // Fetch valuations when run changes
  useEffect(() => {
    if (selectedRun) {
      setLoading(true);
      setSelectedSample(null);
      api.getValuationSamples(selectedRun.id, { per_page: 2000 })
        .then(res => setData(res.samples || []))
        .catch(() => addToast('Failed to load valuation data', 'error'))
        .finally(() => setLoading(false));
    }
  }, [selectedRun]);

  const handlePointClick = useCallback((index) => {
    const sample = data.find(d => (d.sample_index ?? d.index) === index);
    if (sample) setSelectedSample(sample);
  }, [data]);

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
      addToast('Pruning experiment started! Check the Experiments page.', 'success');
    } catch (e) {
      addToast('Failed to start experiment: ' + e.message, 'error');
    }
  };

  const handleExport = () => {
    if (selectedRun) {
      api.exportRefinedDataset(selectedRun.id);
    }
  };

  const handleApplyWeights = async (weights) => {
    if (!selectedRun) return;
    setWeightsLoading(true);
    try {
      await api.recomputeScores(selectedRun.id, weights);
      addToast('Scores recomputed successfully', 'success');
      // Re-fetch data
      const res = await api.getValuationSamples(selectedRun.id, { per_page: 2000 });
      setData(res.samples || []);
    } catch (e) {
      addToast('Failed to recompute scores: ' + e.message, 'error');
    } finally {
      setWeightsLoading(false);
    }
  };

  const handleBatchExport = () => {
    const toExport = data.filter(d => selectedIndices.has(d.sample_index ?? d.index));
    const csvContent = "data:text/csv;charset=utf-8," 
      + "sample_index,category,unified_score\n"
      + toExport.map(e => `${e.sample_index ?? e.index},${e.category},${e.unified_score}`).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "batch_export.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleBatchUpdateCategory = async (category) => {
    if (!selectedRun) return;
    try {
      await api.batchUpdateCategory(selectedRun.id, [...selectedIndices], category);
      addToast(`Marked ${selectedIndices.size} samples as ${category}`, 'success');
      // Re-fetch data
      const res = await api.getValuationSamples(selectedRun.id, { per_page: 2000 });
      setData(res.samples || []);
      setSelectedIndices(new Set());
    } catch (e) {
      addToast('Failed to update categories: ' + e.message, 'error');
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

      <WeightSliders onApply={handleApplyWeights} loading={weightsLoading} />

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

      <div className="flex-1 flex flex-col gap-4 min-h-0">
        {/* Top Area: Scatter + Sidebar */}
        <div className="flex-1 flex gap-4 min-h-0">
          <div className="flex-1 relative min-w-0">
            {loading ? (
              <div className="absolute inset-0 flex items-center justify-center glass-panel">Loading Plot...</div>
            ) : (
              <ScatterPlot key={JSON.stringify(filters)} data={filteredData} onPointClick={handlePointClick} />
            )}
          </div>
          
          {/* Sidebar: Sample Details */}
          {selectedSample && (
            <div className="shrink-0" style={{ width: '400px' }}>
              <SampleCard 
                sample={selectedSample} 
                datasetId={selectedRun?.dataset_id}
                onClose={() => setSelectedSample(null)} 
              />
            </div>
          )}
        </div>

        {/* Bottom Area: Table */}
        <div className="h-1/3 min-h-[250px] overflow-hidden rounded-xl border border-glass shrink-0">
          <div className="h-full overflow-y-auto custom-scrollbar bg-glass">
            <SampleTable 
              samples={filteredData.slice(0, 100)} 
              onRowClick={setSelectedSample} 
              selectable={true}
              selectedIndices={selectedIndices}
              onSelectionChange={setSelectedIndices}
            />
          </div>
        </div>
      </div>
      
      <BatchToolbar 
        visible={selectedIndices.size > 0} 
        selectedCount={selectedIndices.size}
        onExport={handleBatchExport}
        onMarkCategory={handleBatchUpdateCategory}
        onDeselectAll={() => setSelectedIndices(new Set())}
      />
    </div>
  );
}
