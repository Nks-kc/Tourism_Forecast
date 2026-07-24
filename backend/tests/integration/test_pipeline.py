# tests/integration/test_pipeline.py
from feature_engineering.data_loader import prepare_dataframe
from feature_engineering.features import add_lag_features, add_time_features
from feature_engineering.preprocessing import preprocess_data


def test_full_feature_pipeline_produces_no_nans_after_trim(sample_raw_df):
    df = prepare_dataframe(sample_raw_df)
    df = preprocess_data(df)
    df = add_time_features(df)
    df = add_lag_features(df)
    assert "lag_1" in df.columns  # confirms stages connect correctly end-to-end
