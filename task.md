
# Phase F: Advanced Features & Betting Strategy Optimization

## F-1: Advanced Feature Engineering
- [x] Implement Speed Index Calculator
    - [x] Create `SpeedIndexCalculator` class
    - [x] Implement base time calculation (median of winning times)
    - [x] Implement speed index calculation logic
    - [x] Implement pace adjustment logic
    - [x] Add time trend features (rolling mean, max, improvement rate)
- [x] Implement Dark Horse Features
    - [x] Add "Comeback from defeat" flag
    - [x] Add Class change features (promotion/demotion)
    - [x] Add Odds/Popularity divergence
    - [x] Add Rest/Layoff flag
    - [x] Add Pace suitability flag
- [ ] Implement Pedigree Encoding (Future/Optional)
    - [ ] Research fastText/Node2Vec for pedigree

## F-2: Dark Horse Model & Hybrid Prediction
- [x] Create `DarkHorseModel` class (Integrated in Trainer)
    - [x] Define hole horse label (e.g., Pop >= 6 & Rank <= 3)
    - [x] Configure LightGBM parameters for imbalanced data (focal loss/class weights)
    - [x] Implement training pipeline for Dark Horse model
- [x] Implement Hybrid Prediction Logic
    - [x] Combine Main Model (Win probability/Rank) and Dark Horse Model (Hole probability)
    - [x] Suggest bet combinations based on hybrid scores

## F-3: Betting Strategy Optimization
- [x] Implement Probability Calibration
    - [x] Use `CalibratedClassifierCV` or `IsotonicRegression`
    - [x] Calibrate ranking scores to actual probabilities
    - [x] Implement Kelly Criterion Strategy
    - [x] Create `KellyBettingStrategy` class
    - [x] Implement optimal bet sizing formula
    - [x] Implement expected value (EV) filtering (with confidence check)
    - [x] Implement Safe Kelly Strategy (Drawdown limit, Min Prob 10%)
    - [x] Implement Race Anomaly Detection (Flat Distribution Check)
    - [x] Fix Prediction Sorting and Ranking (Backend)
- [x] Implement Simulation & Backtesting
    - [x] Update backtesting tools to use Kelly Strategy
    - [x] Compare ROI with flat betting (Result: ~47% Recovery Rate, needs tuning)

## F-4: System Integration & Evaluation
- [x] Integrate new features into `FeatureEngineering` pipeline
- [x] Update `Predictor` to use new models
- [ ] Run comprehensive evaluation on 2024-2025 data
- [ ] Documentation update
## Phase G: Model Improvement & Stabilization (Concept Drift Countermeasures)
- [x] G-1: Implement Walk-Forward Validation
    - [x] Create `WalkForwardValidator` class
    - [x] Implement time-series split logic
    - [x] Run evaluation on 2023-2025 data
- [x] G-1.5: Collect 2025 Data (Address Data Sparsity)
    - [x] Run scraper for 2025-01 to 2025-12 (Partial: Jan 2025 Complete)
    - [x] Verify data count in DB (643 races in Jan)
- [x] G-2: Implement Incremental Learning (Retraining)
    - [x] Create `IncrementalRetrainer` class
    - [x] Implement monthly retraining logic (via script)
    - [x] Implement time-decay weighting
- [x] G-3: Drift Detection & Monitoring
    - [x] Create `DriftDetector` class
    - [x] Implement baseline performance setting
    - [x] Implement daily drift monitoring
- [x] G-4: Variance Reduction & Tuning
    - [x] Implement low-variance betting strategy (Lower odds focus)
    - [x] Implement high-volume strategy (Wider EV tolerance)
    - [x] Implement high-volume strategy (Wider EV tolerance)
    - [x] Implement diversified betting (Win/Place/Wide)
- [x] G-5: Rigorous Verification (Statistical Significance)
    - [x] Expand validation period (Oct 2024 - Jan 2025) to ensure sufficient sample size
    - [x] Implement Monte Carlo simulation for chance verification
    - [x] Calculate 95% confidence intervals for ROI
    - [x] Verify Lookahead Bias (Strict audit of feature timestamps)
    - **Result**: High Volume (3145 bets, +18.4% ROI) is promising but 95% CI is [-13.9%, +54.1%]. Need ~1000 more bets for statistical significance. Low Variance sample is too small.

## Phase 5: Polish & UI Revamp (Phase 5-alpha: Paper Trading Mode)
- [ ] Implement Simulation UI with Strategy Selection
- [ ] Add "Paper Trading" Mode (Virtual Betting)
    - [ ] Display Warning Banner (Statistical Significance Not Reached)
    - [ ] Visualize ROI / Confidence Interval
- [ ] Background Data Collection & Verification (Continue until N > 4000)
