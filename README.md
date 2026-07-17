# ATHMOS — Climate Digital Twin (Project Foundation)

Starter scaffold only. No ML models are implemented yet.

## Folder Structure

```
backend/     FastAPI app, routes, placeholder services
frontend/    React + Vite + TailwindCSS dashboard UI
models/      (empty) trained model artifacts go here later
datasets/    (empty) raw/processed climate data goes here later
docs/        (empty) architecture & planning docs
```

## Installation

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Run Commands

### Backend (http://localhost:8000)

```bash
cd backend
uvicorn app:app --reload
```

### Frontend (http://localhost:5173)

```bash
cd frontend
npm run dev
```

## Folder Explanation

- **backend/app.py** — FastAPI entry point, defines `/dashboard`, `/climate`,
  `/forecast`, `/scenario` routes returning dummy JSON.
- **backend/config.py** — App settings (host, port, CORS).
- **backend/services/** — Service layer. `data_loader.py` implements the
  full Climate Data Fusion module (IMD/ERA5/INSAT loaders, missing-value
  handling, spatial/temporal alignment, normalization, NetCDF/NumPy
  persistence, and a PyTorch `ClimateFusionDataset` with train/val split).
  `forecast_service.py` and `scenario_service.py` remain placeholders with
  TODOs for future ML integration.
- **frontend/src/pages/** — Dashboard, Forecast, Scenario pages.
- **frontend/src/components/** — Navbar, Sidebar, Card UI components.
- **frontend/src/api.js** — Fetch wrapper for backend endpoints.
- **models/** — Reserved for trained PyTorch model checkpoints.
- **datasets/** — Reserved for IMD / INSAT-3D / MOSDAC / ERA5 data.
- **docs/** — Reserved for architecture and planning documents.
