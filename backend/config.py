from dotenv import load_dotenv

load_dotenv()
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_RAW_DIR = os.path.join(DATA_DIR, "raw")
DATA_INTERIM_DIR = os.path.join(DATA_DIR, "interim")
DATA_PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
DATA_EXTERNAL_DIR = os.path.join(DATA_DIR, "external")
SAVED_MODELS_DIR = os.path.join(BASE_DIR, "saved_models")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
OUTPUTS_LOGS_DIR = os.path.join(OUTPUTS_DIR, "logs")
OUTPUTS_METRICS_DIR = os.path.join(OUTPUTS_DIR, "metrics")
OUTPUTS_FORECASTS_DIR = os.path.join(OUTPUTS_DIR, "forecasts")
OUTPUTS_REPORTS_DIR = os.path.join(OUTPUTS_DIR, "reports")
RAW_DATA_FILE = os.path.join(DATA_RAW_DIR, "tourism_country_long.csv")
PROCESSED_CSV = os.path.join(DATA_PROCESSED_DIR, "tourism_features.csv")
EXTERNAL_DATA_GLOB = os.path.join(DATA_EXTERNAL_DIR, "*.xlsx")
INTERIM_RECONCILED_CSV = os.path.join(
    DATA_INTERIM_DIR, "tourism_country_long_reconciled.csv"
)
INTERIM_VALIDATION_REPORT = os.path.join(DATA_INTERIM_DIR, "validation_report.txt")
PROCESSED_TOTAL_CSV = os.path.join(DATA_PROCESSED_DIR, "tourism_total_features.csv")

SEED_COUNTRY_CSV = RAW_DATA_FILE
SEED_NATIONAL_CSV = os.path.join(DATA_RAW_DIR, "tourism_monthly_corrected.csv")
TEST_MONTHS = 12
FORECAST_HORIZON = 12
RANDOM_STATE = 42
MLP_HIDDEN_SIZES = [64, 32]
MLP_LEARNING_RATE = 0.001
MLP_EPOCHS = 2000
MLP_BATCH_SIZE = 16
LR_MODEL_FILENAME = "linear_regression.pkl"
SCALER_FILENAME = "scalers.npz"
SAVED_MODELS_TOTAL_DIR = os.path.join(SAVED_MODELS_DIR, "total")
TOTAL_SCALER_FILENAME = "scalers_total.npz"
TOTAL_LR_MODEL_FILENAME = "linear_regression_total.pkl"
TOTAL_RESULTS_FILENAME = "results_total.json"
SARIMA_ORDER = (1, 1, 1)
SARIMA_SEASONAL_ORDER = (1, 1, 1, 12)
HW_TREND = "add"
HW_SEASONAL = "add"
HW_SEASONAL_PERIODS = 12
API_HOST = "0.0.0.0"
API_PORT = 5000
NOTIFICATION_WEBHOOK_URL = os.environ.get("NOTIFICATION_WEBHOOK_URL", "")
SECRET_KEY = "change-this-to-a-random-secret-in-production"
JWT_SECRET_KEY = "change-this-jwt-secret-in-production"
DATABASE_PATH = os.path.join(BASE_DIR, "tourism.db")

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", "no-reply@tourism-forecast.local")
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").lower() != "false"
OTP_LENGTH = 6
OTP_TTL_SECONDS = 60
OTP_MAX_REQUESTS_PER_WINDOW = int(os.environ.get("OTP_MAX_REQUESTS_PER_WINDOW", "5"))
OTP_REQUEST_WINDOW_SECONDS = int(os.environ.get("OTP_REQUEST_WINDOW_SECONDS", "3600"))

ENABLE_ALERT_SCHEDULER = (
    os.environ.get("ENABLE_ALERT_SCHEDULER", "true").lower() != "false"
)
ALERT_SCAN_INTERVAL_MINUTES = int(os.environ.get("ALERT_SCAN_INTERVAL_MINUTES", "60"))
