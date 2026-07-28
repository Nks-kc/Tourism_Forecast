import ModelComparisonChart from "./ModelComparisonChart";
import { compactNumber } from "../lib/format";

const horizons = [1, 3, 6, 12];

export default function ForecastPanel({ horizon, setHorizon, predictions, onGenerate, loading, isLoggedIn, message, theme }) {
  const names = Object.keys(predictions || {});
  const hasData = names.length > 0;

  function handleHorizonChange(value) {
    setHorizon(value);
  }

  return (
    <section className="panel">
      <div className="panel-head">
        <span className="panel-title">Model forecast comparison</span>

        <div className="panel-head-right">
          {/* Horizon chips + Regenerate — all one control group */}
          <div className="forecast-controls">
            <span className="section-meta">Horizon</span>
            <div className="chip-group">
              {horizons.map((value) => (
                <button
                  key={value}
                  className={`chip ${horizon === value ? "active" : ""}`}
                  type="button"
                  onClick={() => handleHorizonChange(value)}
                >
                  {value} mo
                </button>
              ))}
            </div>
            <button
              className="primary-btn forecast-regen-btn"
              type="button"
              disabled={!isLoggedIn || loading}
              onClick={onGenerate}
            >
              {loading ? (
                <>
                  <span className="regen-spinner" />
                  Generating…
                </>
              ) : hasData ? (
                "Regenerate"
              ) : (
                "Generate"
              )}
            </button>
          </div>
        </div>
      </div>

      {message?.text && (
        <p className={`forecast-message ${message?.error ? "error" : ""}`}>{message.text}</p>
      )}

      <ModelComparisonChart
        predictions={predictions}
        theme={theme}
        emptyText={isLoggedIn ? "Generate a forecast to compare models." : "Login to generate forecasts."}
      />

      {hasData && (
        <div className="card-grid">
          {names.map((name) => (
            <article className="prediction-card" key={name}>
              <h3>{name}</h3>
              <ul className="prediction-list">
                {predictions[name].months.map((month, index) => (
                  <li key={month}>
                    <span>{month}</span>
                    <strong>{compactNumber(predictions[name].arrivals[index])}</strong>
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
