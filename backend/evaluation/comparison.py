from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List
from config import SAVED_MODELS_DIR, OUTPUTS_METRICS_DIR, OUTPUTS_PLOTS_DIR

METRIC_NAMES = ["MAE", "RMSE", "MAPE"]
PRIMARY_METRIC = "MAPE"


class ModelComparison:
    @staticmethod
    def load_results(path: str | Path | None = None) -> Dict[str, dict]:
        path = Path(path) if path else Path(SAVED_MODELS_DIR) / "results.json"
        if not path.exists():
            raise FileNotFoundError(
                f"No results file found at {path}. Run 'python train.py' first."
            )
        with open(path) as f:
            return json.load(f)

    @staticmethod
    def rank_models(
        results: Dict[str, dict], metric: str = PRIMARY_METRIC
    ) -> List[tuple[str, float]]:
        if metric not in METRIC_NAMES:
            raise ValueError(
                f"Unknown metric '{metric}'. Expected one of {METRIC_NAMES}."
            )
        return sorted(
            ((name, values[metric]) for name, values in results.items()),
            key=lambda pair: pair[1],
        )

    @classmethod
    def best_model(cls, results: Dict[str, dict], metric: str = PRIMARY_METRIC) -> str:
        ranking = cls.rank_models(results, metric=metric)
        if not ranking:
            raise ValueError("results is empty; cannot determine best model.")
        return ranking[0][0]

    @classmethod
    def compare(cls, results: Dict[str, dict]) -> Dict[str, dict]:
        if not results:
            raise ValueError("results is empty; nothing to compare.")
        overall_best = cls.best_model(results, metric=PRIMARY_METRIC)
        comparison: Dict[str, dict] = {
            name: {"is_best_overall": name == overall_best} for name in results
        }
        for metric in METRIC_NAMES:
            ranking = cls.rank_models(results, metric=metric)
            best_value = ranking[0][1]
            for rank, (name, value) in enumerate(ranking, start=1):
                delta = round(value - best_value, 4)
                pct_worse = (
                    round(delta / best_value * 100, 2)
                    if best_value not in (0, 0.0)
                    else 0.0
                )
                comparison[name][metric] = {
                    "rank": rank,
                    "value": value,
                    "delta_from_best": delta,
                    "pct_worse_than_best": pct_worse,
                }
        return {
            "best_model": overall_best,
            "primary_metric": PRIMARY_METRIC,
            "models": comparison,
        }

    @classmethod
    def generate_report_text(cls, results: Dict[str, dict]) -> str:
        ranking = cls.rank_models(results, metric=PRIMARY_METRIC)
        lines = [
            "=" * 66,
            f"Model Comparison (ranked by {PRIMARY_METRIC}, lower is better)",
            "=" * 66,
            f"{'Rank':<6}{'Model':<22}{'MAE':>10}{'RMSE':>10}{'MAPE':>10}",
            "-" * 66,
        ]
        for rank, (name, _) in enumerate(ranking, start=1):
            metrics = results[name]
            marker = " <- best" if rank == 1 else ""
            lines.append(
                f"{rank:<6}{name:<22}{metrics['MAE']:>10.2f}{metrics['RMSE']:>10.2f}{metrics['MAPE']:>9.2f}%{marker}"
            )
        lines.append("=" * 66)
        return "\n".join(lines)

    @classmethod
    def print_comparison(cls, results: Dict[str, dict]) -> None:
        print("\n" + cls.generate_report_text(results))

    @classmethod
    def save_report(
        cls, results: Dict[str, dict], path: str | Path | None = None
    ) -> None:
        path = (
            Path(path) if path else Path(OUTPUTS_METRICS_DIR) / "comparison_report.txt"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(cls.generate_report_text(results) + "\n")

    @staticmethod
    def save_comparison(comparison: dict, path: str | Path | None = None) -> None:
        path = Path(path) if path else Path(OUTPUTS_METRICS_DIR) / "comparison.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(comparison, f, indent=4)


if __name__ == "__main__":
    from evaluation.plotting import plot_model_comparison

    results = ModelComparison.load_results()
    ModelComparison.print_comparison(results)
    comparison = ModelComparison.compare(results)
    ModelComparison.save_comparison(comparison)
    ModelComparison.save_report(results)
    plot_model_comparison(results, Path(OUTPUTS_PLOTS_DIR) / "model_comparison.svg")
    print(f"\nBest overall model: {comparison['best_model']}")
    print(f"Comparison JSON saved to: {Path(OUTPUTS_METRICS_DIR) / 'comparison.json'}")
    print(
        f"Comparison report saved to: {Path(OUTPUTS_METRICS_DIR) / 'comparison_report.txt'}"
    )
    print(
        f"Comparison plot saved to: {Path(OUTPUTS_PLOTS_DIR) / 'model_comparison.svg'}"
    )
