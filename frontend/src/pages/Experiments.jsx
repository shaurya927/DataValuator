import React, { useState } from 'react';
import ComparisonChart from '../components/ComparisonChart';
import MetricCard from '../components/MetricCard';
import { api } from '../api/client';
import { ScissorsIcon, TagIcon, BarChartIcon, RocketIcon, ClockIcon, DownloadIcon } from '../components/Icons';

export default function Experiments() {
  const [prunePercent, setPrunePercent] = useState(20);
  
  // Mock data for the chart
  const comparisonData = Array.from({ length: 20 }).map((_, i) => ({
    epoch: i + 1,
    original: 10 + Math.log(i + 1) * 25 + Math.random() * 2,
    pruned: 10 + Math.log(i + 1) * 26 + Math.random() * 1.5, // Slightly better
  }));

  return (
    <div className="space-y-6">
      
      {/* Launchers */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-card">
          <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
            <ScissorsIcon size={18} /> Data Pruning
          </h3>
          <p className="text-sm text-muted mb-4">Remove harmful and redundant samples to improve training speed and potentially accuracy.</p>
          
          <div className="mb-6">
            <div className="flex justify-between text-sm mb-2">
              <label className="text-secondary">Prune Percentage</label>
              <span className="font-mono text-accent-blue">{prunePercent}%</span>
            </div>
            <input 
              type="range" 
              min="5" max="50" step="5"
              value={prunePercent}
              onChange={(e) => setPrunePercent(e.target.value)}
              className="w-full accent-accent-blue"
            />
            <div className="flex justify-between text-xs text-muted mt-1">
              <span>Removes ~{(50000 * prunePercent / 100).toLocaleString()} samples</span>
            </div>
          </div>
          
          <button className="btn btn-primary w-full">Run Pruning Experiment</button>
        </div>

        <div className="glass-card">
          <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
            <TagIcon size={18} /> Label Corruption
          </h3>
          <p className="text-sm text-muted mb-4">Test the valuation robustness by artificially corrupting labels and checking detection rates.</p>
          
          <div className="mb-6">
            <div className="flex justify-between text-sm mb-2">
              <label className="text-secondary">Noise Level</label>
              <span className="font-mono text-accent-rose">10%</span>
            </div>
            <input 
              type="range" 
              min="5" max="30" step="5"
              defaultValue="10"
              className="w-full accent-accent-rose"
            />
          </div>
          
          <button className="btn btn-secondary w-full hover:bg-accent-rose hover:text-white hover:border-transparent">
            Run Noise Experiment
          </button>
        </div>
      </div>

      {/* Results Section */}
      <h2 className="text-xl font-semibold mt-8 mb-4">Latest Results: Pruning ({prunePercent}%)</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1 flex flex-col gap-4">
          <MetricCard title="Original Accuracy" value={92.4} subtitle="50k samples" icon={<BarChartIcon size={24} />} />
          <MetricCard title="Pruned Accuracy" value={93.1} subtitle="40k samples" icon={<RocketIcon size={24} />} trend="up" color="emerald" />
          <MetricCard title="Training Time" value="-20%" subtitle="Faster convergence" icon={<ClockIcon size={24} />} color="amber" />
        </div>
        
        <div className="lg:col-span-3">
          <ComparisonChart data={comparisonData} />
          <div style={{ marginTop: 16, display: 'flex', gap: 12 }}>
            <button
              onClick={() => api.exportRefinedDataset('latest')}
              className="btn btn-primary"
              style={{ background: 'var(--accent-emerald)' }}
            >
              <DownloadIcon size={16} /> Download Refined Dataset
            </button>
            <button
              onClick={() => api.exportValuations('latest')}
              className="btn btn-secondary"
            >
              <DownloadIcon size={16} /> Export All Scores
            </button>
          </div>
        </div>
      </div>
      
    </div>
  );
}
