import AnimatedCounter from "./AnimatedCounter";

// Derive next month label (e.g. "September 2026") from current date
function nextMonthLabel() {
  const d = new Date();
  d.setMonth(d.getMonth() + 1);
  return d.toLocaleString("en-US", { month: "long", year: "numeric" });
}

export default function Header({ nextArrival, bestMape, datasetLastMonth, bestModel, forecastLoading }) {
  const monthLabel = nextMonthLabel();
  const hasData = nextArrival !== null && nextArrival !== undefined;

  return (
    <header className="hero">
      <div className="hero-inner">

        {/* Left — eyebrow + big number */}
        <div className="hero-focal">
          <div className="hero-eyebrow">
            <span/>
            Next month forecast
          </div>

          <div className="hero-number-row">
            {forecastLoading ? (
              <div className="hero-skeleton" />
            ) : hasData ? (
              <div className="hero-number">
                <AnimatedCounter value={nextArrival} />
              </div>
            ) : (
              <div className="hero-number hero-number--empty">—</div>
            )}
            <span className="hero-unit">arrivals</span>
          </div>

          <div className="hero-month">{monthLabel}</div>
        </div>

        {/* Right — supporting stats */}
        <div className="hero-aside">
          <div className="hero-aside-item">
            <span className="hero-aside-label">Best model</span>
            <span className="hero-aside-value teal">{bestModel || "—"}</span>
          </div>
          <div className="hero-aside-divider" />
          <div className="hero-aside-item">
            <span className="hero-aside-label">Best MAPE</span>
            <span className="hero-aside-value gold">
              {bestMape != null ? `${Number(bestMape).toFixed(2)}%` : "—"}
            </span>
          </div>
          <div className="hero-aside-divider" />
          <div className="hero-aside-item">
            <span className="hero-aside-label">Latest data</span>
            <span className="hero-aside-value">{datasetLastMonth || "—"}</span>
          </div>
        </div>

      </div>
    </header>
  );
}
