# DataValuator

An end-to-end Machine Learning platform designed to determine which training samples actually matter to a model's performance. By tracking and analyzing data during and after training, DataValuator helps you identify low-quality data, mislabeled samples, and high-value points.

## Key Features

- **Multi-Modal Support**: Train on both Image datasets (via PyTorch CNNs/ResNets) and Tabular datasets (via Scikit-Learn Logistic Regression, Trees, Forests, or Tabular Neural Nets).
- **Tabular Preprocessing UI**: Visually configure pipelines to handle missing values, categorical encoding, scaling, outliers, and feature selection before training.
- **Real-Time Dashboards**: Monitor model training metrics, sample-level metrics (e.g. Forgetting Events, AUM), and system metrics via WebSockets.
- **Valuation Techniques**: Includes implementations of TracIn, Area Under the Margin (AUM), Forgetting Events, Leave-One-Out, and k-NN Rarity Analysis.
- **Experiments Engine**: Prune datasets based on valuation scores or inject label noise to validate how your dataset modifications affect real-world accuracy.

## Quick Start (Windows)

We provide convenient batch scripts for Windows to manage the environment:

1. **Start the App**: Double-click `start.bat`
   - This will automatically check prerequisites, create virtual environments, install Python & Node.js dependencies, launch the backend and frontend in minimized windows, and open the dashboard in your default browser.
2. **Stop the App**: Double-click `stop.bat`
   - This cleanly shuts down the frontend and backend servers.

## Manual Start

If you prefer to start the servers manually or are not on Windows:

### Backend
```bash
cd backend
python -m venv venv
source venv/Scripts/activate  # On macOS/Linux use: source venv/bin/activate
pip install -r requirements.txt
python run.py
```
*The API server starts at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.*

### Frontend
```bash
cd frontend
npm install
npm run dev
```
*The dashboard opens at `http://localhost:5173`.*

## Architecture

```
Frontend (React + Vite)  ←→  Backend (FastAPI)  ←→  ML Engine (PyTorch / Sklearn)
         ↕                          ↕                        ↕
    Plotly/Recharts            SQLite + HDF5         FAISS + UMAP + TracIn
```

## Project Structure

```
DataValuator/
├── backend/
│   ├── app/
│   │   ├── engine/        # PyTorch & Sklearn ML pipelines, Preprocessing, Valuation
│   │   ├── models/        # Pydantic schemas
│   │   ├── routers/       # API endpoints
│   │   ├── services/      # Job manager, WebSockets
│   │   ├── config.py      # Settings
│   │   ├── database.py    # SQLite layer
│   │   └── main.py        # FastAPI app
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── api/           # API client + WebSocket hook
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Dashboard, Training, Explorer, Experiments
│   │   └── index.css      # Design system
│   ├── package.json
│   └── vite.config.js
├── data/                  # Runtime data (gitignored)
├── start.bat              # Auto-start script
└── stop.bat               # Auto-stop script
```
