# Tourism_Forecast

Backend API and simple frontend for forecasting monthly tourism arrivals.

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

After starting the backend, open:

```text
http://localhost:5000/
```

You can also open the static file directly:

```text
frontend/index.html
```

Authentication pages:

```text
http://localhost:5000/login.html
http://localhost:5000/register.html
```

The frontend expects the API base URL to be `http://localhost:5000`.
