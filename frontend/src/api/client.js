/**
 * DataValuator API Client
 * 
 * Provides functions for all backend API calls and a WebSocket hook
 * for real-time training progress updates.
 */
import { useState, useEffect, useRef, useCallback } from 'react';

const BASE_URL = '/api';

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  // ---- Datasets ---- //
  listDatasets: () => request('/datasets'),

  uploadDataset: async (formData) => {
    const res = await fetch(`${BASE_URL}/datasets/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error('Upload failed');
    return res.json();
  },

  downloadCifar10: () =>
    request('/datasets/cifar10', { method: 'POST' }),

  getDataset: (id) => request(`/datasets/${id}`),

  deleteDataset: (id) =>
    request(`/datasets/${id}`, { method: 'DELETE' }),

  // ---- Training ---- //
  startTraining: (config) =>
    request('/training/start', {
      method: 'POST',
      body: JSON.stringify(config),
    }),

  getTrainingStatus: () => request('/training/status'),

  stopTraining: () =>
    request('/training/stop', { method: 'POST' }),

  getTrainingHistory: () => request('/training/history'),

  getTrainingRun: (runId) => request(`/training/${runId}`),

  // ---- Valuation ---- //
  getValuationSummary: (runId) =>
    request(`/valuation/${runId}/summary`),

  getValuationSamples: (runId, params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/valuation/${runId}/samples${qs ? '?' + qs : ''}`);
  },

  getSampleDetail: (runId, sampleIndex) =>
    request(`/valuation/${runId}/sample/${sampleIndex}`),

  getDistribution: (runId) =>
    request(`/valuation/${runId}/distribution`),

  getEmbeddings: (runId) =>
    request(`/valuation/${runId}/embeddings`),

  exportValuations: (runId) => {
    window.open(`${BASE_URL}/valuation/${runId}/export`, '_blank');
  },

  exportRefinedDataset: (runId, excludeCategories = 'harmful,redundant') => {
    window.open(`${BASE_URL}/valuation/${runId}/export-refined?exclude=${excludeCategories}`, '_blank');
  },

  // ---- Experiments ---- //
  startPruneExperiment: (config) =>
    request('/experiments/prune', {
      method: 'POST',
      body: JSON.stringify(config),
    }),

  startRandomPrune: (config) =>
    request('/experiments/random-prune', {
      method: 'POST',
      body: JSON.stringify(config),
    }),

  startLabelCorruption: (config) =>
    request('/experiments/label-corruption', {
      method: 'POST',
      body: JSON.stringify(config),
    }),

  getExperimentResults: (id) => request(`/experiments/${id}/results`),

  getExperimentHistory: () => request('/experiments/history'),
};


/**
 * React hook for WebSocket connection to training progress updates.
 * Auto-reconnects on disconnect with exponential backoff.
 * 
 * @param {function} onMessage - Callback invoked with each parsed message object
 * @returns {{ connected: boolean, lastMessage: object|null }}
 */
export function useTrainingSocket(onMessage) {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const onMessageRef = useRef(onMessage);

  // Keep callback ref current without re-triggering effect
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/training`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      console.log('[WS] Connected to training socket');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);
        onMessageRef.current?.(data);
      } catch (e) {
        console.warn('[WS] Failed to parse message:', event.data);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      console.log('[WS] Disconnected, reconnecting in 3s...');
      reconnectTimer.current = setTimeout(connect, 3000);
    };

    ws.onerror = (err) => {
      console.error('[WS] Error:', err);
      ws.close();
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { connected, lastMessage };
}
