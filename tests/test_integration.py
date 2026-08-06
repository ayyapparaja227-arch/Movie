import pytest
import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_api_endpoints_integration():
    """Verify that all API endpoints respond correctly and return structured JSON."""
    
    # 1. Check Health Endpoint
    health_resp = requests.get(f"{BASE_URL}/health")
    assert health_resp.status_code == 200
    health_data = health_resp.json()
    assert health_data["status"] == "ok"
    assert health_data["model_loaded"] is True
    
    # 2. Predict with Known Creator (No Cold Start)
    payload_known = {
        "title": "Netflix Exclusive Season Final",
        "channel_title": "Netflix",
        "genre": "Thriller",
        "duration_minutes": 90,
        "upload_time": "2026-08-06T20:00:00Z",
        "language": "en",
        "tags": ["season", "final", "exclusive"]
    }
    pred_resp = requests.post(f"{BASE_URL}/predict", json=payload_known)
    assert pred_resp.status_code == 200
    pred_data = pred_resp.json()
    assert pred_data["cold_start"] is False
    assert pred_data["grounded"] is True
    assert "trending_probability" in pred_data
    assert "explanation" in pred_data
    
    # 3. Predict with Unseen Creator (Engages Cold Start)
    payload_unseen = {
        "title": "My cooking recipe vlog",
        "channel_title": "ChefGordonUnseenChannel",
        "genre": "Comedy",
        "duration_minutes": 10,
        "upload_time": "2026-08-06T15:30:00Z",
        "language": "en",
        "tags": ["cooking", "recipe", "vlog"]
    }
    pred_resp2 = requests.post(f"{BASE_URL}/predict", json=payload_unseen)
    assert pred_resp2.status_code == 200
    pred_data2 = pred_resp2.json()
    assert pred_data2["cold_start"] is True
    assert "content_only" in pred_data2["model_version"]
    
    # 4. Predict with Unseen Genre (Ungrounded)
    payload_unseen_genre = {
        "title": "Avant garde short art movie",
        "channel_title": "Netflix",
        "genre": "Neo-Art-Nouveau-Cyberpunk",
        "duration_minutes": 15,
        "upload_time": "2026-08-06T18:00:00Z",
        "language": "en",
        "tags": ["art", "movie"]
    }
    pred_resp3 = requests.post(f"{BASE_URL}/predict", json=payload_unseen_genre)
    assert pred_resp3.status_code == 200
    pred_data3 = pred_resp3.json()
    assert pred_data3["grounded"] is False
    assert pred_data3["predicted_label"] == "uncertain"
    
    # 5. Check Metrics Endpoint (Prometheus metrics)
    metrics_resp = requests.get(f"{BASE_URL}/metrics")
    assert metrics_resp.status_code == 200
    assert "http_requests_total" in metrics_resp.text
