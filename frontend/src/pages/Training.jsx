import React, { useState } from 'react';
import ProgressBar from '../components/ProgressBar';
import { api, useTrainingSocket } from '../api/client';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { RocketIcon, StopIcon } from '../components/Icons';

export default function Training() {
  const [status, setStatus] = useState('idle'); // idle, training, completed
  const [config, setConfig] = useState({ dataset_id: '', model_name: 'simple_cnn', epochs: 20, learning_rate: 0.01 });
  const [datasets, setDatasets] = useState([]);
  const [runId, setRunId] = useState(null);
  
  const [history, setHistory] = useState([]);
  const [progress, setProgress] = useState(0);
  const [metrics, setMetrics] = useState({ loss: null, acc: null, epoch: 0 });

  // Load datasets on mount
  React.useEffect(() => {
    api.listDatasets().then(ds => {
      setDatasets(ds || []);
      if (ds?.length > 0 && !config.dataset_id) {
        setConfig(prev => ({ ...prev, dataset_id: ds[0].id }));
      }
    }).catch(() => {});
  }, []);

  useTrainingSocket((msg) => {
    if (msg.status === 'training') {
      setStatus('training');
      setProgress(msg.progress || 0);
      setMetrics({ loss: msg.train_loss, acc: msg.val_accuracy, epoch: msg.epoch });
      setHistory(prev => [...prev, { epoch: msg.epoch, loss: msg.train_loss, accuracy: msg.val_accuracy }]);
    } else if (msg.status === 'completed') {
      setStatus('completed');
      setProgress(100);
    } else if (msg.status === 'failed') {
      setStatus('idle');
    }
  });

  const handleStart = async () => {
    setStatus('training');
    setHistory([]);
    setProgress(0);
    try {
      const res = await api.startTraining(config);
      setRunId(res.run_id || res.runId);
    } catch (e) {
      setStatus('idle');
    }
  };

  const handleStop = async () => {
    if (runId) await api.stopTraining(runId);
    setStatus('idle');
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Config Panel */}
        <div className="glass-card lg:col-span-1">
          <h3 className="text-lg font-semibold mb-4 border-b border-glass pb-2">Training Configuration</h3>
          
          <div className="space-y-4">
            <div className="input-group">
              <label className="input-label">Dataset</label>
              <select 
                className="input-field" 
                value={config.dataset_id}
                onChange={e => setConfig({...config, dataset_id: e.target.value})}
                disabled={status === 'training'}
              >
                <option value="">Select a dataset...</option>
                {datasets.map(ds => (
                  <option key={ds.id} value={ds.id}>{ds.name} ({ds.num_samples} samples)</option>
                ))}
              </select>
            </div>
            
            <div className="input-group">
              <label className="input-label">Model Architecture</label>
              <select 
                className="input-field"
                value={config.model_name}
                onChange={e => setConfig({...config, model_name: e.target.value})}
                disabled={status === 'training'}
              >
                <option value="simple_cnn">Simple CNN</option>
                <option value="resnet18">ResNet-18</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="input-group">
                <label className="input-label">Epochs</label>
                <input 
                  type="number" 
                  className="input-field" 
                  value={config.epochs}
                  min={1} max={200}
                  onChange={e => setConfig({...config, epochs: parseInt(e.target.value) || 20})}
                  disabled={status === 'training'}
                />
              </div>
              <div className="input-group">
                <label className="input-label">Learning Rate</label>
                <input 
                  type="number" 
                  step="0.001"
                  className="input-field" 
                  value={config.learning_rate}
                  onChange={e => setConfig({...config, learning_rate: parseFloat(e.target.value) || 0.01})}
                  disabled={status === 'training'}
                />
              </div>
            </div>

            <div className="pt-4 border-t border-glass">
              {status === 'idle' || status === 'completed' ? (
                <button className="btn btn-primary w-full py-3 text-base" onClick={handleStart}>
                  <RocketIcon size={16} /> Start Training & Valuation
                </button>
              ) : (
                <button className="btn btn-danger w-full py-3 text-base" onClick={handleStop}>
                  <StopIcon size={16} /> Stop Training
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Status & Charts */}
        <div className="lg:col-span-2 space-y-6">
          {(status === 'training' || status === 'completed') && (
            <ProgressBar 
              progress={progress} 
              epoch={metrics.epoch} 
              totalEpochs={config.epochs}
              loss={metrics.loss}
              accuracy={metrics.acc}
              eta={status === 'training' ? '5m 30s' : 'Done'}
            />
          )}

          <div className="glass-panel p-5 h-80 flex flex-col relative">
            {status === 'idle' && history.length === 0 && (
              <div className="absolute inset-0 flex items-center justify-center text-muted z-10 bg-base/50 backdrop-blur-sm rounded-lg">
                Start training to view live metrics
              </div>
            )}
            <h3 className="text-sm font-medium text-secondary uppercase mb-4">Live Metrics</h3>
            <div className="flex-1 w-full min-h-0">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={history} margin={{ top: 5, right: 20, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
                  <XAxis dataKey="epoch" stroke="#64748B" fontSize={12} tickLine={false} />
                  <YAxis yAxisId="left" stroke="#64748B" fontSize={12} tickLine={false} domain={[0, 'auto']} />
                  <YAxis yAxisId="right" orientation="right" stroke="#10B981" fontSize={12} tickLine={false} domain={[0, 1]} />
                  <Tooltip contentStyle={{ backgroundColor: 'var(--bg-surface)', borderColor: 'var(--border-glass)' }} />
                  <Line yAxisId="left" type="monotone" dataKey="loss" stroke="#3B82F6" strokeWidth={2} dot={false} isAnimationActive={false} />
                  <Line yAxisId="right" type="monotone" dataKey="accuracy" stroke="#10B981" strokeWidth={2} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
