import pytest
import numpy as np
import pandas as pd
from pipeline.feature_engineering import FeatureEngineer

def test_cyclical_encoding_hour():
    """Verify hour 23 and hour 1 are closer in sin/cos space than 23 and 12."""
    fe = FeatureEngineer()
    h23_sin, h23_cos = fe.cyclical_encode(23, 24)
    h1_sin, h1_cos = fe.cyclical_encode(1, 24)
    h12_sin, h12_cos = fe.cyclical_encode(12, 24)
    
    dist_23_to_1 = np.sqrt((h23_sin - h1_sin)**2 + (h23_cos - h1_cos)**2)
    dist_23_to_12 = np.sqrt((h23_sin - h12_sin)**2 + (h23_cos - h12_cos)**2)
    
    assert dist_23_to_1 < dist_23_to_12, "Hour 23 -> 1 should be closer than 23 -> 12"

def test_unseen_genre_and_cold_start():
    """Verify unseen creators activate cold_start, and unseen genres are flagged."""
    # Fit on small mock dataframe
    train_data = pd.DataFrame([
        {"genre": "Action", "language": "en", "channel_title": "KnownChannel", "is_trending": 1},
        {"genre": "Drama", "language": "en", "channel_title": "KnownChannel", "is_trending": 0}
    ])
    
    fe = FeatureEngineer()
    fe.fit(train_data)
    
    # Unseen creator (cold start)
    row_unseen_creator = {
        "title": "Vlog",
        "channel_title": "UnseenCreator_99",
        "genre": "Action",
        "duration_minutes": 10,
        "upload_time": "2026-08-06T18:30:00Z",
        "language": "en",
        "tags": "tag1,tag2"
    }
    feats, meta = fe.transform_row(row_unseen_creator)
    assert meta["cold_start"] is True
    assert meta["genre_is_unseen"] is False
    
    # Unseen genre
    row_unseen_genre = {
        "title": "Vlog",
        "channel_title": "KnownChannel",
        "genre": "SciFiNovelty",
        "duration_minutes": 10,
        "upload_time": "2026-08-06T18:30:00Z",
        "language": "en",
        "tags": "tag1,tag2"
    }
    feats, meta = fe.transform_row(row_unseen_genre)
    assert meta["cold_start"] is False
    assert meta["genre_is_unseen"] is True

def test_missing_and_hostile_inputs():
    """Verify pipeline handles missing or malformed fields gracefully."""
    train_data = pd.DataFrame([
        {"genre": "Action", "language": "en", "channel_title": "KnownChannel", "is_trending": 1}
    ])
    fe = FeatureEngineer()
    fe.fit(train_data)
    
    # Missing duration and tags
    row = {
        "title": "Vlog",
        "channel_title": "KnownChannel",
        "genre": "Action",
        "upload_time": "2026-08-06T18:30:00Z",
        "language": "en"
    }
    feats, meta = fe.transform_row(row)
    assert feats["duration_minutes"] == 10.0  # Uses default fallback
    assert feats["tag_count"] == 0
    
    # Invalid upload_time
    row_invalid_time = {
        "title": "Vlog",
        "channel_title": "KnownChannel",
        "genre": "Action",
        "upload_time": "invalid_date_format_str"
    }
    feats, _ = fe.transform_row(row_invalid_time)
    assert feats["hour_sin"] is not None
