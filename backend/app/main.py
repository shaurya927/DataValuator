from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import init_db, close_db
from app.routers import datasets, training, valuation, experiments
from app.services.ws_manager import manager as ws_manager
from app.auth import verify_api_key

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    await init_db(settings.DB_PATH)
    yield
    await close_db()

app = FastAPI(title="DataValuator API", lifespan=lifespan, dependencies=[Depends(verify_api_key)])

# CORS — use configurable origins, not wildcard with credentials
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets.router)
app.include_router(training.router)
app.include_router(valuation.router)
app.include_router(experiments.router)

app.mount("/static", StaticFiles(directory=settings.UPLOAD_DIR), name="static")

@app.websocket("/ws/training")
async def websocket_training(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
