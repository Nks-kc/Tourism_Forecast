# Tourism_Forecast

Backend API and React frontend for forecasting monthly tourism arrivals.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Backend

```bash
python backend/api.py
```

The API runs at:

```text
http://localhost:5000
```

## Run Frontend

The frontend is a Vite React app. In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173/
```

The Vite dev server proxies API calls to the Flask backend at `http://localhost:5000`.

## Build Frontend For Flask

To serve the built frontend from Flask:

```bash
cd frontend
npm run build
cd ..
python backend/api.py
```

Then open:

```text
http://localhost:5000/
```

The React app includes dashboard, history, forecast, model comparison, login, and registration views.
