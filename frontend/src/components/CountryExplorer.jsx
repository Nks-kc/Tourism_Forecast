import { useEffect, useState } from "react";
import { getCountries, getCountryHistory, getCountryPredictions } from "../lib/api";
import HistoryLineChart from "./HistoryLineChart";
import ModelComparisonChart from "./ModelComparisonChart";
import SeasonalDonutChart from "./SeasonalDonutChart";
import MonthlyAverageChart from "./MonthlyAverageChart";
import AnimatedCounter from "./AnimatedCounter";
import { compactNumber, seasonLabels, seasonColors } from "../lib/format";

const HORIZONS = [1, 3, 6, 12];
const FLAG_MAP = {
  Australia: "🇦🇺", Bangladesh: "🇧🇩", Canada: "🇨🇦", China: "🇨🇳",
  France: "🇫🇷", Germany: "🇩🇪", India: "🇮🇳", Italy: "🇮🇹",
  Japan: "🇯🇵", Malaysia: "🇲🇾", Myanmar: "🇲🇲", Netherlands: "🇳🇱",
  Others: "🌐", South_Korea: "🇰🇷", Spain: "🇪🇸", Sri_Lanka: "🇱🇰",
  Thailand: "🇹🇭", UK: "🇬🇧", USA: "🇺🇸",
};

function getFlag(country) {
  return FLAG_MAP[country] || "🌏";
}

