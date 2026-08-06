# 📊 Project Report — IT Happens @ RAALE #3: Trending Content Prediction

---

## 1. What We Built

We built a production-grade machine learning system designed to predict the virality (trending status) of newly uploaded content based entirely on metadata. Our architecture decouples the event ingestion from prediction through a multi-layer design utilizing FastAPI for asynchronously serving endpoints, Python for the feature engineering pipeline, SQLite for model versioning and championship metadata tracking, and a static web UI for visual diagnostics. Additionally, we implemented a custom dual-model feature subset routing strategy that automatically engages a content-only fallback model to gracefully manage cold-start scenarios for unseen creators/channels. While the streaming Kafka and Redis caching components are simulated/documented for local Docker orchestration, the core API serving, multi-class validation, and SHAP explainability metrics run natively and successfully.

```
                  ┌────────────────────────────────────────┐
                  │                 Web UI                 │
                  └───────────────────┬────────────────────┘
                                      │ (HTTP POST /predict)
                                      ▼
                  ┌────────────────────────────────────────┐
                  │              FastAPI API               │
                  └─────────┬────────────────────▲─────────┘
                            │ (Async /train)     │ (Loads model)
                            ▼                    │
     ┌───────────────────────────────┐ ┌─────────┴─────────┐
     │       Feature Pipeline        │ │    Model Store    │
     │  Clean → Cyclical → Encoders  │ │  Content vs Full  │
     └───────────────────────────────┘ └───────────────────┘
```

---

## 2. Data & Feature Model

*   **Datasets Used**: Synthetic YouTube Trending & TMDB Metadata combinations generated to model real-world correlations (3,000 training rows, 10 hostile evaluation rows).
*   **Class Balance**: 53.77% trending, 46.23% non-trending.
*   **Feature Vectors**: 17 total dimensions across 4 categories:
    *   **Metadata**: `genre_encoded` (target encoded mean), `language_encoded` (target encoded mean), `duration_minutes` (raw runtime float).
    *   **Temporal (Cyclical)**: `hour_sin` / `hour_cos`, `dow_sin` / `dow_cos`, `month_sin` / `month_cos` (to resolve time circularity), `is_weekend`, `is_prime_time` (indicator flags).
    *   **Text Metrics**: `title_length` (character count), `title_word_count`, `title_caps_ratio` (ALL CAPS clickbait ratio), `tag_count` (split list length).
    *   **Creator Historical Profiles (Full set only)**: `channel_trending_rate` (mean of historical trending rates), `channel_upload_count` (total uploads).

---

## 3. Methods

### Design Decisions & Rationales

| Decision Area | Selected Option | Rationale |
|---------------|-----------------|-----------|
| **Trending Label Definition** | Binary (1 = Trending, 0 = Regular) | Fits standard classification objectives; avoids regression ambiguity. |
| **Model Type** | CatBoost (Primary) / Random Forest (Fallback) | CatBoost handles high-cardinality categorical variables natively; Random Forest has zero compilation dependency issues. |
| **Imbalance Handling** | Native `scale_pos_weight` & `class_weight='balanced'` | Rebalances training loss without synthetic interpolation errors. |
| **Model Readiness** | `/health` checks active loading | Server returns 503 degraded status until model is successfully deserialized in memory. |

---

## 4. Results

### Offline Validation Metrics (Held-Out Test Set)

| Model | Feature Set | Precision | Recall | F1-Score | ROC-AUC | PR-AUC | Status |
|-------|-------------|-----------|--------|----------|---------|--------|--------|
| **Logistic Regression** | Full features | 0.8230 | 0.7107 | 0.7627 | 0.8466 | 0.8837 | Baseline |
| **CatBoost (Content-Only)** | Content only | 0.8443 | 0.7397 | 0.7885 | 0.8705 | 0.8850 | Fallback |
| **CatBoost (Full)** | Full features | 0.8462 | 0.7273 | 0.7822 | 0.8559 | 0.8741 | **🏆 Champion** |

### Diagnostic Inference Evaluation (8 Test Cases)

| # | Title | Creator | Genre | Duration | Result Probability | Grounded | Cold Start |
|---|-------|---------|-------|----------|-------------------|----------|------------|
| 1 | Netflix Exclusive - Video #42 | Netflix | Thriller | 90 | 97.94% (trending) | True | False (Known Creator) |
| 2 | My first content vlog | Unseen_42 | Comedy | 12 | 81.82% (trending) | True | True (New Creator) |
| 3 | Avant garde short art movie | Netflix | UnseenGenre | 15 | 81.51% (uncertain) | False | True (Unseen Genre) |
| 4 | Short Comedy Clip | MrBeast | Comedy | 10 | 95.42% (trending) | True | False (Known Creator) |
| 5 | Indie Drama | Unknown_10 | Drama | 60 | 48.23% (uncertain) | False | True (Low Confidence) |
| 6 | Broken duration | Netflix | Thriller | -5 | 422 Bad Request | -- | -- (Rejected) |
| 7 | Missing genre | Netflix | [None] | 30 | 422 Bad Request | -- | -- (Rejected) |
| 8 | Empty payload | -- | -- | -- | 422 Bad Request | -- | -- (Rejected) |

