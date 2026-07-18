import AnimatedCounter from "./AnimatedCounter";

export default function Header({nextArrival, totalForecast, bestMape, datasetLastMonth }) {
  return (
    <header className="hero">
      <div className="hero-content">
        <div className="hero-left">
          <h1>Tourism <em>Forecasting</em></h1>
        </div>
        <div className="hero-stats">
          <div className="hero-stat">
            <div className="hero-stat-value red">
              <AnimatedCounter value={nextArrival} />
            </div>
            <div className="hero-stat-label">Next forecast</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-value gold">
              <AnimatedCounter value={totalForecast} />
            </div>
            <div className="hero-stat-label">Horizon total</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-value teal">
              {bestMape ? (
                <AnimatedCounter
                  value={bestMape}
                  formatter={(v) => `${v.toFixed(2)}%`}
                />
              ) : (
                "--"
              )}
            </div>
            <div className="hero-stat-label">Best MAPE</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-value small">{datasetLastMonth || "--"}</div>
            <div className="hero-stat-label">Latest data</div>
          </div>
        </div>
      </div>
    </header>
  );
}
