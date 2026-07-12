from __future__ import annotations
import numpy as np
import pandas as pd
from forecasting.utils import (
    next_month,
    update_lag_features,
    update_rolling_features,
    update_time_features,
    update_season_flags,
)


class RecursiveForecaster:
    def forecast(
        self,
        model,
        history_df: pd.DataFrame,
        feature_columns: list[str],
        target_column: str,
        horizon: int,
        feature_scaler=None,
        target_scaler=None,
    ) -> np.ndarray:
        last_row = history_df.iloc[-1].to_dict()
        target_history = history_df[target_column].tolist()
        current_date = pd.to_datetime(last_row["date"])
        current_time_index = int(last_row["time_index"])
        predictions = []
        for _ in range(horizon):
            current_date = next_month(current_date)
            current_time_index += 1
            new_row = dict(last_row)
            new_row["date"] = current_date
            new_row.update(update_lag_features(target_history))
            new_row.update(update_rolling_features(target_history))
            new_row.update(update_time_features(current_date, current_time_index))
            new_row.update(update_season_flags(current_date))
            X = np.array([[new_row[column] for column in feature_columns]], dtype=float)
            if feature_scaler is not None:
                X = feature_scaler.transform(X)
            prediction = model.predict(X)
            prediction = np.asarray(prediction).reshape(-1)
            if target_scaler is not None:
                prediction = target_scaler.inverse_transform(
                    prediction.reshape(-1, 1)
                ).flatten()
            value = float(prediction[0])
            predictions.append(value)
            new_row[target_column] = value
            target_history.append(value)
            last_row = new_row
        return np.asarray(predictions)
