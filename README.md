# DataValuator

An end-to-end ML platform that determines which training samples actually matter to a machine-learning model.

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
python run.py
```

The API server starts at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dashboard opens at `http://localhost:5173`.

### First Run

1. Open the dashboard
2. Go to **Datasets** → click **Download CIFAR-10**
3. Go to **Training** → select CIFAR-10, choose a model, click **Start Training**
4. Watch live training progress via WebSocket
5. When complete, explore results in **Explorer** and run validation in **Experiments**

## Architecture

```
Frontend (React + Vite)  ←→  Backend (FastAPI)  ←→  ML Engine (PyTorch)
         ↕                          ↕                        ↕
    Plotly/Recharts            SQLite + HDF5         FAISS + UMAP
```

## Valuation Techniques

| Technique | What it measures | Computational cost |
|-----------|-----------------|-------------------|
| Forgetting Events | How often a sample is forgotten during training | O(1) per sample/epoch |
| Loss/AUM Tracking | Per-sample loss trajectory and logit margin | O(N) per epoch |
| TracIn | Gradient-based influence across checkpoints | O(K·N·p) post-training |
| Rarity Analysis | Embedding-space density via FAISS k-NN | O(N·log N) post-training |
| Unified Score | Weighted combination of all signals | O(N) post-training |

## Project Structure

```
DataValuator/
├── backend/
│   ├── app/
│   │   ├── engine/        # PyTorch ML pipeline
│   │   ├── models/        # Pydantic schemas
│   │   ├── routers/       # API endpoints
│   │   ├── services/      # Job manager, WebSocket
│   │   ├── config.py      # Settings
│   │   ├── database.py    # SQLite layer
│   │   └── main.py        # FastAPI app
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── api/           # API client + WebSocket hook
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Dashboard, Training, Explorer, etc.
│   │   └── index.css      # Design system
│   ├── package.json
│   └── vite.config.js
└── data/                  # Runtime data (gitignored)
```