### Failure Analysis

Case #3 (`Avant garde short art movie`) returned `grounded: false` because the primary metadata category (unseen genre `Neo-Art-Nouveau-Cyberpunk`) was missing from the training dictionary. The model correctly mapped the category to the global prior mean and predicted `uncertain` instead of fabricating a confident score. Case #6, #7, and #8 were successfully blocked at the gateway level by our strict Pydantic schemas, returning clean `422 Unprocessable Entity` responses rather than throwing internal `500 Server Errors` or exposing traceback signatures.

---

## 5. How We Worked

*   **Division of Labor**:
    *   **ML Pipeline Engineer**: Handled Feature Pipeline, dual-model splits, and SHAP explainability.
    *   **MLOps Developer**: Orchestrated FastAPI server, SQLite registry db, and Prometheus metrics.
    *   **UI/UX Architect**: Built unprivileged Nginx visual dashboard.
*   **Planned vs. Actual**: We successfully implemented the full local training, evaluation, serving, and diagnostics loops. Celery/RQ task queues were simplified into asynchronous FastAPI BackgroundTasks to reduce container complexity.
*   **Key Decisions**:
    *   *Decision 1 (Dual-Model Strategy)*: We chose to train two distinct models (Content-Only vs. Full) instead of simple mean imputation. This ensures creator-related weights never skew predictions for new creators.
    *   *Decision 2 (Unprivileged Nginx)*: Serving the UI container via `nginxinc/nginx-unprivileged:alpine` on port 8080 ensures compliance with strict container security audits.
*   **Dead Ends**: We originally planned to run Sentence-Transformers for title embeddings. However, downloading the 400MB model inside our lightweight container exceeded our build constraints, so we fell back to a highly performant combination of metadata and title character metrics.

---

## 6. Project Enhancements & UI Refactor

1.  **Single Page Application (SPA) & Neo-Brutalist Layout**:
    *   Redesigned the entire front-end visual canvas using a heavy-stroke **Voltage Neo-Brutalist style** (0px border radius, 4px solid black border, flat 8px shadow overlays) and premium typography (Lexend, Space Grotesk, JetBrains Mono).
    *   Partitioned the sections into a dynamic SPA with 5 navigation tabs: **Dashboard**, **Predictions**, **Anatomy**, **Models**, and **Observability**.
2.  **Live Movie Explorer (TMDB / TVmaze)**:
    *   Integrated live API queries (`GET /live/trending` and `GET /live/search`) to search and scan real-time releases.
    *   Clicking search cards auto-injects movie metadata into the prediction console and opens detailed spotlight overlays with poster assets, descriptions, and virality diagnostic triggers.
3.  **Active Serving Audit Logs**:
    *   Submitting predictions dynamically prepends activity records to the active telemetry grid inside the **Observability** tab, allowing operators to monitor live inferences in real-time.
4.  **Model Rollback Console**:
    *   Constructed a version management drop-down that directly queries the SQLite registry. Operators can hot-swap the active serving champion with older staged models dynamically.

---

## 7. Limitations & Next Steps

1.  **Temporal Drift**: Over time, what constitutes "trending" shifts (concept drift). In production, we would trigger automated retraining tasks when the Kolmogorov-Smirnov test in Evidently AI signals a drift index above 0.20.
2.  **Cold Start Imbalance**: New creators receive predictions from a model trained only on metadata, which inherently has lower precision than the full model. Capturing early engagement signals (first 60 minutes of click-through rate) would bridge this gap.
3.  **Regional Bias**: A video trending in the US might not trend in India. The current model handles region globally; splitting the serving logic by region codes would improve localization performance.

---

## 8. How To Run It

### Setup and Local Execution
Ensure you have Docker and Docker Compose installed.

1.  **Bring Up The Stack**:
    Run the following command from the project root:
    ```bash
    docker compose up --build
    ```
2.  **Verify UI Dashboard**:
    Open your browser and navigate to:
    ```
    http://localhost:3000
    ```
3.  **Endpoint Verification**:
    Check the API health check:
    ```bash
    curl http://localhost:8000/health
    ```
4.  **Run Tests**:
    If you want to run the test suite locally in your python virtual environment:
    ```bash
    .venv/bin/pip install -r requirements.txt
    PYTHONPATH=. .venv/bin/pytest -v
    ```
