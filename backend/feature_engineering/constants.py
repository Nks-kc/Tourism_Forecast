from __future__ import annotations

DATE_COLUMN = "date"
YEAR_COLUMN = "year"
MONTH_COLUMN = "month"
COUNTRY_COLUMN = "country"
TARGET_COLUMN = "arrivals"
REQUIRED_COLUMNS = [
    DATE_COLUMN,
    YEAR_COLUMN,
    MONTH_COLUMN,
    COUNTRY_COLUMN,
    TARGET_COLUMN,
]
LAG_MONTHS = [1, 2, 3, 12]
ROLLING_WINDOWS = [3, 6]
MONTHS_IN_YEAR = 12
COVID_START = "2020-03-01"
COVID_END = "2022-02-01"
SPRING_MONTHS = [3, 4, 5]
AUTUMN_MONTHS = [9, 10, 11]
MONSOON_MONTHS = [6, 7, 8]
WINTER_MONTHS = [12, 1, 2]
MIN_ARRIVALS = 0
ALLOW_DUPLICATES = False
ALLOW_NEGATIVE_VALUES = False
COUNTRY_PREFIX = "country"
DROP_FIRST_COUNTRY = False
BASE_FEATURES = [
    "month_sin",
    "month_cos",
    "time_index",
    "is_covid",
    "is_spring_trek",
    "is_autumn_trek",
    "is_monsoon",
]
LAG_FEATURES = [f"lag_{lag}" for lag in LAG_MONTHS]
ROLLING_FEATURES = []
for window in ROLLING_WINDOWS:
    ROLLING_FEATURES.append(f"rolling_mean_{window}")
    ROLLING_FEATURES.append(f"rolling_std_{window}")
TIME_FEATURES = ["month_sin", "month_cos", "time_index"]
SEASON_FLAG_COLUMNS = ["is_spring_trek", "is_autumn_trek", "is_monsoon", "is_covid"]
FEATURE_COLUMNS = BASE_FEATURES + LAG_FEATURES + ROLLING_FEATURES
