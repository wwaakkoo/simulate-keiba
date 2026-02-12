# Project Overview

**Project Name**: Horse Racing Simulation App (simulate-keiba)
**Purpose**: An application to predict horse race results and simulate races using 2D visuals.

## Tech Stack
- **Frontend**: React 19, Vite 7, TypeScript 5.9+, PixiJS 8, React Router v7.
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2, BeautifulSoup4 + httpx (Scraping), scikit-learn + pandas (Prediction).
- **Database**: SQLite.

## Codebase Structure
- `frontend/`: React + PixiJS source code.
- `backend/app/`: FastAPI application code.
  - `api/`: API endpoints.
  - `scraper/`: netkeiba.com scraper.
  - `predictor/`: Machine learning models and features.
  - `models/`: Database models.
- `data/`: Local SQLite database files.
- `docs/`: Project documentation.
