# Smart Emergency Response & Accident Severity Prediction System

Roadwise is a local, educational road-accident analytics and severity classification prototype. It provides a React dashboard, interactive analytics, a single-record prediction form, CSV batch prediction, model evaluation, and downloadable reports.

> **Important:** Accident records are generated synthetic data, not official historical records. Model scores and predictions are for coursework demonstration only. This application is not an emergency dispatch system, does not identify real emergencies, and cannot guarantee real-world accident outcomes.

## Project summary

This project demonstrates a full data science application workflow: generate structured data locally, preprocess mixed numeric and categorical features with a Scikit-learn pipeline, train a Random Forest classifier, evaluate it on a stratified holdout set, and make the saved model available through a Flask API and React web interface.

### Problem statement and objectives

Road conditions, visibility, traffic, and vehicle characteristics can be explored as factors associated with accident severity. The project aims to:

- Build a reproducible synthetic accident dataset without paid APIs or manual collection.
- Explore severity patterns through interactive charts and filters.
- Demonstrate model training and actual held-out evaluation metrics.
- Predict severity classes for user-provided feature values and CSV rows.
- Present results with clear limitations and a student-friendly setup.

## Technology

- **Frontend:** React, Vite, JavaScript, Tailwind CSS, Recharts, Lucide React, Axios
- **Backend:** Python, Flask, Flask-CORS, Pandas, NumPy
- **Machine learning:** Scikit-learn preprocessing pipeline, Random Forest, Joblib
- **Report:** ReportLab-generated PDF summary

## Project structure

```text
.
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── generate_dataset.py
│   ├── train_model.py
│   ├── requirements.txt
│   ├── tests/
│   └── models/                  # created after training
├── data/                        # generated on first run
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── services/api.js
│   ├── .env.example
│   └── package.json
└── README.md
```

## Synthetic dataset

`backend/generate_dataset.py` creates 120,000 reproducible synthetic records with a fixed seed and saves them to `data/accidents.csv`. Severity has these consistent labels:

| Label | Category |
|---:|---|
| 1 | Fatal |
| 2 | Serious Injury |
| 3 | Minor Injury |
| 4 | Property Damage Only |

The script validates expected fields, numeric bounds, severity labels, missing values, and accident ID uniqueness. If the CSV already exists, it will **not overwrite it**. The four labels are balanced using quantile cutoffs on a noisy score based on multiple conditions, rather than a direct rule on one input field. Casualty counts are generated independently of the target label. The generated geography and patterns are illustrative and must not be interpreted as official or real-world data; this is not a validated accident-risk model.

## Machine-learning workflow

`backend/train_model.py` verifies required columns, excludes identifiers and target-leaking fields from training, uses a stratified 80/20 split, imputes missing values, scales numeric inputs, one-hot encodes categories, and fits a Random Forest classifier. The complete fitted pipeline is saved to `backend/models/accident_severity_model.joblib`; actual evaluation metrics are saved to `backend/models/model_metrics.json`.

Metrics include accuracy, macro precision/recall/F1, weighted F1, confusion matrix, per-class scores, and training/test record counts. The browser only displays values loaded from that evaluation file; it does not show hardcoded model scores.

## Windows setup and run

Open two PowerShell terminals in the workspace.

### 1. Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python generate_dataset.py
python train_model.py
python app.py
```

The API starts at `http://127.0.0.1:5000`. If PowerShell blocks environment activation, call the virtual environment Python directly:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe generate_dataset.py
.\venv\Scripts\python.exe train_model.py
.\venv\Scripts\python.exe app.py
```

The API also binds to `0.0.0.0` and uses the `PORT` environment variable when supplied by a hosting provider.

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the local Vite URL (normally `http://127.0.0.1:5173`). The frontend defaults to the local Flask API. To configure it, copy `.env.example` to `.env.local` and set `VITE_API_URL`, for example:

```text
VITE_API_URL=http://127.0.0.1:5000/api
```

No secret keys are required. If the dataset/model has not been generated/trained, the API responds with an actionable error instead of fabricated data.

## Features

- Dashboard summary cards and six chart views, with severity/weather/road/date filtering
- Accident analytics with comparison charts, searchable and paginated records, and filtered CSV export
- Single-record prediction with validation, class probability bars, and an educational-use disclaimer
- Batch prediction of up to 5,000 CSV rows (10 MB maximum), with a results preview and downloadable CSV
- Model evaluation metrics and confusion matrix from the saved training evaluation
- Data dimensions, missing-value counts, duplicate count, severity distribution, and a sample
- Dataset CSV download, filtered PDF summary export, and confirmed synthetic data regeneration with timestamped backups
- Responsive navigation and clear loading, empty, and error states

