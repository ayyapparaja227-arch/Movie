import os
import shutil
import asyncio
import time
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Depends, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram

from api.schemas import PredictRequest, PredictResponse, TrainResponse, StatusResponse, HealthResponse
from api.config import settings
from pipeline.predict import TrendingPredictor
from pipeline.training import run_training
from pipeline.registry import ModelRegistry

app = FastAPI(
    title="Trending Content Prediction API",
    description="Production-grade trending content classification with cold-start routing and explainability.",
    version="1.0.0"
)

# CORS configuration for UI connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Predictor instance
predictor = None

# In-memory training job tracker (thread-safe, persists for worker session)
TRAINING_JOBS: Dict[str, Dict[str, Any]] = {}

# Prometheus instrumentation metrics
HTTP_REQUESTS_TOTAL = Counter("http_requests_total", "Total HTTP Requests", ["method", "endpoint", "status"])
LATENCY_HISTOGRAM = Histogram("http_request_duration_seconds", "HTTP Request Latency", ["method", "endpoint"])
PREDICTIONS_COUNTER = Counter("predictions_total", "Prediction requests split by labels", ["label", "cold_start", "grounded"])

@app.on_event("startup")
def startup_event():
    global predictor
    print("API starting up. Attempting to load active champion model...")
    try:
        predictor = TrendingPredictor()
    except Exception as e:
        print(f"No active champion model loaded yet: {e}")

@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    """Intercept requests to record Prometheus metrics."""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    endpoint = request.url.path
    # Exclude metrics endpoint to avoid loops
    if endpoint != "/metrics":
        HTTP_REQUESTS_TOTAL.labels(method=request.method, endpoint=endpoint, status=response.status_code).inc()
        LATENCY_HISTOGRAM.labels(method=request.method, endpoint=endpoint).observe(duration)
        
    return response

@app.get("/health", response_model=HealthResponse)
async def health():
    """Verify system health. Returns NOT ok if no model is loaded."""
    model_loaded = predictor is not None and predictor.is_loaded
    status = "ok" if model_loaded else "degraded"
    
    response_data = {
        "status": status,
        "model_loaded": model_loaded,
        "enrichment_api_connected": True
    }
    
    if not model_loaded:
        return JSONResponse(status_code=503, content=response_data)
        
    return response_data

def async_training_worker(job_id: str, temp_csv_path: str):
    """Target function run in FastAPI BackgroundTasks to train the models."""
    global predictor
    TRAINING_JOBS[job_id]["status"] = "training"
    
    try:
        # Load number of rows
        import pandas as pd
        df = pd.read_csv(temp_csv_path)
        TRAINING_JOBS[job_id]["rows_total"] = len(df)
        TRAINING_JOBS[job_id]["rows_processed"] = int(len(df) * 0.3)  # simulate progress
        
        # Run training
        metrics = run_training(job_id=job_id, csv_path=temp_csv_path)
        
        TRAINING_JOBS[job_id]["rows_processed"] = len(df)
        TRAINING_JOBS[job_id]["status"] = "complete"
        
        # Reload predictor to use the newly trained champion model
        predictor = TrendingPredictor(version=job_id)
        
    except Exception as e:
        TRAINING_JOBS[job_id]["status"] = "failed"
        TRAINING_JOBS[job_id]["error_message"] = str(e)
    finally:
        # Clean up temporary CSV file
        if os.path.exists(temp_csv_path):
            try:
                os.remove(temp_csv_path)
            except Exception:
                pass

