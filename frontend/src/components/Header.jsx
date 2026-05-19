import { compactNumber } from "../lib/format";

export default function Header({ apiOnline, nextArrival, totalForecast, bestMape, datasetLastMonth }) {
  return (
    <header className="hero">
      <div className="hero-content">
        <div className={`hero-tag ${apiOnline ? "online" : "offline"}`}>
          {apiOnline ? "API online" : "API offline"}
        </div>
        <h1>Tourism Demand <br /><em>Forecasting</em> in Nepal</h1>
        <p className="hero-desc">
          Explore historical arrivals by season and generate model forecasts for Nepal tourism demand.
        </p>
        <div className="hero-stats">
          <div className="hero-stat">
            <div className="hero-stat-value red">{compactNumber(nextArrival)}</div>
            <div className="hero-stat-label">Next forecast arrival</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-value gold">{compactNumber(totalForecast)}</div>
            <div className="hero-stat-label">Selected horizon total</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-value teal">{bestMape ? `${Number(bestMape).toFixed(2)}%` : "--"}</div>
            <div className="hero-stat-label">Best saved MAPE</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-value small">{datasetLastMonth || "--"}</div>
            <div className="hero-stat-label">Dataset last month</div>
          </div>
        </div>
      </div>
    </header>
  );
}
