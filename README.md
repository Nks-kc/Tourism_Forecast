# Nepal Tourism Forecast

> A full-stack machine learning dashboard for forecasting monthly foreign tourist arrivals to Nepal — with per-country breakdowns, seasonal analytics, and multi-model comparison.

---

## Features

- **4 Forecasting Models** — MLP Neural Network, SARIMA, Holt-Winters, and Linear Regression
- **19 Source Countries** — Per-country model training and prediction
- **Interactive Dashboard** — Year-over-year charts, seasonal donut charts, monthly averages
- **Adjustable Horizon** — Forecast 1, 3, 6, or 12 months ahead
- **JWT Authentication** — Secure login/register with token-based access
- **Dark / Light Theme** — Persistent theme toggle
- **Model Evaluation** — MAE, RMSE, MAPE metrics saved and served via API
- **HTML Report Generation** — Auto-generated comparison reports after training

---

## Project Structure

```
Tourism_Forecast/
├── backend/
│   ├── api.py                  # Flask REST API (all routes)
│   ├── train.py                # Training pipeline for all models
│   ├── predict.py              # Total-series prediction logic
│   ├── retrain_hw.py           # Holt-Winters retrain utility
│   ├── config.py               # All paths and hyperparameters
│   ├── auth/                   # JWT auth (models + routes)
│   ├── models/                 # ML model wrappers
│   │   ├── mlp.py              # Multi-Layer Perceptron (NumPy)
│   │   ├── sarima_model.py     # SARIMA (statsmodels)
│   │   ├── holtwinters_model.py# Holt-Winters (statsmodels)
│   │   └── linear_regression_model.py
│   ├── evaluation/             # Metrics, plotting, comparison, reports
│   ├── feature_engineering/    # Data loading, feature extraction, seasonality
│   ├── forecasting/            # Forecast engine + caching utilities
│   ├── data/
│   │   └── raw/                # tourism_country_long.csv (source data)
│   └── saved_models/           # Trained model artifacts (gitignored)
│       ├── holtwinters/        # Per-country .pkl files
│       ├── sarima/             # Per-country .pkl files
│       └── total/              # Nationwide aggregate models
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Root component & state management
│   │   ├── styles.css          # Full design system (dark/light)
│   │   ├── components/         # 17 UI components
│   │   │   ├── LoginPage.jsx
│   │   │   ├── Header.jsx
│   │   │   ├── Nav.jsx
│   │   │   ├── HistoryPanel.jsx
│   │   │   ├── ForecastPanel.jsx
│   │   │   ├── CountryExplorer.jsx
│   │   │   ├── ModelsPanel.jsx
│   │   │   ├── YoYChart.jsx
│   │   │   ├── SeasonalDonutChart.jsx
│   │   │   ├── MonthlyAverageChart.jsx
│   │   │   ├── ModelComparisonChart.jsx
│   │   │   └── ...
│   │   └── lib/
│   │       ├── api.js          # API client (fetch wrappers)
│   │       └── chartTheme.js   # Chart.js theme config
│   └── index.html
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Models

| Model | Type | Description |
|---|---|---|
| **MLP** | Neural Network | 2-hidden-layer perceptron (64→32), trained with MSE loss over 2000 epochs |
| **SARIMA** | Statistical | Seasonal ARIMA `(1,1,1)(1,1,1,12)` with exogenous trekking season flags |
| **Holt-Winters** | Statistical | Additive trend + additive seasonal smoothing, period=12 |
| **Linear Regression** | Classical ML | Regularized regression with seasonal and lag features |

Models are evaluated on a **12-month held-out test set** using:
- **MAE** — Mean Absolute Error
- **RMSE** — Root Mean Squared Error
- **MAPE** — Mean Absolute Percentage Error

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3, Flask, Flask-CORS |
| **ML / Stats** | NumPy, pandas, scikit-learn, statsmodels |
| **Auth** | JWT (PyJWT), SQLite |
| **Frontend** | React 19, Chart.js, Vite |
| **Styling** | Vanilla CSS (dark/light design system) |

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Nks-kc/Tourism_Forecast.git
cd Tourism_Forecast
```

### 2. Set Up the Python Backend

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate       # Linux / macOS
# .venv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Place the Dataset

Put your source CSV in:

```
backend/data/raw/tourism_country_long.csv
```

Expected columns: `date`, `country`, `arrivals`

### 4. Train the Models

```bash
cd backend
python train.py
```

This will:
- Train all 4 models × 2 series (per-country + total)
- Save model artifacts to `backend/saved_models/`
- Generate evaluation plots, metrics JSON, and an HTML comparison report in `backend/outputs/`

### 5. Start the API Server

```bash
cd backend
python api.py
# API running at → http://localhost:5000
```

### 6. Start the Frontend (Dev Mode)

```bash
cd frontend
npm install
npm run dev
# Frontend running at → http://localhost:5173
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | ❌ | API health check |
| `POST` | `/auth/register` | ❌ | Register a new user |
| `POST` | `/auth/login` | ❌ | Login and receive JWT token |
| `GET` | `/history` | ❌ | Nationwide arrival history (filterable by year & season) |
| `GET` | `/countries` | ❌ | List all available source countries |
| `GET` | `/history/country` | ❌ | Per-country historical arrivals |
| `POST` | `/predict` | ✅ | Nationwide forecast (horizon: 1/3/6/12 months) |
| `POST` | `/predict/country` | ✅ | Per-country forecast from all 4 models |
| `GET` | `/evaluate` | ✅ | Total-series model evaluation metrics |
| `GET` | `/evaluate/country` | ✅ | Per-country evaluation metrics |
| `GET` | `/compare` | ✅ | Model comparison summary |
| `POST` | `/admin/reload` | ❌ | Clear in-memory model cache after retraining |

---

## Notes on Model Files

Trained model files (`*.pkl`, `*.npz`) are **not committed to git** because:
- They are large and environment-specific
- They can be regenerated by running `python train.py`
- Pickle files are not portable across Python versions

---