Batch CSV files must include the 15 model input columns used by the prediction form. An uploaded `severity` column is not required and is never passed to the model. If included, it remains only as an original column in the results file.

## API endpoints

All endpoints are under `/api`.

| Method | Route | Description |
|---|---|---|
| GET | `/health` | Backend and artifact availability |
| GET | `/dashboard` | Summary statistics and dashboard chart counts; supports severity, weather, road type, date_from, date_to |
| GET | `/analytics` | Filtered analytics and paginated/searchable records |
| POST | `/predict` | JSON single-record prediction with probabilities |
| POST | `/batch-predict` | Multipart CSV prediction; form field name `file` |
| GET | `/model-metrics` | Actual saved holdout evaluation |
| GET | `/data-summary` | Dataset dimensions, quality counts, and sample |
| GET | `/download-dataset` | Original dataset CSV |
| GET | `/export-csv` | Download filtered accident CSV |
| GET | `/export-report` | Generate a PDF summary of filtered records and available model metrics |
| POST | `/regenerate-demo` | Confirmed demo dataset replacement; requires JSON `{"confirmation":"REPLACE SYNTHETIC DATA"}` |

Prediction categorical values and numeric bounds are shared conceptually between the model contract and UI. The API rejects missing required columns, invalid category values, and out-of-range numeric values. When regenerating, the existing CSV and model artifacts are backed up; the model artifacts are then invalidated and must be retrained.

## Tests and build

From the workspace root:

```powershell
python -m unittest discover -s backend\tests
```

Frontend production build:

```powershell
cd frontend
npm run build
```

After starting the backend, check `http://127.0.0.1:5000/api/health`, then try the dashboard, prediction form, metrics page, and a CSV upload in the browser.

## Troubleshooting

- **Dataset missing:** from `backend`, run `python generate_dataset.py`.
- **Model not trained / metrics unavailable:** from `backend`, run `python train_model.py` after dataset generation.
- **Backend unavailable in the UI:** ensure `python app.py` is still running and check `VITE_API_URL`.
- **PowerShell activation blocked:** use the virtual environment's `python.exe` commands shown above.
- **CSV rejected:** check for all 15 required feature headers, accepted categorical values, valid numeric ranges, a `.csv` extension, and the 10 MB / 5,000-row upload limits.
- **Port is already in use:** stop the other application using port 5000 or set `PORT` to an available port and update `VITE_API_URL`.

## Screenshots

Add genuine screenshots captured from the running local application here before submission, for example:

```text
![Dashboard screenshot](docs/screenshots/dashboard.png)
![Model evaluation screenshot](docs/screenshots/model-evaluation.png)
```

Do not use mock screenshots or present synthetic patterns as real observations.

## College submission and viva notes

**Short summary:** Roadwise is a full-stack educational prototype that generates synthetic accident records, visualizes descriptive patterns, and predicts one of four severity categories with a trained Scikit-learn Random Forest pipeline. A Flask API connects the model and dataset to a React dashboard. Evaluation values are computed on a held-out test split.

**Workflow for a viva:** First, a fixed random seed produces a reproducible synthetic CSV. Next, the training script validates its input, separates features and label, creates a stratified train/test split, preprocesses numeric and categorical columns, fits the classifier, and saves both the pipeline and actual evaluation results. The Flask API loads the saved pipeline for predictions and computes descriptive summaries from the CSV. React requests those endpoints and presents the returned statistics, charts, predictions, and exports.

## Limitations and future enhancements

Synthetic records cannot establish real-world accident patterns or model utility. The features and synthetic label-generation logic are illustrative, held-out performance on generated data does not establish real-world validity, and no causal inference is performed. Possible future work includes carefully governed official data, external validation, fairness and calibration studies, model monitoring, richer geography, and deployment security hardening.

## Optional deployment

Deployment is optional; verify local operation first.

- **Render backend:** create a Python web service with root directory `backend`, build command `pip install -r requirements.txt`, and start command `python app.py`. Set `CORS_ORIGINS` to the exact deployed frontend origin. The service needs writable persistent storage for generated data and model artifacts; if its filesystem is ephemeral, regenerate/retrain during deployment or use a persistent disk.
- **Vercel frontend:** set the project root to `frontend`, build command `npm run build`, output directory `dist`, and environment variable `VITE_API_URL` to the deployed backend's `/api` URL. Add a Vercel rewrite for SPA routing if deep links are introduced.

Do not add real credentials or paid service keys to this project.
