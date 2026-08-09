import React, { useState, useEffect } from 'react';
import FileUpload from '../components/FileUpload';
import { api } from '../api/client';
import { useNavigate } from 'react-router-dom';
import { FolderIcon, FileTextIcon } from '../components/Icons';

export default function Datasets() {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const fetchDatasets = async () => {
    setLoading(true);
    try {
      const data = await api.listDatasets();
      setDatasets(data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const handleUploadSuccess = () => {
    fetchDatasets();
  };

  const handleDelete = async (id) => {
    if (window.confirm('Delete this dataset?')) {
      await api.deleteDataset(id);
      fetchDatasets();
    }
  };

  return (
    <div className="space-y-6">
      <FileUpload onUploadSuccess={handleUploadSuccess} />

      <div>
        <h2 className="text-xl font-semibold mb-4">Available Datasets</h2>
        
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1,2,3].map(i => <div key={i} className="h-40 skeleton" />)}
          </div>
        ) : datasets.length === 0 ? (
          <div className="glass-panel p-12 text-center flex flex-col items-center">
            <div className="text-6xl mb-4 opacity-50"><FolderIcon size={48} /></div>
            <h3 className="text-lg font-medium text-secondary">No datasets found</h3>
            <p className="text-muted mt-2">Upload a dataset above to get started.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {datasets.map(ds => (
              <div key={ds.id} className="glass-card flex flex-col group">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-surface flex items-center justify-center text-xl">
                      <FileTextIcon size={20} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-lg">{ds.name}</h3>
                      <p className="text-xs text-muted">{new Date(ds.createdAt).toLocaleDateString()}</p>
                    </div>
                  </div>
                </div>
                
                <div className="flex justify-between py-3 border-y border-glass mb-4">
                  <div className="text-center">
                    <p className="text-xs text-muted uppercase">Samples</p>
                    <p className="font-mono font-medium">{ds.sampleCount.toLocaleString()}</p>
                  </div>
                  <div className="text-center border-l border-glass pl-4">
                    <p className="text-xs text-muted uppercase">Classes</p>
                    <p className="font-mono font-medium">{ds.classCount}</p>
                  </div>
                </div>

                <div className="mt-auto flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button 
                    onClick={() => navigate('/training')} 
                    className="btn btn-primary flex-1 py-1 text-xs"
                  >
                    Train
                  </button>
                  <button 
                    onClick={() => handleDelete(ds.id)} 
                    className="btn btn-danger py-1 text-xs px-3"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
