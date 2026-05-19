import LineChart from "./LineChart";
import { compactNumber, modelColors } from "../lib/format";

const horizons = [1, 3, 6, 12];

export default function ForecastPanel({ horizon, setHorizon, predictions, onGenerate, loading, isLoggedIn, message }) {
  const names = Object.keys(predictions || {});
  const labels = names.length ? predictions[names[0]].months : [];
  const series = names.map((name) => ({
    name,
    values: predictions[name].arrivals,
    color: modelColors[name] || "#e8e6df"
  }));

  return (
    <section className="panel">
      <div className="panel-head">
        <span className="panel-title">Model forecast by month</span>
        <div className="chip-group">
          <span className="section-meta">Horizon</span>
          {horizons.map((value) => (
            <button key={value} className={`chip ${horizon === value ? "active" : ""}`} type="button" onClick={() => setHorizon(value)}>
              {value} mo
            </button>
          ))}
        </div>
      </div>

      <LineChart labels={labels} series={series} emptyText={isLoggedIn ? "Generate a forecast to show model output." : "Login to generate protected forecasts."} />

      <div className="forecast-actions">
        <button className="primary-btn" type="button" disabled={!isLoggedIn || loading} onClick={onGenerate}>
          {loading ? "Generating..." : "Generate Forecast"}
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
