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
OUTPUTS_PLOTS_DIR = os.path.join(OUTPUTS_DIR, "plots")
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
DATABASE_PATH = os.path.join(BASE_DIR, "users.db")