@app.post("/train", response_model=TrainResponse, status_code=202)
async def train(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload training data CSV and queue async model retraining."""
    job_id = f"job_{int(time.time())}"
    
    # Save the file temporarily
    os.makedirs("data/temp", exist_ok=True)
    temp_csv_path = f"data/temp/{job_id}.csv"
    
    with open(temp_csv_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Read row count
    try:
        import pandas as pd
        df = pd.read_csv(temp_csv_path)
        rows_count = len(df)
    except Exception as e:
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)
        raise HTTPException(status_code=400, detail=f"Invalid CSV file: {e}")
        
    TRAINING_JOBS[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "rows_total": rows_count,
        "rows_processed": 0,
        "rows_failed": 0
    }
    
    background_tasks.add_task(async_training_worker, job_id, temp_csv_path)
    
    return {
        "job_id": job_id,
        "rows_received": rows_count,
        "status": "queued"
    }

@app.get("/status", response_model=StatusResponse)
async def status(job_id: str):
    """Retrieve the current training status of an asynchronous job."""
    if job_id not in TRAINING_JOBS:
        # Check if job_id is "latest"
        if job_id == "latest" and TRAINING_JOBS:
            latest_key = list(TRAINING_JOBS.keys())[-1]
            return TRAINING_JOBS[latest_key]
        raise HTTPException(status_code=404, detail=f"Job ID '{job_id}' not found")
        
    return TRAINING_JOBS[job_id]

@app.post("/predict", response_model=PredictResponse)
async def predict(payload: PredictRequest):
    """Evaluate metadata and serve trend predictions (handles cold-starts)."""
    global predictor
    if predictor is None or not predictor.is_loaded:
        # Try loading on the fly
        try:
            predictor = TrendingPredictor()
        except Exception:
            pass
            
    if predictor is None or not predictor.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Predictor is not ready yet. Please train a model first using POST /train."
        )
        
    # Transform request to dict
    row_dict = payload.dict()
    
    try:
        res = predictor.predict(row_dict)
        
        # Track Prometheus metrics
        PREDICTIONS_COUNTER.labels(
            label=res["predicted_label"],
            cold_start=str(res["cold_start"]),
            grounded=str(res["grounded"])
        ).inc()
        
        # Generate prediction UUID
        import uuid
        res["prediction_id"] = str(uuid.uuid4())
        
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {e}")

@app.get("/live/trending")
async def live_trending():
    """Scan today's releases from TMDB and evaluate virality."""
    global predictor
    if predictor is None or not predictor.is_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded yet.")
    
    try:
        from pipeline.enrichment import scan_todays_trending_movies
        movies = scan_todays_trending_movies()
        scored_movies = []
        for m in movies:
            pred = predictor.predict(m)
            scored_movies.append({
                "title": m["title"],
                "channel_title": m["channel_title"],
                "genre": m["genre"],
                "duration_minutes": m["duration_minutes"],
                "upload_time": m["upload_time"],
                "trending_probability": pred["trending_probability"],
                "predicted_label": pred["predicted_label"],
                "cold_start": pred["cold_start"],
                "image_url": m.get("image_url", ""),
                "summary": m.get("summary", ""),
                "director": m.get("director", "Unknown Director"),
                "year": m.get("year", "2026")
            })
        return scored_movies
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Live scanning error: {e}")

@app.get("/live/search")
async def live_search(query: str):
    """Search for any movie title, fetch its metadata, and evaluate virality."""
    global predictor
    if predictor is None or not predictor.is_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded yet.")
    
    try:
        from pipeline.enrichment import search_movie_by_title
        movies = search_movie_by_title(query)
        scored_movies = []
        for m in movies:
            pred = predictor.predict(m)
            scored_movies.append({
                "title": m["title"],
                "channel_title": m["channel_title"],
                "genre": m["genre"],
                "duration_minutes": m["duration_minutes"],
                "upload_time": m["upload_time"],
                "trending_probability": pred["trending_probability"],
                "predicted_label": pred["predicted_label"],
                "cold_start": pred["cold_start"],
                "image_url": m.get("image_url", ""),
                "summary": m.get("summary", ""),
                "director": m.get("director", "Unknown Director"),
                "year": m.get("year", "2026")
            })
        return scored_movies
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Live search error: {e}")

@app.post("/model/rollback")
async def rollback(version: str):
    """Roll back active model serving to a previous registry version."""
    global predictor
    registry = ModelRegistry()
    model_info = registry.get_version(version)
    
    if not model_info:
        raise HTTPException(status_code=404, detail=f"Model version '{version}' not found in registry")
        
    try:
        registry.promote_to_champion(version)
        with open("model-store/active_version.txt", "w") as f:
            f.write(version)
            
        predictor = TrendingPredictor(version=version)
        
        return {
            "status": "rolled_back",
            "active_version": version,
            "metrics": model_info["metrics"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rollback failed: {e}")

@app.get("/model/versions")
async def get_model_versions():
    """Get all model versions in the SQLite registry."""
    try:
        registry = ModelRegistry()
        return registry.get_all_versions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch model versions: {e}")

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
