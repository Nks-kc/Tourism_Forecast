import ModelComparisonChart from "./ModelComparisonChart";
import { compactNumber } from "../lib/format";

const horizons = [1, 3, 6, 12];

export default function ForecastPanel({ horizon, setHorizon, predictions, onGenerate, loading, isLoggedIn, message, theme }) {
  const names = Object.keys(predictions || {});

  return (
    <section className="panel">
      <div className="panel-head">
        <span className="panel-title">Model forecast comparison</span>
        <div className="chip-group">
          <span className="section-meta">Horizon</span>
          {horizons.map((value) => (
            <button key={value} className={`chip ${horizon === value ? "active" : ""}`} type="button" onClick={() => setHorizon(value)}>
              {value} mo
            </button>
          ))}
        </div>
      </div>

      <ModelComparisonChart
        predictions={predictions}
        theme={theme}
        emptyText={isLoggedIn ? "Generate a forecast to compare models." : "Login to generate forecasts."}
      />

      <div className="forecast-actions">
        <button className="primary-btn" type="button" disabled={!isLoggedIn || loading} onClick={onGenerate}>
          {loading ? "Generating…" : "Generate Forecast"}
        </button>
        <span className={`message ${message?.error ? "error" : ""}`}>{message?.text}</span>
      </div>

      {names.length > 0 && (
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
