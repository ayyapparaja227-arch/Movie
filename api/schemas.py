from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class PredictRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500, description="Content title")
    channel_title: str = Field(..., min_length=1, max_length=200, description="Creator/Channel name")
    genre: str = Field(..., min_length=1, max_length=100, description="Primary content genre")
    duration_minutes: int = Field(..., ge=1, le=1440, description="Content runtime in minutes")
    upload_time: str = Field(..., description="ISO 8601 formatted upload time (e.g. 2026-08-06T18:30:00Z)")
    language: str = Field(..., min_length=2, max_length=10, description="Language code")
    tags: List[str] = Field(default_factory=list, description="Content tags list")

    @field_validator('genre')
    @classmethod
    def sanitize_genre(cls, v):
        """Sanitize genre inputs to be clean."""
        import re
        if not re.match(r'^[a-zA-Z\s\-/,]+$', v):
            raise ValueError('Genre contains invalid characters')
        return v.strip().title()

class PredictResponse(BaseModel):
    trending_probability: float = Field(..., description="Trending probability score (0.0 to 1.0)")
    predicted_label: str = Field(..., description="Classification label: trending | not_trending | uncertain")
    model_version: str = Field(..., description="Active model version identifier")
    top_features: List[str] = Field(..., description="Key driving features for this prediction")
    grounded: bool = Field(..., description="Grounded status based on confidence and training vocabulary")
    cold_start: bool = Field(..., description="True if creator/channel was unseen during training, using fallback content model")
    explanation: Dict[str, Any] = Field(..., description="SHAP or Feature Importance explanation metadata")

class TrainResponse(BaseModel):
    job_id: str
    rows_received: int
    status: str

class StatusResponse(BaseModel):
    job_id: str
    status: str  # queued | training | complete | failed
    rows_total: int
    rows_processed: int
    rows_failed: int
    error_message: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    enrichment_api_connected: bool