export default function CountryExplorer({ session, theme }) {
  const isLoggedIn = Boolean(session?.token);

  const [countries, setCountries] = useState([]);
  const [selectedCountry, setSelectedCountry] = useState("");

  const [history, setHistory] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);

  const [horizon, setHorizon] = useState(3);
  const [predictions, setPredictions] = useState(null);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [forecastMsg, setForecastMsg] = useState({ text: "" });

  // Load countries list on mount
  useEffect(() => {
    getCountries()
      .then((d) => {
        setCountries(d.countries || []);
        if (d.countries?.length) setSelectedCountry(d.countries[0]);
      })
      .catch(() => {});
  }, []);

  // Load history whenever country changes
  useEffect(() => {
    if (!selectedCountry) return;
    let ignore = false;
    setHistoryLoading(true);
    setPredictions(null);
    setForecastMsg({ text: "" });
    getCountryHistory(selectedCountry)
      .then((d) => { if (!ignore) setHistory(d); })
      .catch(() => { if (!ignore) setHistory(null); })
      .finally(() => { if (!ignore) setHistoryLoading(false); });
    return () => { ignore = true; };
  }, [selectedCountry]);

  // Auto-generate 3-month forecast whenever country changes
  useEffect(() => {
    if (!selectedCountry || !isLoggedIn) return;
    let ignore = false;
    setForecastLoading(true);
    getCountryPredictions(selectedCountry, 3, session.token)
      .then((d) => { if (!ignore) setPredictions(d.predictions || {}); })
      .catch(() => {})
      .finally(() => { if (!ignore) setForecastLoading(false); });
    return () => { ignore = true; };
  }, [selectedCountry, isLoggedIn]);

  async function handleForecast() {
    if (!isLoggedIn) return;
    setForecastLoading(true);
    setForecastMsg({ text: "" });
    try {
      const d = await getCountryPredictions(selectedCountry, horizon, session.token);
      setPredictions(d.predictions || {});
    } catch (err) {
      setForecastMsg({ text: err.message, error: true });
    } finally {
      setForecastLoading(false);
    }
  }

  const records = history?.records || [];
  const latest = records.at(-1);
  const peak = records.length ? Math.max(...records.map((r) => r.arrivals)) : null;
  const peakRecord = peak ? records.find((r) => r.arrivals === peak) : null;
  const avg = records.length
    ? Math.round(records.reduce((s, r) => s + r.arrivals, 0) / records.length)
    : null;

  const displayName = selectedCountry.replace(/_/g, " ");

  return (
    <div className="country-explorer">
      {/* Country picker */}
      <div className="ce-header panel">
        <div className="ce-picker-row">
          <div className="ce-flag-name">
            {selectedCountry && (
              <span className="ce-flag">{getFlag(selectedCountry)}</span>
            )}
            <div>
              <div className="panel-title">{displayName || "Select a country"}</div>
              <div className="section-meta">
                {historyLoading ? "loading…" : history ? `${records.length} months of data` : ""}
              </div>
            </div>
          </div>

          <select
            id="country-select"
            className="ce-country-select"
            value={selectedCountry}
            onChange={(e) => setSelectedCountry(e.target.value)}
          >
            {countries.map((c) => (
              <option key={c} value={c}>{getFlag(c)} {c.replace(/_/g, " ")}</option>
            ))}
          </select>
        </div>

        {/* Summary pills */}
        <div className="ce-pills">
          <div className="summary-pill">
            <span>Latest month</span>
            <strong className="teal">
              {latest ? <AnimatedCounter value={latest.arrivals} /> : "—"}
            </strong>
          </div>
          <div className="summary-pill">
            <span>Monthly avg</span>
            <strong className="gold">
              {avg != null ? <AnimatedCounter value={avg} /> : "—"}
            </strong>
          </div>
          <div className="summary-pill">
            <span>Peak arrivals</span>
            <strong>
              {peak != null ? compactNumber(peak) : "—"}
              {peakRecord && <sub style={{ fontSize: "10px", color: "var(--muted)", marginLeft: 4 }}>{peakRecord.date}</sub>}
            </strong>
          </div>
          <div className="summary-pill">
            <span>Data span</span>
            <strong>
              {history ? `${history.meta.min_year}–${history.meta.max_year}` : "—"}
            </strong>
          </div>
        </div>
      </div>

      {/* Forecast panel — moved above history */}
      <section className="panel">
        <div className="panel-head">
          <span className="panel-title">
            Country forecast
            {selectedCountry && <span className="section-meta" style={{ marginLeft: 8 }}>— {displayName}</span>}
          </span>
          <div className="forecast-controls">
            <span className="section-meta">Horizon</span>
            <div className="chip-group">
              {HORIZONS.map((h) => (
                <button
                  key={h}
                  className={`chip ${horizon === h ? "active" : ""}`}
                  type="button"
                  onClick={() => { setHorizon(h); setPredictions(null); }}
                >
                  {h} mo
                </button>
              ))}
            </div>
            <button
              id="btn-country-forecast"
              className="primary-btn forecast-regen-btn"
              type="button"
              disabled={!isLoggedIn || forecastLoading || !selectedCountry}
              onClick={handleForecast}
            >
              {forecastLoading ? (
                <><span className="regen-spinner" />Generating…</>
              ) : predictions ? "Regenerate" : "Generate"}
            </button>
          </div>
        </div>

        {forecastMsg.text && (
          <p className={`forecast-message ${forecastMsg.error ? "error" : ""}`}>{forecastMsg.text}</p>
        )}

        <ModelComparisonChart
          predictions={predictions || {}}
          theme={theme}
          emptyText={
            isLoggedIn
              ? `Select a country and generate a forecast.`
              : "Login to generate forecasts."
          }
        />

        {/* Prediction table */}
        {predictions && Object.keys(predictions).length > 0 && (
          <div className="card-grid" style={{ marginTop: 16 }}>
            {Object.entries(predictions).map(([name, pred]) => (
              <article className="prediction-card" key={name}>
                <h3>{name}</h3>
                <ul className="prediction-list">
                  {pred.months.map((month, i) => (
                    <li key={month}>
                      <span>{month}</span>
                      <strong>{compactNumber(pred.arrivals[i])}</strong>
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        )}
      </section>

      {/* Zone divider */}
      <div className="zone-divider">
        <span className="zone-label">Historical Analysis</span>
      </div>

      {/* Historical line chart */}
      <section className="panel">
        <div className="panel-head">
          <span className="panel-title">Monthly arrivals history</span>
          <span className="section-meta">{displayName}</span>
        </div>
        <HistoryLineChart
          records={records}
          theme={theme}
          emptyText={historyLoading ? "Loading…" : "No data for this country."}
        />
      </section>

      {/* Two-column: Monthly avg + Seasonal */}
      <div className="dashboard-charts">
        <section className="panel">
          <div className="panel-head">
            <span className="panel-title">Monthly average</span>
            <span className="section-meta">all years</span>
          </div>
          <MonthlyAverageChart monthlyAverage={history?.monthly_average || []} theme={theme} />
        </section>
        <section className="panel">
          <div className="panel-head">
            <span className="panel-title">Seasonal breakdown</span>
            <span className="section-meta">avg arrivals by season</span>
          </div>
          <SeasonalDonutChart seasonAverage={history?.season_average || []} theme={theme} />
        </section>
      </div>

      {/* Season breakdown pills */}
      {(history?.season_average || []).length > 0 && (
        <div className="history-summary" style={{ marginTop: 0 }}>
          {history.season_average.map((row) => (
            <div className="summary-pill" key={row.season}>
              <span>{seasonLabels[row.season] || row.season}</span>
              <strong style={{ color: seasonColors[row.season] }}>
                <AnimatedCounter value={Math.round(row.average_arrivals)} />
              </strong>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
