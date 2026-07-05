"""
Global configuration for the Tourism Forecasting backend.
"""

import os

# =============================================================================
# Base Directories
# =============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")

DATA_RAW_DIR = os.path.join(DATA_DIR, "raw")
DATA_INTERIM_DIR = os.path.join(DATA_DIR, "interim")
DATA_PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
DATA_EXTERNAL_DIR = os.path.join(DATA_DIR, "external")

SAVED_MODELS_DIR = os.path.join(BASE_DIR, "saved_models")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

# =============================================================================
# Dataset Files
# =============================================================================

RAW_DATA_FILE = os.path.join(
    DATA_RAW_DIR,
    "tourism_country_long.csv",
)

PROCESSED_CSV = os.path.join(
    DATA_PROCESSED_DIR,
    "tourism_features.csv",
)

# =============================================================================
# Train / Test
# =============================================================================

TEST_MONTHS = 12

FORECAST_HORIZON = 12

RANDOM_STATE = 42

# =============================================================================
# MLP (NumPy)
# =============================================================================

MLP_HIDDEN_SIZES = [64, 32]

MLP_LEARNING_RATE = 0.001

MLP_EPOCHS = 2000

MLP_BATCH_SIZE = 16

# =============================================================================
# Linear Regression
# =============================================================================

LR_MODEL_FILENAME = "linear_regression.pkl"

# =============================================================================
# SARIMA
# =============================================================================

SARIMA_ORDER = (1, 1, 1)

SARIMA_SEASONAL_ORDER = (1, 1, 1, 12)

# =============================================================================
# Holt-Winters
# =============================================================================

HW_TREND = "add"

HW_SEASONAL = "add"

HW_SEASONAL_PERIODS = 12

# =============================================================================
# Flask API
# =============================================================================

API_HOST = "0.0.0.0"

API_PORT = 5000

SECRET_KEY = "change-this-to-a-random-secret-in-production"

JWT_SECRET_KEY = "change-this-jwt-secret-in-production"

DATABASE_PATH = os.path.join(BASE_DIR, "users.db")
