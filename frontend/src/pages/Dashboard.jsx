import React, { useState, useEffect } from 'react';
import MetricCard from '../components/MetricCard';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { BarChartIcon, FolderIcon, ZapIcon, SearchIcon, RefreshIcon, AlertCircleIcon, TargetIcon, ActivityIcon, InboxIcon, DownloadIcon, LayersIcon } from '../components/Icons';

const CATEGORY_COLORS = {
  high_value: '#34d399',
  normal: '#007BFF',
  redundant: '#fbbf24',
  harmful: '#fb7185',
  suspicious: '#a78bfa',
};

const CATEGORY_LABELS = {
  high_value: 'High Value',
  normal: 'Normal',
  redundant: 'Redundant',
  harmful: 'Harmful',
  suspicious: 'Suspicious',
};

export default function Dashboard() {
  const navigate = useNavigate();
  const [runs, setRuns] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedRunId, setSelectedRunId] = useState('');
  const [completedRuns, setCompletedRuns] = useState([]);
  const [runSummaries, setRunSummaries] = useState([]);

  useEffect(() => {
    loadHistory();
    api.getAllRunSummaries().then(data => setRunSummaries(Array.isArray(data) ? data : [])).catch(console.error);
  }, []);

  async function loadHistory() {
    setLoading(true);
    try {
      const history = await api.getTrainingHistory().catch(() => []);
      setRuns(Array.isArray(history) ? history : []);

      const completed = (Array.isArray(history) ? history : []).filter(r => r.status === 'completed');
      setCompletedRuns(completed);
      if (completed.length > 0) {
        setSelectedRunId(completed[0].id);
      } else {
        setLoading(false);
      }
    } catch (e) {
      console.error('Failed to load dashboard data:', e);
      setLoading(false);
    }
  }

  useEffect(() => {
    if (selectedRunId) {
      setLoading(true);
      api.getValuationSummary(selectedRunId)
        .then(summ => setSummary(summ))
        .catch(() => setSummary(null))
        .finally(() => setLoading(false));
    }
  }, [selectedRunId]);

  const categories = summary?.category_counts || {};
  const total = summary?.total_samples || 0;
  const removalPct = summary?.recommended_removal_percentage || 0;

  const pieData = Object.entries(categories).map(([key, val]) => ({
    name: CATEGORY_LABELS[key] || key,
    value: val,
    color: CATEGORY_COLORS[key] || '#5a5a5a',
  }));

  const usablePct = total > 0
    ? Math.round(((total - (categories.harmful || 0) - (categories.redundant || 0)) / total) * 100)
    : 0;

  // Empty state when no data
  if (!loading && !summary && runs.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon"><BarChartIcon size={48} /></div>
        <h2 style={{ fontSize: 'var(--font-2xl)', marginBottom: 'var(--space-2)' }}>Welcome to DataValuator</h2>
        <p style={{ maxWidth: 480, marginBottom: 'var(--space-6)' }}>
          Upload a dataset and train a model to start discovering which training samples
          actually matter to your model's performance.
        </p>
        <div className="flex gap-4">
          <button className="btn btn-primary py-3 px-6" onClick={() => navigate('/datasets')}>
            <FolderIcon size={16} /> Upload Dataset
          </button>
          <button className="btn btn-secondary py-3 px-6" onClick={() => navigate('/training')}>
            <ZapIcon size={16} /> Start Training
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 h-[calc(100vh-8rem)] min-h-0">
      {/* Header & Run Selector */}
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-6">
          <h2 className="text-xl font-semibold">Overview</h2>
          
          <div className="flex gap-2">
            <button onClick={() => navigate('/datasets')} className="btn btn-secondary px-3 py-1.5 text-xs font-medium">
              <FolderIcon size={14} /> Upload Data
            </button>
            <button onClick={() => navigate('/training')} className="btn btn-secondary px-3 py-1.5 text-xs font-medium">
              <ZapIcon size={14} /> Train
            </button>
            <button onClick={() => navigate('/explorer')} className="btn btn-secondary px-3 py-1.5 text-xs font-medium">
              <SearchIcon size={14} /> Explore
            </button>
            {selectedRunId && (
              <button onClick={() => api.exportRefinedDataset(selectedRunId)} className="btn btn-primary px-3 py-1.5 text-xs font-medium bg-accent-emerald text-black border-transparent hover:bg-white hover:text-black hover:border-transparent">
                <DownloadIcon size={14} /> Export Cleaned
              </button>
            )}
          </div>
        </div>

        <select 
          className="input-field max-w-xs text-sm py-1.5 px-3"
          value={selectedRunId}
          onChange={(e) => setSelectedRunId(e.target.value)}
        >
          {completedRuns.map(r => (
            <option key={r.id} value={r.id}>
              {r.model_name} (Acc: {r.val_accuracy?.toFixed(3)}) - {new Date(r.started_at).toLocaleString()}
            </option>
          ))}
        </select>
      </div>

      {/* Metric cards row */}
      <div className="grid gap-4 shrink-0" style={{ gridTemplateColumns: 'repeat(5, minmax(0, 1fr))' }}>
        <MetricCard title="Total Samples" value={total} icon={<BarChartIcon size={20} />} color="blue" />
        <MetricCard
          title="High Value"
          value={categories.high_value || 0}
          icon={<ActivityIcon size={20} />} color="emerald"
          subtitle={total ? `${Math.round(((categories.high_value || 0) / total) * 100)}% of dataset` : ''}
        />
        <MetricCard title="Redundant" value={categories.redundant || 0} icon={<RefreshIcon size={20} />} color="amber" />
        <MetricCard title="Harmful" value={categories.harmful || 0} icon={<AlertCircleIcon size={20} />} color="rose" trend="down" />
        <MetricCard title="Suspicious" value={categories.suspicious || 0} icon={<SearchIcon size={20} />} color="violet" />
      </div>

      <div className="grid gap-4 flex-1 min-h-0" style={{ gridTemplateColumns: '1fr 2fr' }}>
        {/* Dataset Health donut */}
        <div className="glass-card flex flex-col col-span-1 h-full overflow-hidden p-4">
          <h3 className="text-md font-semibold mb-2 shrink-0">Dataset Health</h3>
          <div className="flex-1 relative flex flex-col justify-center items-center" style={{ minHeight: '200px' }}>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    innerRadius={50}
                    outerRadius={70}
                    paddingAngle={5}
                    dataKey="value"
                    stroke="none"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: 'var(--bg-surface)', borderColor: 'var(--border-glass)', borderRadius: '8px', fontSize: '12px' }}
                    itemStyle={{ color: 'var(--text-primary)' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center">
                <span className="text-muted text-sm">No data yet</span>
              </div>
            )}
            {total > 0 && (
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-xl font-bold">{usablePct}%</span>
                <span className="text-[10px] text-muted uppercase tracking-wider">Usable</span>
              </div>
            )}
          </div>
          {/* Legend */}
          <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[10px] mt-2 shrink-0">
            {pieData.map(d => (
              <div key={d.name} className="flex items-center gap-1.5">
                <div style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: d.color, flexShrink: 0 }} />
                <span className="text-muted truncate" title={d.name}>{d.name}</span>
              </div>
            ))}
          </div>
          {removalPct > 0 && (
            <div className="mt-3 p-2 bg-rose-500/10 border border-rose-500/20 rounded-md text-xs shrink-0 flex items-center gap-2">
              <AlertCircleIcon size={14} className="text-accent-rose shrink-0" />
              <div>
                <strong className="text-accent-rose font-medium block">Recommended removal:</strong>
                <span className="text-muted">{removalPct.toFixed(1)}% of dataset</span>
              </div>
            </div>
          )}
        </div>

        {/* Model Leaderboard */}
        <div className="glass-panel flex flex-col col-span-2 h-full overflow-hidden p-4">
          <h3 className="text-md font-semibold mb-3 shrink-0 flex items-center gap-2">
            <LayersIcon size={16} /> Model Leaderboard
          </h3>
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            <table className="table w-full text-sm">
              <thead className="sticky top-0 bg-dark z-10 shadow-sm">
                <tr>
                  <th className="py-2">Model</th>
                  <th className="py-2">Accuracy</th>
                  <th className="py-2">Epochs</th>
                  <th className="py-2">High Value</th>
                  <th className="py-2">Harmful</th>
                  <th className="py-2 text-right">Date</th>
                </tr>
              </thead>
              <tbody>
                {[...runSummaries].sort((a, b) => (b.val_accuracy || 0) - (a.val_accuracy || 0)).map(run => (
                  <tr 
                    key={run.id || run.run_id} 
                    onClick={() => setSelectedRunId(run.id || run.run_id)} 
                    style={{ cursor: 'pointer' }} 
                    className={`hover:bg-white/5 transition-colors ${selectedRunId === (run.id || run.run_id) ? 'bg-white/10' : ''}`}
                  >
                    <td className="font-medium text-secondary truncate max-w-[100px]" title={run.model_name}>{run.model_name || '—'}</td>
                    <td>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-medium text-accent-blue w-12 shrink-0">{run.val_accuracy ? `${(run.val_accuracy * 100).toFixed(1)}%` : '—'}</span>
                        <div className="flex-1 bg-black/40 rounded-full h-1 w-16 overflow-hidden min-w-[40px]">
                          <div className="h-full bg-accent-blue" style={{ width: run.val_accuracy ? `${run.val_accuracy * 100}%` : '0%' }} />
                        </div>
                      </div>
                    </td>
                    <td className="font-mono text-muted">{run.hyperparameters?.epochs || '—'}</td>
                    <td className="font-mono text-emerald-400/80">{run.category_counts?.high_value ? `${((run.category_counts.high_value / run.total_samples) * 100).toFixed(1)}%` : '—'}</td>
                    <td className="font-mono text-rose-400/80">{run.category_counts?.harmful ? `${((run.category_counts.harmful / run.total_samples) * 100).toFixed(1)}%` : '—'}</td>
                    <td className="text-muted text-xs text-right whitespace-nowrap">{run.started_at ? new Date(run.started_at).toLocaleDateString() : '—'}</td>
                  </tr>
                ))}
                {runSummaries.length === 0 && (
                  <tr>
                    <td colSpan={6} className="text-center text-muted py-8">No models trained yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
