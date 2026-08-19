import React, { useState, useEffect } from 'react';
import ProgressBar from '../components/ProgressBar';
import { api, useTrainingSocket } from '../api/client';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { RocketIcon, StopIcon, DatabaseIcon, ChevronLeftIcon, DownloadIcon } from '../components/Icons';
import { useToast } from '../components/Toast';

export default function Training() {
  const [status, setStatus] = useState('idle'); // idle, training, completed
    const [config, setConfig] = useState({ dataset_id: '', model_name: 'simple_cnn', task_type: 'classification', epochs: 20, learning_rate: 0.01 });

    // ... (Keep existing states) ...
    const [datasets, setDatasets] = useState([]);
    const [runId, setRunId] = useState(null);
    const [history, setHistory] = useState([]);
    const [progress, setProgress] = useState(0);
    const [metrics, setMetrics] = useState({ loss: null, acc: null, epoch: 0 });
    const { addToast } = useToast();

    const [tabularAnalysis, setTabularAnalysis] = useState(null);
    const [loadingAnalysis, setLoadingAnalysis] = useState(false);
    const [prepConfig, setPrepConfig] = useState({
      imputation_strategy: 'mean',
      categorical_encoding: 'onehot',
      scaling: 'standard',
      transformation: 'none',
      outlier_detection: 'none',
      outlier_treatment: 'none',
      feature_selection: 'none',
      imbalance_strategy: 'none',
      duplicate_handling: 'keep',
      split_strategy: 'random',
      test_size: 0.2,
      random_seed: 42,
      drop_columns: '',
      target_column: ''
    });
    const [showPrepOptions, setShowPrepOptions] = useState(false);
    const [isDownloading, setIsDownloading] = useState(false);

    // Load datasets and check running status on mount
    useEffect(() => {
      api.listDatasets().then(ds => {
        setDatasets(ds || []);
        if (ds?.length > 0 && !config.dataset_id) {
          setConfig(prev => ({ ...prev, dataset_id: ds[0].id }));
        }
      }).catch(() => addToast('Failed to load datasets', 'error'));

      api.getTrainingStatus().then(async (statusRes) => {
        if (statusRes && statusRes.status === 'running') {
          setStatus('training');
          setRunId(statusRes.id);
          try {
            const runDetails = await api.getTrainingRun(statusRes.id);
            if (runDetails) {
              setProgress(runDetails.current_epoch ? (runDetails.current_epoch / runDetails.epochs) * 100 : 0);
              setConfig(prev => ({
                ...prev,
                dataset_id: runDetails.dataset_id || prev.dataset_id,
                model_name: runDetails.model_name || prev.model_name,
                task_type: runDetails.task_type || prev.task_type,
                epochs: runDetails.epochs || prev.epochs,
                learning_rate: runDetails.learning_rate || prev.learning_rate
              }));
              setMetrics({
                loss: runDetails.train_loss,
                acc: runDetails.val_accuracy,
                epoch: runDetails.current_epoch
              });
            }
          } catch (e) {}
        }
      }).catch(() => {});
    }, []);

    const selectedDataset = datasets.find(d => d.id === config.dataset_id);
    const isTabular = selectedDataset?.type === 'csv';

    // Auto-switch models if switching dataset types
    useEffect(() => {
      if (isTabular && ['simple_cnn', 'resnet18'].includes(config.model_name)) {
        setConfig(prev => ({ ...prev, model_name: 'random_forest' }));
      } else if (!isTabular && !['simple_cnn', 'resnet18'].includes(config.model_name)) {
        setConfig(prev => ({ ...prev, model_name: 'simple_cnn', task_type: 'classification' }));
      }
    }, [isTabular, config.dataset_id]);

    useEffect(() => {
      if (config.dataset_id && isTabular) {
        setLoadingAnalysis(true);
        api.analyzeDataset(config.dataset_id)
          .then(data => {
            setTabularAnalysis(data);
            setPrepConfig(prev => ({...prev, target_column: selectedDataset.target_column || ''}));
          })
          .catch(() => setTabularAnalysis(null))
          .finally(() => setLoadingAnalysis(false));
      } else {
        setTabularAnalysis(null);
      }
    }, [config.dataset_id, isTabular]);

    useTrainingSocket((msg) => {
      if (msg.status === 'training') {
        setStatus('training');
        setProgress(msg.progress || 0);
        setMetrics({ loss: msg.train_loss, acc: msg.val_accuracy, epoch: msg.epoch });
        setHistory(prev => [...prev, { epoch: msg.epoch, loss: msg.train_loss, accuracy: msg.val_accuracy }]);
      } else if (msg.status === 'computing_valuations' || msg.status === 'storing_results') {
        setStatus(msg.status);
        setProgress(100);
      } else if (msg.status === 'completed') {
        setStatus('completed');
        setProgress(100);
        addToast('Training completed successfully!', 'success');
      } else if (msg.status === 'failed') {
        setStatus('idle');
        addToast('Training failed', 'error');
      }
    });

    const handleStart = async () => {
      setStatus('training');
      setHistory([]);
      setProgress(0);
      try {
        const payload = { ...config, preprocessing: prepConfig };
        const res = await api.startTraining(payload);
        setRunId(res.run_id || res.runId);
      } catch (e) {
        setStatus('idle');
        addToast('Failed to start training: ' + (e.message || 'Unknown error'), 'error');
      }
    };

    const handleStop = async () => {
      if (runId) await api.stopTraining(runId);
      setStatus('idle');
    };

    const handleDownloadPreprocessed = async () => {
      setIsDownloading(true);
      try {
        const options = {
          ...prepConfig,
          drop_columns: prepConfig.drop_columns ? prepConfig.drop_columns.split(',').map(s => s.trim()).filter(Boolean) : [],
          target_column: prepConfig.target_column || null
        };
        await api.downloadPreprocessedDataset(config.dataset_id, options);
        addToast('Download started successfully', 'success');
      } catch (e) {
        addToast('Failed to download preprocessed data', 'error');
      }
      setIsDownloading(false);
    };

    const isSklearn = ['logistic_regression', 'linear_regression', 'decision_tree', 'random_forest'].includes(config.model_name);

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

              {isTabular && (
                <div className="input-group">
                  <label className="input-label">Task Type</label>
                  <select 
                    className="input-field"
                    value={config.task_type}
                    onChange={e => {
                      const newType = e.target.value;
                      let newModel = config.model_name;
                      if (newType === 'regression' && config.model_name === 'logistic_regression') newModel = 'linear_regression';
                      if (newType === 'classification' && config.model_name === 'linear_regression') newModel = 'logistic_regression';
                      setConfig({...config, task_type: newType, model_name: newModel});
                    }}
                    disabled={status === 'training'}
                  >
                    <option value="classification">Classification</option>
                    <option value="regression">Regression</option>
                  </select>
                </div>
              )}
              
              <div className="input-group">
                <label className="input-label">Model Architecture</label>
                <select 
                  className="input-field"
                  value={config.model_name}
                  onChange={e => setConfig({...config, model_name: e.target.value})}
                  disabled={status === 'training'}
                >
                  {!isTabular && (
                    <>
                      <option value="simple_cnn">Simple CNN (PyTorch)</option>
                      <option value="resnet18">ResNet-18 (PyTorch)</option>
                    </>
                  )}
                  {isTabular && config.task_type === 'classification' && (
                    <>
                      <option value="logistic_regression">Logistic Regression (SKLearn)</option>
                      <option value="decision_tree">Decision Tree (SKLearn)</option>
                      <option value="random_forest">Random Forest (SKLearn)</option>

                      <option value="tabular">Simple Tabular Net (PyTorch)</option>
                    </>
                  )}
                  {isTabular && config.task_type === 'regression' && (
                    <>
                      <option value="linear_regression">Linear Regression (SKLearn)</option>
                      <option value="decision_tree">Decision Tree (SKLearn)</option>
                      <option value="random_forest">Random Forest (SKLearn)</option>

                      <option value="tabular">Simple Tabular Regressor (PyTorch)</option>
                    </>
                  )}
                </select>
              </div>

              {!isSklearn && (
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
              )}

            {/* Tabular Preprocessing block */}
            {isTabular && (
              <div className="border border-glass rounded-lg overflow-hidden my-4 bg-surface/30">
                <button 
                  className="w-full flex items-center justify-between p-3 bg-white/5 hover:bg-white/10 transition-colors"
                  onClick={() => setShowPrepOptions(!showPrepOptions)}
                >
                  <span className="font-semibold text-sm flex items-center gap-2">
                    <DatabaseIcon size={16} /> Data Analysis & Preprocessing
                  </span>
                  {showPrepOptions ? <ChevronLeftIcon size={16} style={{transform: 'rotate(-90deg)'}} /> : <ChevronLeftIcon size={16} style={{transform: 'rotate(180deg)'}} />}
                </button>
                
                {showPrepOptions && (
                  <div className="p-4 space-y-4 text-sm animate-fade-in border-t border-glass">
                    {loadingAnalysis ? (
                      <div className="text-muted text-center py-4">Analyzing dataset...</div>
                    ) : tabularAnalysis ? (
                      <>
                        <div className="text-xs bg-dark p-3 rounded mb-4 space-y-2">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <span className="text-muted block uppercase">Rows / Cols</span>
                              <span className="font-mono">{tabularAnalysis.total_rows.toLocaleString()} / {tabularAnalysis.total_columns}</span>
                            </div>
                            <div>
                              <span className="text-muted block uppercase">Missing Vals</span>
                              <span className={`font-mono ${tabularAnalysis.total_missing > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                                {tabularAnalysis.total_missing.toLocaleString()}
                              </span>
                            </div>
                            <div>
                              <span className="text-muted block uppercase">Numerical</span>
                              <span className="font-mono">{tabularAnalysis.num_numerical}</span>
                            </div>
                            <div>
                              <span className="text-muted block uppercase">Categorical</span>
                              <span className="font-mono">{tabularAnalysis.num_categorical}</span>
                            </div>
                          </div>
                          {tabularAnalysis.duplicate_rows > 0 && <div className="text-amber-400 font-medium pt-2 border-t border-glass mt-2">Duplicates found: {tabularAnalysis.duplicate_rows} rows</div>}
                          {tabularAnalysis.target_info?.imbalance_warning && <div className="text-amber-400 font-medium">Class Imbalance detected!</div>}
                        </div>

                        <div className="input-group">
                          <label className="input-label text-xs">Target Column</label>
                          <select className="input-field py-1 text-xs" value={prepConfig.target_column} onChange={e => setPrepConfig({...prepConfig, target_column: e.target.value})}>
                            <option value="">(None)</option>
                            {tabularAnalysis.columns.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
                          </select>
                        </div>

                        <div className="input-group">
                          <label className="input-label text-xs">Missing Values Imputation</label>
                          <select className="input-field py-1 text-xs" value={prepConfig.imputation_strategy} onChange={e => setPrepConfig({...prepConfig, imputation_strategy: e.target.value})}>
                            <option value="none">None</option>
                            <option value="drop">Drop Rows with Missing</option>
                            <option value="mean">Mean (Num) / Mode (Cat)</option>
                            <option value="median">Median (Num) / Mode (Cat)</option>
                            <option value="most_frequent">Most Frequent</option>
                            <option value="knn">KNN Imputer (Num) / Mode (Cat)</option>
                            <option value="constant">Constant (0 / "missing")</option>
                            <option value="ffill">Forward Fill</option>
                            <option value="bfill">Backward Fill</option>
                          </select>
                        </div>

                        <div className="input-group">
                          <label className="input-label text-xs">Categorical Encoding</label>
                          <select className="input-field py-1 text-xs" value={prepConfig.categorical_encoding} onChange={e => setPrepConfig({...prepConfig, categorical_encoding: e.target.value})}>
                            <option value="none">None</option>
                            <option value="onehot">One-Hot Encoding</option>
                            <option value="ordinal">Ordinal Encoding</option>
                            <option value="frequency">Frequency Encoding</option>
                            <option value="target">Target Encoding</option>
                          </select>
                        </div>
                        
                        <div className="input-group">
                          <label className="input-label text-xs">Scaling (Numerical)</label>
                          <select className="input-field py-1 text-xs" value={prepConfig.scaling} onChange={e => setPrepConfig({...prepConfig, scaling: e.target.value})}>
                            <option value="none">None</option>
                            <option value="standard">Standard Scaler (Z-score)</option>
                            <option value="minmax">MinMax Scaler</option>
                            <option value="robust">Robust Scaler</option>
                          </select>
                        </div>

                        <div className="input-group">
                          <label className="input-label text-xs">Feature Transformation</label>
                          <select className="input-field py-1 text-xs" value={prepConfig.transformation} onChange={e => setPrepConfig({...prepConfig, transformation: e.target.value})}>
                            <option value="none">None</option>
                            <option value="log1p">Log1p</option>
                            <option value="yeo-johnson">Yeo-Johnson</option>
                          </select>
                        </div>

                        <div className="input-group">
                          <label className="input-label text-xs">Outliers</label>
                          <div className="flex gap-2">
                            <select className="input-field py-1 text-xs flex-1" value={prepConfig.outlier_detection} onChange={e => setPrepConfig({...prepConfig, outlier_detection: e.target.value})}>
                              <option value="none">No Detection</option>
                              <option value="iqr">IQR Based</option>
                              <option value="zscore">Z-score Based</option>
                            </select>
                            <select className="input-field py-1 text-xs flex-1" value={prepConfig.outlier_treatment} onChange={e => setPrepConfig({...prepConfig, outlier_treatment: e.target.value})}>
                              <option value="none">No Treatment</option>
                              <option value="clip">Clip / Winsorize</option>
                              <option value="remove">Remove (Train only)</option>
                            </select>
                          </div>
                        </div>

                        <div className="input-group">
                          <label className="input-label text-xs">Feature Selection</label>
                          <select className="input-field py-1 text-xs" value={prepConfig.feature_selection} onChange={e => setPrepConfig({...prepConfig, feature_selection: e.target.value})}>
                            <option value="none">None</option>
                            <option value="constant">Remove Constant Cols</option>
                            <option value="correlation">Remove Correlated Cols</option>
                            <option value="selectkbest">Select K Best</option>
                            <option value="mutual_info">Mutual Information</option>
                          </select>
                        </div>

                        {config.task_type === 'classification' && (
                          <div className="input-group">
                            <label className="input-label text-xs">Class Imbalance Strategy</label>
                            <select className="input-field py-1 text-xs" value={prepConfig.imbalance_strategy} onChange={e => setPrepConfig({...prepConfig, imbalance_strategy: e.target.value})}>
                              <option value="none">None</option>
                              <option value="random_undersample">Random Undersampling</option>
                              <option value="random_oversample">Random Oversampling</option>
                              <option value="smote">SMOTE</option>
                            </select>
                          </div>
                        )}

                        <div className="input-group">
                          <label className="input-label text-xs">Duplicate Handling</label>
                          <select className="input-field py-1 text-xs" value={prepConfig.duplicate_handling} onChange={e => setPrepConfig({...prepConfig, duplicate_handling: e.target.value})}>
                            <option value="keep">Keep Duplicates</option>
                            <option value="remove">Remove Duplicates</option>
                          </select>
                        </div>

                        <div className="input-group">
                          <label className="input-label text-xs">Drop Columns (Comma separated)</label>
                          <input type="text" className="input-field py-1 text-xs" placeholder="e.g. id, Name, Ticket" value={prepConfig.drop_columns} onChange={e => setPrepConfig({...prepConfig, drop_columns: e.target.value})} />
                          {tabularAnalysis.potential_id_columns?.length > 0 && (
                            <div className="text-xs text-muted mt-1">Suggested IDs: {tabularAnalysis.potential_id_columns.join(", ")}</div>
                          )}
                        </div>

                        <button 
                          className="btn btn-secondary w-full py-1.5 text-xs flex items-center justify-center gap-2 mt-4"
                          onClick={handleDownloadPreprocessed}
                          disabled={isDownloading}
                        >
                          <DownloadIcon size={14} /> {isDownloading ? 'Processing...' : 'Download Preprocessed'}
                        </button>
                      </>
                    ) : (
                      <div className="text-rose-400 text-center py-4">Failed to load analysis.</div>
                    )}
                  </div>
                )}
              </div>
            )}

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
          <ProgressBar 
            progress={progress} 
            epoch={metrics.epoch} 
            totalEpochs={config.epochs}
            loss={metrics.loss}
            accuracy={metrics.acc}
            eta={
              status === 'idle' ? 'Ready to start' :
              status === 'training' ? 'Training Model...' : 
              status === 'computing_valuations' ? (isSklearn ? 'Computing Fast Leave-One-Out (Sklearn)...' : 'Computing TracIn & Embeddings (PyTorch)...') :
              status === 'storing_results' ? 'Saving results to DB...' : 'Done'
            }
          />

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
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.04)" />
                  <XAxis dataKey="epoch" stroke="#a0a0a0" fontSize={12} tickLine={false} />
                  <YAxis yAxisId="left" stroke="#a0a0a0" fontSize={12} tickLine={false} domain={[0, 'auto']} />
                  <YAxis yAxisId="right" orientation="right" stroke="#34d399" fontSize={12} tickLine={false} domain={[0, 1]} />
                  <Tooltip contentStyle={{ backgroundColor: 'var(--bg-surface)', borderColor: 'var(--border-glass)' }} />
                  <Line yAxisId="left" type="monotone" dataKey="loss" stroke="#007BFF" strokeWidth={2} dot={false} isAnimationActive={false} />
                  <Line yAxisId="right" type="monotone" dataKey="accuracy" stroke="#34d399" strokeWidth={2} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
