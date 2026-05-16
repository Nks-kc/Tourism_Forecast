import os
import json
import numpy as np

from models.mlp                     import MLP
from models.sarima_model            import SARIMAModel
from models.holtwinters_model       import HoltWintersModel
from models.linear_regression_model import LinearRegressionModel
from utils.feature_engineering      import prepare_data, inverse_scale_target
from config import (
    SAVED_MODELS_DIR, MLP_HIDDEN_SIZES, MLP_LEARNING_RATE,
    MLP_EPOCHS, MLP_BATCH_SIZE, FEATURE_COLS, LR_MODEL_FILENAME,
)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    y_true  = y_true.flatten()
    y_pred  = y_pred.flatten()
    mae     = float(np.mean(np.abs(y_true - y_pred)))
    rmse    = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    nonzero = y_true != 0
    mape    = float(np.mean(np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])) * 100)
    return {"MAE": round(mae, 2), "RMSE": round(rmse, 2), "MAPE": round(mape, 2)}


def main():
    os.makedirs(SAVED_MODELS_DIR, exist_ok=True)

    print("\n" + "=" * 60)
    print("  TOURISM FORECAST — TRAINING ALL MODELS")
    print("=" * 60)

    print("\n[Step 1/5]  Loading and preparing data...")
    data = prepare_data()

    X_train     = data["X_train"]
    y_train     = data["y_train"]
    X_test      = data["X_test"]
    y_test      = data["y_test"]
    tgt_scaler  = data["tgt_scaler"]
    train_df    = data["train_df"]
    test_df     = data["test_df"]
    y_train_raw = train_df["foreign_arrivals"].values
    y_test_raw  = test_df["foreign_arrivals"].values
    results     = {}

    print(f"\n[Step 2/5]  Training MLP...")
    mlp = MLP(input_size=len(FEATURE_COLS), hidden_sizes=MLP_HIDDEN_SIZES, learning_rate=MLP_LEARNING_RATE)
    history = mlp.train(X_train, y_train, epochs=MLP_EPOCHS, batch_size=MLP_BATCH_SIZE, val_data=(X_test, y_test), verbose=True)
    y_pred_mlp = inverse_scale_target(mlp.predict(X_test), tgt_scaler).flatten()
    mlp.save(os.path.join(SAVED_MODELS_DIR, "mlp.npz"))
    np.savez(os.path.join(SAVED_MODELS_DIR, "scalers.npz"),
             feat_mean=data["feat_scaler"]["mean"], feat_std=data["feat_scaler"]["std"],
             tgt_mean=np.array([tgt_scaler["mean"]]), tgt_std=np.array([tgt_scaler["std"]]))
    results["MLP"] = compute_metrics(y_test_raw, y_pred_mlp)

    print(f"\n[Step 3/5]  Training SARIMA...")
    exog_cols   = ["is_spring_trek", "is_autumn_trek", "is_monsoon", "is_covid"]
    sarima      = SARIMAModel()
    sarima.fit(y_train_raw, exog_train=train_df[exog_cols].values)
    y_pred_sarima = sarima.predict(steps=len(y_test_raw), exog_future=test_df[exog_cols].values)
    sarima.save(os.path.join(SAVED_MODELS_DIR, "sarima.pkl"))
    results["SARIMA"] = compute_metrics(y_test_raw, y_pred_sarima)

    print(f"\n[Step 4/5]  Training Holt-Winters...")
    hw = HoltWintersModel()
    hw.fit(y_train_raw)
    y_pred_hw = hw.predict(steps=len(y_test_raw))
    hw.save(os.path.join(SAVED_MODELS_DIR, "holtwinters.pkl"))
    results["Holt-Winters"] = compute_metrics(y_test_raw, y_pred_hw)

    print(f"\n[Step 5/5]  Training Linear Regression with Lag Features...")
    lr = LinearRegressionModel()
    lr.fit(X_train, y_train, feature_names=FEATURE_COLS)
    y_pred_lr = inverse_scale_target(lr.predict(X_test), tgt_scaler).flatten()
    lr.save(os.path.join(SAVED_MODELS_DIR, LR_MODEL_FILENAME))
    results["Linear Regression"] = compute_metrics(y_test_raw, y_pred_lr)

    print("\n" + "=" * 60)
    print("  RESULTS  —  Test set (last 12 months)")
    print("=" * 60)
    print(f"  {'Model':<22} {'MAE':>12} {'RMSE':>12} {'MAPE':>8}")
    print(f"  {'-'*58}")
    for name, m in results.items():
        print(f"  {name:<22} {m['MAE']:>12,.0f} {m['RMSE']:>12,.0f} {m['MAPE']:>7.2f}%")

    with open(os.path.join(SAVED_MODELS_DIR, "results.json"), "w") as f:
        json.dump(results, f, indent=2)
    with open(os.path.join(SAVED_MODELS_DIR, "mlp_history.json"), "w") as f:
        json.dump(history, f)

    print(f"\n  All models saved to: {SAVED_MODELS_DIR}/")
    print(f"  Run the API:  python api.py")


if __name__ == "__main__":
    main()
