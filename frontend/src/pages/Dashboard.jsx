import React, { useState, useEffect } from 'react';
import MetricCard from '../components/MetricCard';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { BarChartIcon, FolderIcon, ZapIcon, SearchIcon, RefreshIcon, AlertCircleIcon, TargetIcon, ActivityIcon, InboxIcon, DownloadIcon } from '../components/Icons';

const CATEGORY_COLORS = {
  high_value: '#10B981',
  normal: '#3B82F6',
  redundant: '#F59E0B',
  harmful: '#F43F5E',
  suspicious: '#8B5CF6',
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
  const [latestRunId, setLatestRunId] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const history = await api.getTrainingHistory().catch(() => []);
      setRuns(Array.isArray(history) ? history : []);

      // Load summary from the most recent completed run
      const completed = (Array.isArray(history) ? history : []).filter(r => r.status === 'completed');
      if (completed.length > 0) {
        const latestRun = completed[0];
        setLatestRunId(latestRun.id);
        const summ = await api.getValuationSummary(latestRun.id).catch(() => null);
        setSummary(summ);
      }
    } catch (e) {
      console.error('Failed to load dashboard data:', e);
    } finally {
      setLoading(false);
    }
  }

  const categories = summary?.category_counts || {};
  const total = summary?.total_samples || 0;
  const removalPct = summary?.recommended_removal_percentage || 0;

  const pieData = Object.entries(categories).map(([key, val]) => ({
    name: CATEGORY_LABELS[key] || key,
    value: val,
    color: CATEGORY_COLORS[key] || '#64748B',
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
    <div className="space-y-6">
      {/* Metric cards row */}
      <div className="grid grid-cols-1 gap-4" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
        <MetricCard title="Total Samples" value={total} icon={<BarChartIcon size={24} />} color="blue" />
        <MetricCard
          title="High Value"
          value={categories.high_value || 0}
          icon={<ActivityIcon size={24} />} color="emerald"
          subtitle={total ? `${Math.round(((categories.high_value || 0) / total) * 100)}% of dataset` : ''}
        />
        <MetricCard title="Redundant" value={categories.redundant || 0} icon={<RefreshIcon size={24} />} color="amber" />
        <MetricCard title="Harmful" value={categories.harmful || 0} icon={<AlertCircleIcon size={24} />} color="rose" trend="down" />
        <MetricCard title="Suspicious" value={categories.suspicious || 0} icon={<SearchIcon size={24} />} color="violet" />
      </div>

      <div className="grid grid-cols-1 gap-6" style={{ gridTemplateColumns: '1fr 2fr' }}>
        {/* Dataset Health donut */}
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
          <h3 className="text-lg font-semibold mb-4">Dataset Health</h3>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', position: 'relative' }}>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={pieData}
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                    stroke="none"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: 'var(--bg-surface)', borderColor: 'var(--border-glass)', borderRadius: '8px' }}
                    itemStyle={{ color: 'var(--text-primary)' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span className="text-muted">No valuation data yet</span>
              </div>
            )}
            {total > 0 && (
              <div className="absolute inset-0" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none' }}>
                <span className="text-2xl font-bold">{usablePct}%</span>
                <span className="text-xs text-muted">Usable Data</span>
              </div>
            )}
          </div>
          {/* Legend */}
          <div className="grid grid-cols-2 gap-2 text-xs mt-4">
            {pieData.map(d => (
              <div key={d.name} className="flex items-center gap-2">
                <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: d.color, flexShrink: 0 }} />
                <span className="text-muted">{d.name}</span>
              </div>
            ))}
          </div>
          {removalPct > 0 && (
            <div style={{ marginTop: 'var(--space-4)', padding: 'var(--space-3)', background: 'var(--cat-harmful-bg)', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-sm)' }}>
              <strong style={{ color: 'var(--accent-rose)' }}>Recommended removal:</strong>{' '}
              <span>{removalPct.toFixed(1)}% of dataset</span>
            </div>
          )}
        </div>

        {/* Quick Actions & Recent Runs */}
        <div className="glass-panel p-6" style={{ display: 'flex', flexDirection: 'column' }}>
          <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
          <div className="flex gap-4 mb-8">
            <button onClick={() => navigate('/datasets')} className="btn btn-primary" style={{ flex: 1, padding: 'var(--space-4)' }}>
              <FolderIcon size={16} /> Upload Dataset
            </button>
            <button onClick={() => navigate('/training')} className="btn btn-secondary" style={{ flex: 1, padding: 'var(--space-4)' }}>
              <ZapIcon size={16} /> Train Model
            </button>
            <button onClick={() => navigate('/explorer')} className="btn btn-secondary" style={{ flex: 1, padding: 'var(--space-4)' }}>
              <SearchIcon size={16} /> Explore Data
            </button>
            {latestRunId && (
              <button onClick={() => api.exportRefinedDataset(latestRunId)} className="btn btn-primary" style={{ flex: 1, padding: 'var(--space-4)', background: 'var(--accent-emerald)' }}>
                <DownloadIcon size={16} /> Download Refined Dataset
              </button>
            )}
          </div>

          <h3 className="text-lg font-semibold mb-4">Recent Runs</h3>
          <div className="table-container" style={{ flex: 1 }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Run ID</th>
                  <th>Model</th>
                  <th>Status</th>
                  <th>Accuracy</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {runs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center text-muted" style={{ padding: 'var(--space-8)' }}>
                      No training runs yet. Start by uploading a dataset.
                    </td>
                  </tr>
                ) : (
                  runs.slice(0, 5).map(run => (
                    <tr key={run.id}>
                      <td className="font-mono text-accent-blue" style={{ fontSize: 'var(--font-xs)' }}>
                        {run.id?.slice(0, 8)}…
                      </td>
                      <td>{run.model_name || '—'}</td>
                      <td>
                        <span className={`badge badge-${run.status === 'completed' ? 'high_value' : run.status === 'failed' ? 'harmful' : 'normal'}`}>
                          {run.status}
                        </span>
                      </td>
                      <td className="font-mono font-medium">
                        {run.val_accuracy ? `${(run.val_accuracy * 100).toFixed(1)}%` : '—'}
                      </td>
                      <td className="text-muted text-sm">
                        {run.started_at ? new Date(run.started_at).toLocaleDateString() : '—'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
