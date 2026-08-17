import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { BarChartIcon, ActivityIcon, SearchIcon, LayersIcon, RefreshIcon } from '../components/Icons';

const CATEGORY_COLORS = {
  high_value: 'var(--accent-emerald, #34d399)',
  normal: 'var(--accent-blue, #2dd4bf)',
  redundant: 'var(--accent-amber, #fbbf24)',
  harmful: 'var(--accent-rose, #fb7185)',
  suspicious: 'var(--accent-violet, #a78bfa)',
};

const CATEGORY_LABELS = {
  high_value: 'High Value',
  normal: 'Normal',
  redundant: 'Redundant',
  harmful: 'Harmful',
  suspicious: 'Suspicious',
};

export default function Compare() {
  const [runs, setRuns] = useState([]);
  const [runA, setRunA] = useState('');
  const [runB, setRunB] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);

  useEffect(() => {
    api.getTrainingHistory()
      .then(data => {
        const completed = (Array.isArray(data) ? data : []).filter(r => r.status === 'completed');
        setRuns(completed);
        if (completed.length > 1) {
          setRunA(completed[0].id);
          setRunB(completed[1].id);
        } else if (completed.length === 1) {
          setRunA(completed[0].id);
        }
      })
      .catch(console.error);
  }, []);

  const handleCompare = async () => {
    if (!runA || !runB) return;
    setLoading(true);
    try {
      const data = await api.compareRuns(runA, runB);
      setResults(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const renderStackedBar = (summary) => {
    if (!summary || !summary.category_counts) return null;
    const total = summary.total || Object.values(summary.category_counts).reduce((a, b) => a + b, 0);
    if (!total) return null;

    return (
      <div className="w-full h-4 rounded-full overflow-hidden flex bg-dark/50 mt-2">
        {Object.entries(summary.category_counts).map(([cat, count]) => {
          if (!count) return null;
          const pct = (count / total) * 100;
          return (
            <div 
              key={cat} 
              style={{ width: `${pct}%`, backgroundColor: CATEGORY_COLORS[cat] || '#5a5a5a' }} 
              title={`${CATEGORY_LABELS[cat] || cat}: ${count}`}
            />
          );
        })}
      </div>
    );
  };

  if (runs.length < 2) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon"><LayersIcon size={48} /></div>
        <h2 style={{ fontSize: 'var(--font-2xl)', marginBottom: 'var(--space-2)' }}>Not enough runs</h2>
        <p style={{ maxWidth: 480, marginBottom: 'var(--space-6)' }}>
          You need at least two completed training runs to compare them.
        </p>
      </div>
    );
  }

  const runAObj = runs.find(r => r.id === runA);
  const runBObj = runs.find(r => r.id === runB);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 bg-dark/20 p-4 rounded-md border border-white/5">
        <div className="flex-1">
          <label className="block text-sm text-muted mb-1">Run A (Baseline)</label>
          <select 
            className="w-full bg-dark/50 border border-white/10 rounded-md px-3 py-2 text-white outline-none"
            value={runA}
            onChange={(e) => setRunA(e.target.value)}
          >
            {runs.map(r => (
              <option key={r.id} value={r.id}>
                {r.model_name} ({new Date(r.started_at).toLocaleDateString()})
              </option>
            ))}
          </select>
        </div>
        <div className="flex-1">
          <label className="block text-sm text-muted mb-1">Run B (Comparison)</label>
          <select 
            className="w-full bg-dark/50 border border-white/10 rounded-md px-3 py-2 text-white outline-none"
            value={runB}
            onChange={(e) => setRunB(e.target.value)}
          >
            {runs.map(r => (
              <option key={r.id} value={r.id}>
                {r.model_name} ({new Date(r.started_at).toLocaleDateString()})
              </option>
            ))}
          </select>
        </div>
        <div className="mt-6">
          <button 
            className="btn btn-primary px-6" 
            onClick={handleCompare} 
            disabled={loading || runA === runB}
          >
            {loading ? 'Comparing...' : 'Compare Runs'}
          </button>
        </div>
      </div>

      {results && (
        <div className="animate-fade-in space-y-6">
          {/* Side-by-side Summaries */}
          <div className="grid grid-cols-2 gap-6">
            <div className="glass-panel p-6">
              <h3 className="text-xl font-semibold mb-1">{runAObj?.model_name || 'Run A'}</h3>
              <div className="text-sm text-muted mb-4">Total Samples: {results.run_a_summary?.total}</div>
              {renderStackedBar(results.run_a_summary)}
              <div className="flex gap-2 flex-wrap mt-4">
                {Object.entries(results.run_a_summary?.category_counts || {}).map(([cat, count]) => (
                  <div key={cat} className="text-xs flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: CATEGORY_COLORS[cat] }} />
                    {CATEGORY_LABELS[cat]}: {count}
                  </div>
                ))}
              </div>
            </div>
            
            <div className="glass-panel p-6">
              <h3 className="text-xl font-semibold mb-1">{runBObj?.model_name || 'Run B'}</h3>
              <div className="text-sm text-muted mb-4">Total Samples: {results.run_b_summary?.total}</div>
              {renderStackedBar(results.run_b_summary)}
              <div className="flex gap-2 flex-wrap mt-4">
                {Object.entries(results.run_b_summary?.category_counts || {}).map(([cat, count]) => (
                  <div key={cat} className="text-xs flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: CATEGORY_COLORS[cat] }} />
                    {CATEGORY_LABELS[cat]}: {count}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Delta Section */}
          <div className="glass-card">
            <h3 className="text-lg font-semibold mb-4">Comparison Insights</h3>
            
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="p-4 bg-dark/30 rounded-md">
                <div className="text-sm text-muted">Accuracy Difference</div>
                {(() => {
                  const accA = runAObj?.val_accuracy || 0;
                  const accB = runBObj?.val_accuracy || 0;
                  const diff = accB - accA;
                  const color = diff > 0 ? 'text-accent-emerald' : diff < 0 ? 'text-accent-rose' : 'text-white';
                  return (
                    <div className={`text-2xl font-mono font-medium ${color}`}>
                      {diff > 0 ? '+' : ''}{(diff * 100).toFixed(2)}%
                    </div>
                  );
                })()}
              </div>
              <div className="p-4 bg-dark/30 rounded-md">
                <div className="text-sm text-muted">Category Overlap</div>
                <div className="text-2xl font-mono font-medium text-accent-blue">
                  {results.total_samples ? ((results.overlap_count / results.total_samples) * 100).toFixed(1) : 0}%
                </div>
              </div>
              <div className="p-4 bg-dark/30 rounded-md">
                <div className="text-sm text-muted">Changed Categories</div>
                <div className="text-2xl font-mono font-medium">
                  {results.total_changes} samples
                </div>
              </div>
            </div>

            {results.category_changes && results.category_changes.length > 0 && (
              <>
                <h4 className="text-md font-medium mb-2">Sample Changes (Max 100)</h4>
                <div className="table-container max-h-96 overflow-y-auto">
                  <table className="table">
                    <thead className="sticky top-0 bg-bg-surface z-10">
                      <tr>
                        <th>Sample Index</th>
                        <th>From Category (A)</th>
                        <th>To Category (B)</th>
                        <th>Score A</th>
                        <th>Score B</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.category_changes.map((change, i) => (
                        <tr key={`${change.sample_index}-${i}`}>
                          <td className="font-mono">{change.sample_index}</td>
                          <td>
                            <span className="badge" style={{ backgroundColor: CATEGORY_COLORS[change.from_category] + '33', color: CATEGORY_COLORS[change.from_category] }}>
                              {CATEGORY_LABELS[change.from_category] || change.from_category}
                            </span>
                          </td>
                          <td>
                            <span className="badge" style={{ backgroundColor: CATEGORY_COLORS[change.to_category] + '33', color: CATEGORY_COLORS[change.to_category] }}>
                              {CATEGORY_LABELS[change.to_category] || change.to_category}
                            </span>
                          </td>
                          <td className="font-mono">{change.score_a?.toFixed(3)}</td>
                          <td className="font-mono">{change.score_b?.toFixed(3)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
