import React, { useState, useRef, useEffect } from 'react';
import { api } from '../api/client';
import { FolderIcon, ZapIcon, TargetIcon, BrainIcon, RocketIcon } from './Icons';

export default function FileUpload({ onUploadSuccess }) {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef(null);

  // Wizard state
  const [step, setStep] = useState(1);
  const [taskType, setTaskType] = useState('image_classification');
  const [targetColumn, setTargetColumn] = useState('target');
  const [template, setTemplate] = useState('resnet18');

  useEffect(() => {
    if (file) {
      if (file.name.toLowerCase().endsWith('.csv')) {
        setTaskType('tabular_classification');
        setTemplate('tabular');
      } else {
        setTaskType('image_classification');
        setTemplate('resnet18');
      }
      setStep(2);
    }
  }, [file]);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    
    const interval = setInterval(() => {
      setProgress(p => {
        if (p >= 90) return p;
        return p + 10;
      });
    }, 200);
    
    try {
      const formData = new FormData();
      formData.append('file', file); // FastAPI expects 'file' not 'dataset'
      formData.append('task_type', taskType);
      formData.append('target_column', targetColumn);
      formData.append('template', template);

      const res = await api.uploadDataset(formData);
      clearInterval(interval);
      setProgress(100);
      setTimeout(() => {
        setUploading(false);
        setFile(null);
        setStep(1);
        setProgress(0);
        if (onUploadSuccess) onUploadSuccess(res.id);
      }, 500);
    } catch (err) {
      console.error(err);
      clearInterval(interval);
      setUploading(false);
    }
  };

  const handleDownloadCifar = async () => {
    setUploading(true);
    try {
      const res = await api.downloadCifar10();
      setUploading(false);
      if (onUploadSuccess) onUploadSuccess(res.id);
    } catch (err) {
      setUploading(false);
    }
  };

  const resetWizard = () => {
    setFile(null);
    setStep(1);
  };

  return (
    <div className="glass-panel p-6 mb-6">
      {step === 1 && (
        <div 
          className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center transition-all ${
            isDragging ? 'border-accent-blue bg-accent-blue-alpha' : 'border-glass hover:border-text-muted'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <div className="text-4xl mb-4 text-secondary"><FolderIcon size={40} /></div>
          <h3 className="text-lg font-medium mb-2">Drag & Drop Dataset Here</h3>
          <p className="text-sm text-muted mb-4">Supports CSV, ZIP containing images, or PyTorch tensors</p>
          
          <input 
            type="file" 
            className="hidden" 
            ref={fileInputRef} 
            onChange={handleFileChange}
          />
          
          {!uploading && (
            <div className="flex gap-4 mt-4">
              <button className="btn btn-secondary" onClick={() => fileInputRef.current?.click()}>
                Browse Files
              </button>
              <span className="text-muted self-center">or</span>
              <button className="btn btn-primary flex items-center gap-2" onClick={handleDownloadCifar}>
                <ZapIcon size={14} /> Download CIFAR-10
              </button>
            </div>
          )}
        </div>
      )}

      {step === 2 && !uploading && (
        <div className="flex flex-col items-center">
          <div className="text-3xl mb-4"><TargetIcon size={32} /></div>
          <h3 className="text-xl font-semibold mb-2">What are you trying to predict?</h3>
          <p className="text-sm text-muted mb-6 text-center max-w-md">
            Help us understand your dataset so we can configure the optimal training pipeline.
          </p>

          <div className="w-full max-w-md space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Task Type</label>
              <select 
                value={taskType} 
                onChange={e => setTaskType(e.target.value)}
                className="w-full bg-surface border border-glass rounded-md p-2"
              >
                <option value="image_classification">Image Classification</option>
                <option value="tabular_classification">Tabular Classification</option>
              </select>
            </div>

            {taskType === 'tabular_classification' && (
              <div>
                <label className="block text-sm font-medium mb-1">Target Column Name</label>
                <input 
                  type="text" 
                  value={targetColumn} 
                  onChange={e => setTargetColumn(e.target.value)}
                  placeholder="e.g., target, label, class"
                  className="w-full bg-surface border border-glass rounded-md p-2"
                />
              </div>
            )}

            <div className="flex justify-end gap-3 mt-6">
              <button className="btn btn-ghost" onClick={resetWizard}>Cancel</button>
              <button className="btn btn-primary" onClick={() => setStep(3)}>Next</button>
            </div>
          </div>
        </div>
      )}

      {step === 3 && !uploading && (
        <div className="flex flex-col items-center">
          <div className="text-3xl mb-4"><BrainIcon size={32} /></div>
          <h3 className="text-xl font-semibold mb-2">Choose your Model</h3>
          <p className="text-sm text-muted mb-6 text-center max-w-md">
            Select the architecture you want to train.
          </p>

          <div className="w-full max-w-md space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Model Template</label>
              <select 
                value={template} 
                onChange={e => setTemplate(e.target.value)}
                className="w-full bg-surface border border-glass rounded-md p-2"
              >
                {taskType === 'image_classification' ? (
                  <>
                    <option value="resnet18">ResNet-18 (Recommended)</option>
                    <option value="simple_cnn">Simple CNN (Fast)</option>
                  </>
                ) : (
                  <option value="tabular">Simple Tabular Net</option>
                )}
              </select>
            </div>

            <div className="px-4 py-3 bg-surface-elevated rounded-md border border-glass flex justify-between items-center mt-4">
              <span className="text-primary truncate max-w-xs">{file.name}</span>
              <span className="text-xs text-muted">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
            </div>

            <div className="flex justify-between mt-6">
              <button className="btn btn-ghost" onClick={() => setStep(2)}>Back</button>
              <div className="flex gap-2">
                <button className="btn btn-ghost text-danger" onClick={resetWizard}>Cancel</button>
                <button className="btn btn-primary" onClick={handleUpload}>Start Upload</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {uploading && (
        <div className="flex flex-col items-center justify-center py-8">
          <div className="w-full max-w-md">
            <div className="flex justify-between text-sm mb-2">
              <span className="font-medium text-accent-blue">Uploading and Configuring...</span>
              <span>{progress}%</span>
            </div>
            <div className="w-full h-3 bg-surface rounded-full overflow-hidden border border-glass">
              <div 
                className="h-full bg-accent-blue transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
