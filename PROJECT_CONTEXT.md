# DataValuator Project Context

## Project Purpose
DataValuator is an end-to-end Machine Learning platform designed to determine the value of individual training samples to a model. It helps researchers and engineers identify harmful, suspicious, redundant, or high-value data points within a dataset by analyzing learning dynamics during training (e.g., forgetting events, loss trajectories) and evaluating post-training signals (e.g., gradient influence, embedding rarity). 

## Architecture
The system follows a modern decoupled architecture:
- **Frontend**: A Single Page Application (SPA) providing a dashboard for dataset management, training monitoring, and data exploration.
- **Backend**: An asynchronous API server handling business logic, orchestrating ML jobs, and serving data to the frontend.
- **ML Engine**: A core pipeline built on PyTorch that conducts the actual training, tracking, and valuation computation.
- **Storage Layer**: A hybrid approach using SQLite for relational metadata and HDF5 for dense, high-frequency training metrics.

## Folder Structure
```
DataValuator/
├── backend/
│   ├── app/
│   │   ├── engine/        # PyTorch ML pipeline (trainer, trackers, valuator)
│   │   ├── models/        # Pydantic schemas for data validation
│   │   ├── routers/       # FastAPI REST API endpoints
│   │   ├── services/      # Background services (e.g., WebSocket manager)
│   │   ├── config.py      # Pydantic settings management
│   │   ├── database.py    # Async SQLite database layer
│   │   └── main.py        # FastAPI application entrypoint
│   ├── requirements.txt
│   └── run.py             # Script to start the Uvicorn server
├── frontend/
│   ├── src/
│   │   ├── api/           # API client (client.js) handling REST and WebSockets
│   │   ├── components/    # Reusable React UI components
│   │   ├── pages/         # High-level route components (Dashboard, Explorer)
│   │   └── index.css      # Application styling
│   ├── package.json
│   └── vite.config.js
└── data/                  # Local storage (gitignored) for DB, uploads, metrics, and checkpoints
```

## Technology Stack
- **Frontend**: React (v19), Vite, React Router DOM, Plotly.js, Recharts
- **Backend**: Python, FastAPI, Uvicorn (ASGI), Pydantic
- **ML / Data Science**: PyTorch, Torchvision, FAISS (similarity search), UMAP-learn (dimensionality reduction), NumPy, Pandas
- **Database / Storage**: SQLite (via `aiosqlite`), HDF5 (via `h5py`)

## Important Files
- `backend/app/main.py`: Configures FastAPI, WebSockets, CORS, and static file mounting.
- `backend/app/engine/trainer.py`: The custom PyTorch training loop that integrates metrics tracking and HDF5 storage.
- `backend/app/engine/valuator.py`: Computes the final unified valuation scores and categorizes samples based on all collected signals.
- `backend/app/database.py`: Handles all async interactions with the SQLite database and schema initialization.
- `frontend/src/api/client.js`: Centralized API client managing all HTTP requests and WebSocket auto-reconnection logic.

## Frontend/Backend Communication
- **REST API (HTTP)**: Used for stateless operations—uploading datasets, starting jobs, fetching historical runs, and querying sample valuations.
- **WebSockets (`/ws/training`)**: Provides real-time, low-latency streaming of training progress (epoch, loss, accuracy) from the backend directly to the frontend dashboard.

## Database Schema (SQLite)
- `datasets`: Stores metadata about uploaded/downloaded datasets.
- `training_runs`: Tracks metadata for individual training jobs (epochs, learning rate, status, file paths).
- `sample_valuations`: Stores the computed valuation scores (forgetting count, AUM, TracIn, rarity, unified score) and category for every sample in a run.
- `experiments`: Tracks ablation experiments run against specific valuations (e.g., pruning harmful samples).

## ML Pipeline
1. **Training & Tracking**: `DataValuatorTrainer` runs the PyTorch loop. `ForgettingTracker` and `LossAUMTracker` record per-sample metrics on every batch.
2. **Dense Storage**: Per-sample, per-epoch losses and margins are written to an HDF5 `MetricStore`.
3. **Post-Training Analysis**: 
   - Checkpoints are analyzed to calculate gradient-based influence (TracIn).
   - FAISS k-NN is used on sample embeddings to compute rarity scores.
4. **Unified Valuation**: `valuator.py` combines percentiles of forgetting events, loss, AUM, TracIn, and rarity using weighted sums to generate a Unified Score and a categorical label (harmful, suspicious, redundant, high-value, normal).

## API Endpoints
Organized into separate routers:
- `/datasets`: `GET /`, `POST /upload`, `POST /cifar10`, `GET /{id}`, `DELETE /{id}`
- `/training`: `POST /start`, `GET /status`, `POST /stop`, `GET /history`, `GET /{run_id}`
- `/valuation`: `GET /{run_id}/summary`, `GET /{run_id}/samples`, `GET /{run_id}/sample/{idx}`, `GET /{run_id}/distribution`, `GET /{run_id}/embeddings`, `GET /{run_id}/export`
- `/experiments`: `POST /prune`, `POST /random-prune`, `POST /label-corruption`, `GET /history`, `GET /{id}/results`

## Environment Variables / Configuration
Managed via Pydantic `BaseSettings` in `config.py`. Defaults are optimized for local execution.
- `APP_NAME`: DataValuator
- Directories: `DATA_DIR`, `UPLOAD_DIR`, `CHECKPOINT_DIR`, `METRICS_DIR`
- SQLite DB Path: `DB_PATH`
- Defaults: `DEFAULT_EPOCHS`, `DEFAULT_LR`, `CHECKPOINT_INTERVAL`, `MAX_UPLOAD_SIZE`

## Deployment Architecture
Currently designed for local execution.
- **Server**: Uvicorn serves the FastAPI backend on `localhost:8000`.
- **Client**: Vite serves the frontend on `localhost:5173`.
- **Storage**: The `data/` folder on the local file system acts as the source of truth for the database, metrics, and models.

## Current Implementation Status
The core pipeline is implemented and runnable locally. The system can successfully download CIFAR-10, run a training job with live WebSocket tracking, compute valuations, store them in SQLite, and serve them to the frontend for exploration.

## Known Issues
- **Concurrency & Blocking**: Intense ML loops (`trainer.py`) and FAISS computations run synchronously. If executed within the main FastAPI event loop, they can block other API requests. A background worker queue (like Celery) is not currently implemented.
- **Scalability**: Heavy reliance on local SQLite and local HDF5 files limits horizontal scalability.
- **Hardcoded Parameters**: Valuation weighting in `valuator.py` is hardcoded, which might not optimally generalize to all dataset distributions.
- **Lack of Authentication**: The system currently has no authentication or user session management.

## Important Design Decisions
- **Hybrid Storage (SQLite + HDF5)**: Storing per-epoch metrics for tens of thousands of samples would quickly bloat a SQLite database and cause write contention. HDF5 was chosen for metrics storage because it excels at high-speed writes and reads of large, dense numerical arrays. SQLite is strictly reserved for relational metadata.
- **WebSocket Streaming**: Chosen over HTTP polling to provide a smooth, low-latency UX for monitoring training loops.
- **Unified Scoring**: Rather than relying on a single metric (like AUM or TracIn alone), the system aggregates multiple signals via percentiles to provide a more robust sample valuation.
