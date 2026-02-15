# Phase G-1: Walk-Forward Validation Implementation Plan

## Goal
Address the "Concept Drift" issue where the model performance degrades over time. Instead of a simple Train/Test split, implement **Walk-Forward Validation** to accurately simulate real-world model performance and periodic retraining.

## User Review Required
- **Validation Period**: 2023-01-01 to 2025-12-31
- **Train Window**: Initial 24 months (or 18 months), rolling or expanding? -> User suggested rolling/sliding.
- **Test Window**: 3 months
- **Step Size**: 3 months

## Proposed Changes

### 1. New Validator Class (`backend/app/predictor/validation.py`)
- Create `WalkForwardValidator` class.
- Methods:
    - `split(df)`: Generates (train_idx, test_idx) pairs based on time.
    - `cross_validate(df)`: Runs the training and evaluation loop.
    - `_train_model(...)`: Standard LightGBM training (using LambdaRank).
    - `_evaluate(...)`: Calculates Metrics (NDCG, Win Rate, ROI).

### 2. Update Training Script (`backend/train_model.py` or new script)
- Create `evaluate_walk_forward.py` to run this validation specifically.
- Load all available historical data.
- Run validation and output the "True ROI" properly.

### 3. Features
- Ensure `FeatureFactory` is used or pre-computed features are loaded efficiently (Walk-Forward can be slow if features are re-calculated, but with 3-month steps it should be manageable).

## Verification Plan
1.  Run `evaluate_walk_forward.py`.
2.  Check if ROI remains stable across folds found in 2024 vs 2025.
3.  Confirm that retraining improves 2025 performance compared to the static model.

## Phase G-2: Incremental Learning
### 1. New Class (`backend/app/predictor/retraining.py`)
- `IncrementalRetrainer`: Handles periodic retraining with time-decay sample weights.
- `train_for_date(current_date, lookback_months)`: Trains a model using data prior to `current_date`.

### 2. CLI Script (`backend/retrain_model.py`)
- Allows manual triggering of retraining.

## Phase G-3: Drift Detection
### 1. New Class (`backend/app/predictor/drift_detection.py`)
- `DriftDetector`: Monitors daily accuracy against a baseline.
- `check_drift()`: Alerts if performance drops below threshold.

## Phase G-4: Variance Reduction
### 1. Update Strategy (`backend/app/predictor/betting.py`)
- Added `VarianceReductionStrategy` class.
- Supports:
    - `low_variance`: Odds <= 3.0, EV > 1.3
    - `high_volume`: EV > 1.15, Top 3 picks
    - `diversified`: Win + Place + Wide logic
