import os

BASE_DIR           = os.path.dirname(os.path.abspath(__file__))
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
SAVED_MODELS_DIR   = os.path.join(BASE_DIR, "saved_models")
PROCESSED_CSV      = os.path.join(DATA_PROCESSED_DIR, "tourism_monthly.csv")

FEATURE_COLS = [
    "month_sin", "month_cos", "year_norm",
    "is_spring_trek", "is_autumn_trek", "is_monsoon", "is_covid",
    "lag_1", "lag_3", "lag_12",
]

TARGET_COL  = "foreign_arrivals"
TEST_MONTHS = 12

MLP_HIDDEN_SIZES  = [64, 32]
MLP_LEARNING_RATE = 0.001
MLP_EPOCHS        = 2000
MLP_BATCH_SIZE    = 16

SARIMA_ORDER          = (1, 1, 1)
SARIMA_SEASONAL_ORDER = (1, 1, 1, 12)

HW_TREND            = "add"
HW_SEASONAL         = "add"
HW_SEASONAL_PERIODS = 12

LR_MODEL_FILENAME = "linear_regression.pkl"

API_HOST       = "0.0.0.0"
API_PORT       = 5000
SECRET_KEY     = "change-this-to-a-random-secret-in-production"
JWT_SECRET_KEY = "change-this-jwt-secret-in-production"
DATABASE_PATH  = os.path.join(BASE_DIR, "users.db")
