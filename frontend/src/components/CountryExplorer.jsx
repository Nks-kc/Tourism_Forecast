import { useEffect, useMemo, useRef, useState } from "react";
import {
  getCountries, getCountryHistory, getCountryPredictions,
  getWatchlist, pinCountry, unpinCountry,
} from "../lib/api";
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
  Others: "🌐", "South Korea": "🇰🇷", Spain: "🇪🇸", "Sri Lanka": "🇱🇰",
  Thailand: "🇹🇭", UK: "🇬🇧", USA: "🇺🇸",
};

function getFlag(c) { return FLAG_MAP[c] || "🌏"; }
function label(c) { return c.replace(/_/g, " "); }

// ── Pinned country mini-card ──────────────────────────────────────────────────
function PinnedCard({ country, history, theme, onOpen, onUnpin, isPending }) {
  const records = history?.records || [];
  const latest  = records.at(-1);
  const peak    = records.length ? Math.max(...records.map((r) => r.arrivals)) : null;
  const avg     = records.length
    ? Math.round(records.reduce((s, r) => s + r.arrivals, 0) / records.length)
    : null;

  return (
    <article className="pinned-card" onClick={onOpen} role="button" tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onOpen()}>
      <div className="pinned-card-header">
        <div className="pinned-card-title">
          <span className="pinned-card-flag">{getFlag(country)}</span>
          <span className="pinned-card-name">{label(country)}</span>
        </div>
        <button
          className="pinned-card-unpin"
          type="button"
          title="Unpin"
          aria-label={`Unpin ${label(country)}`}
          disabled={isPending}
          onClick={(e) => { e.stopPropagation(); onUnpin(); }}
        >
          {isPending ? "…" : "×"}
        </button>
      </div>

      <div className="pinned-card-stats">
        <div className="pc-stat">
          <span>Latest</span>
          <strong className="teal">{latest ? <AnimatedCounter value={latest.arrivals} /> : "—"}</strong>
        </div>
        <div className="pc-stat">
          <span>Avg / mo</span>
          <strong>{avg != null ? <AnimatedCounter value={avg} /> : "—"}</strong>
        </div>
        <div className="pc-stat">
          <span>Peak</span>
          <strong>{peak != null ? compactNumber(peak) : "—"}</strong>
        </div>
      </div>

      <div className="pinned-card-chart" onClick={(e) => e.stopPropagation()}>
        {!history ? (
          <div className="pc-loading"><span className="regen-spinner" />Loading…</div>
        ) : (
          <HistoryLineChart records={records} theme={theme} emptyText="No data." />
        )}
      </div>
    </article>
  );
}

// ── Overview panel ────────────────────────────────────────────────────────────
function PinnedOverview({ watchlist, pinnedHistories, theme, pendingPins, onOpen, onUnpin }) {
  return (
    <div className="pinned-overview">
      <div className="pinned-overview-head">
        <span className="panel-title">Pinned countries</span>
        <span className="section-meta">{watchlist.length} saved · click to explore</span>
      </div>
      <div className="pinned-overview-grid">
        {watchlist.map((c) => (
          <PinnedCard
            key={c}
            country={c}
            history={pinnedHistories[c] ?? null}
            theme={theme}
            isPending={pendingPins.has(c)}
            onOpen={() => onOpen(c)}
            onUnpin={() => onUnpin(c)}
          />
        ))}
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function CountryExplorer({ session, theme }) {
  const isLoggedIn = Boolean(session?.token);

  const [countries, setCountries]         = useState([]);
  const [selectedCountry, setSelected]    = useState("");
  const [viewMode, setViewMode]           = useState("detail"); // "overview" | "detail"

  const [watchlist, setWatchlist]             = useState([]);
  const [watchlistLoading, setWLLoading]      = useState(false);
  const [watchlistError, setWLError]          = useState("");
  const [pendingPins, setPendingPins]         = useState(new Set());
  const [pinnedHistories, setPinnedHistories] = useState({});

  const [history, setHistory]           = useState(null);
  const [historyLoading, setHLoading]   = useState(false);
  const [horizon, setHorizon]           = useState(3);
  const [predictions, setPredictions]   = useState(null);
  const [forecastLoading, setFLoading]  = useState(false);
  const [forecastMsg, setForecastMsg]   = useState({ text: "" });

  const wlInitialized = useRef(false);

  // Load countries
  useEffect(() => {
    getCountries()
      .then((d) => setCountries(d.countries || []))
      .catch(() => {});
  }, []);

  // Fetch / clear watchlist on auth change
  useEffect(() => {
    if (!session?.token) {
      setWatchlist([]); setWLError(""); setPendingPins(new Set());
      setPinnedHistories({}); wlInitialized.current = false; return;
    }
    setWLLoading(true); setWLError("");
    getWatchlist(session.token)
      .then((d) => setWatchlist(d.watchlist || []))
      .catch(() => { setWatchlist([]); setWLError("Couldn't load watchlist."); })
      .finally(() => { setWLLoading(false); wlInitialized.current = true; });
  }, [session?.token]);

  // Decide initial view mode after both loads settle
  useEffect(() => {
    if (watchlistLoading || !wlInitialized.current) return;
    if (watchlist.length > 0) {
      setViewMode("overview"); setSelected("");
    } else if (countries.length > 0 && !selectedCountry) {
      setViewMode("detail"); setSelected(countries[0]);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watchlistLoading, watchlist.length, countries.length]);

  // Fetch histories for pinned overview cards
  useEffect(() => {
    const missing = watchlist.filter((c) => !pinnedHistories[c]);
    missing.forEach((c) => {
      getCountryHistory(c)
        .then((d) => setPinnedHistories((prev) => ({ ...prev, [c]: d })))
        .catch(() => {});
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watchlist]);

  // Load detail history when switching to a country
  useEffect(() => {
    if (!selectedCountry || viewMode !== "detail") return;
    let dead = false;
    setHLoading(true); setPredictions(null); setForecastMsg({ text: "" });
    getCountryHistory(selectedCountry)
      .then((d) => { if (!dead) setHistory(d); })
      .catch(() => { if (!dead) setHistory(null); })
      .finally(() => { if (!dead) setHLoading(false); });
    return () => { dead = true; };
  }, [selectedCountry, viewMode]);

  // Auto-forecast on country select
  useEffect(() => {
    if (!selectedCountry || !isLoggedIn || viewMode !== "detail") return;
    let dead = false;
    setFLoading(true);
    getCountryPredictions(selectedCountry, 3, session.token)
      .then((d) => { if (!dead) setPredictions(d.predictions || {}); })
      .catch(() => {})
      .finally(() => { if (!dead) setFLoading(false); });
    return () => { dead = true; };
  }, [selectedCountry, isLoggedIn, viewMode]);

  const watchlistSet     = useMemo(() => new Set(watchlist), [watchlist]);
  const orderedCountries = useMemo(
    () => [...watchlist, ...countries.filter((c) => !watchlistSet.has(c))],
    [watchlist, countries, watchlistSet]
  );

  async function handlePin(c) {
    const prev = watchlist;
    setWLError(""); setWatchlist((wl) => [...wl, c]);
    setPendingPins((s) => new Set(s).add(c));
    try {
      await pinCountry(c, session.token);
      getCountryHistory(c).then((d) => setPinnedHistories((ph) => ({ ...ph, [c]: d }))).catch(() => {});
    } catch (err) {
      setWatchlist(prev); setWLError(err.message || "Failed to pin.");
    } finally {
      setPendingPins((s) => { const n = new Set(s); n.delete(c); return n; });
    }
  }

  async function handleUnpin(c) {
    const prev = watchlist;
    setWLError(""); setWatchlist((wl) => wl.filter((x) => x !== c));
    setPendingPins((s) => new Set(s).add(c));
    try {
      await unpinCountry(c, session.token);
      setPinnedHistories((ph) => { const n = { ...ph }; delete n[c]; return n; });
    } catch (err) {
      setWatchlist(prev); setWLError(err.message || "Failed to unpin.");
    } finally {
      setPendingPins((s) => { const n = new Set(s); n.delete(c); return n; });
      if (watchlist.length === 1) { setViewMode("detail"); setSelected(countries[0] || ""); }
    }
  }

  function openDetail(c) { setSelected(c); setViewMode("detail"); }
  function openOverview() { setViewMode("overview"); setSelected(""); }

  async function handleForecast() {
    if (!isLoggedIn) return;
    setFLoading(true); setForecastMsg({ text: "" });
    try {
      const d = await getCountryPredictions(selectedCountry, horizon, session.token);
      setPredictions(d.predictions || {});
    } catch (err) {
      setForecastMsg({ text: err.message, error: true });
    } finally { setFLoading(false); }
  }

  const records    = history?.records || [];
  const latest     = records.at(-1);
  const peak       = records.length ? Math.max(...records.map((r) => r.arrivals)) : null;
  const peakRecord = peak ? records.find((r) => r.arrivals === peak) : null;
  const avg        = records.length
    ? Math.round(records.reduce((s, r) => s + r.arrivals, 0) / records.length)
    : null;

  return (
    <div className="country-explorer">
      {watchlistError && (
        <div className="watchlist-error-banner" role="alert">
          <span>{watchlistError}</span>
          <button className="watchlist-error-dismiss" type="button" onClick={() => setWLError("")}>×</button>
        </div>
      )}

      <div className="ce-layout">
        {/* ── Sidebar ─────────────────────────────────────── */}
        <aside className="ce-sidebar">
          <div className="ce-sidebar-header">
            <span className="ce-sidebar-title">Countries</span>
            <div className="ce-sidebar-meta">
              {isLoggedIn && watchlist.length > 0 && (
                <span className="watchlist-count">{watchlist.length}</span>
              )}
              {viewMode === "detail" && watchlist.length > 0 && (
                <button className="ce-overview-btn" type="button" onClick={openOverview}
                  title="Back to pinned overview">
                  Pinned
                </button>
              )}
            </div>
          </div>

          {watchlistLoading ? (
            <div className="ce-sidebar-loading">
              <span className="regen-spinner" /><span>Loading…</span>
            </div>
          ) : (
            <ul className="ce-country-list" role="listbox">
              {isLoggedIn && watchlist.length > 0 && (
                <li className="ce-section-label" aria-hidden="true">Pinned</li>
              )}
              {orderedCountries.map((c, idx) => {
                const isPinned  = watchlistSet.has(c);
                const isPending = pendingPins.has(c);
                const isActive  = viewMode === "detail" && selectedCountry === c;
                const showDivider = isLoggedIn && watchlist.length > 0 && !isPinned && idx === watchlist.length;
                return (
                  <li key={c}>
                    {showDivider && <div className="ce-section-label" aria-hidden="true">All</div>}
                    <button
                      type="button" role="option" aria-selected={isActive}
                      className={`ce-country-item${isActive ? " active" : ""}${isPinned ? " pinned" : ""}`}
                      onClick={() => { openDetail(c); setWLError(""); }}
                    >
                      <span className="ce-country-flag">{getFlag(c)}</span>
                      <span className="ce-country-name">{label(c)}</span>
                      {isLoggedIn && (
                        <button
                          type="button"
                          className={`pin-btn${isPinned ? " pinned" : ""}`}
                          title={isPinned ? "Unpin" : "Pin"}
                          aria-label={`${isPinned ? "Unpin" : "Pin"} ${label(c)}`}
                          disabled={isPending}
                          onClick={(e) => { e.stopPropagation(); isPinned ? handleUnpin(c) : handlePin(c); }}
                        >
                          {isPinned ? "×" : "+"}
                        </button>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </aside>

        {/* ── Main panel ──────────────────────────────────── */}
        <div className="ce-detail">

          {/* ══ OVERVIEW MODE ══════════════════════════════ */}
          {viewMode === "overview" && (
            <PinnedOverview
              watchlist={watchlist}
              pinnedHistories={pinnedHistories}
              theme={theme}
              pendingPins={pendingPins}
              onOpen={openDetail}
              onUnpin={handleUnpin}
            />
          )}

          {/* ══ DETAIL MODE ════════════════════════════════ */}
          {viewMode === "detail" && (
            <>
              {/* Country header */}
              <div className="ce-header panel">
                <div className="ce-header-top">
                  <div className="ce-flag-name">
                    {selectedCountry && <span className="ce-flag">{getFlag(selectedCountry)}</span>}
                    <div>
                      <div className="panel-title">{label(selectedCountry) || "Select a country"}</div>
                      <div className="section-meta">
                        {historyLoading ? "loading…" : history ? `${records.length} months` : ""}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="ce-pills">
                  <div className="summary-pill">
                    <span>Latest</span>
                    <strong className="teal">{latest ? <AnimatedCounter value={latest.arrivals} /> : "—"}</strong>
                  </div>
                  <div className="summary-pill">
                    <span>Monthly avg</span>
                    <strong className="gold">{avg != null ? <AnimatedCounter value={avg} /> : "—"}</strong>
                  </div>
                  <div className="summary-pill">
                    <span>Peak</span>
                    <strong>
                      {peak != null ? compactNumber(peak) : "—"}
                      {peakRecord && <sub style={{ fontSize: 10, color: "var(--muted)", marginLeft: 4 }}>{peakRecord.date}</sub>}
                    </strong>
                  </div>
                  <div className="summary-pill">
                    <span>Data span</span>
                    <strong>{history ? `${history.meta.min_year}–${history.meta.max_year}` : "—"}</strong>
                  </div>
                </div>
              </div>

              {/* Forecast */}
              <section className="panel">
                <div className="panel-head">
                  <span className="panel-title">Forecast</span>
                  <div className="forecast-controls">
                    <div className="chip-group">
                      {HORIZONS.map((h) => (
                        <button key={h} className={`chip${horizon === h ? " active" : ""}`}
                          type="button" onClick={() => { setHorizon(h); setPredictions(null); }}>
                          {h} mo
                        </button>
                      ))}
                    </div>
                    <button id="btn-country-forecast" className="primary-btn forecast-regen-btn"
                      type="button" disabled={!isLoggedIn || forecastLoading || !selectedCountry}
                      onClick={handleForecast}>
                      {forecastLoading ? <><span className="regen-spinner" />Generating…</> : predictions ? "Regenerate" : "Generate"}
                    </button>
                  </div>
                </div>
                {forecastMsg.text && (
                  <p className={`forecast-message${forecastMsg.error ? " error" : ""}`}>{forecastMsg.text}</p>
                )}
                <ModelComparisonChart predictions={predictions || {}} theme={theme}
                  emptyText={isLoggedIn ? "Generate a forecast to see predictions." : "Login to generate forecasts."} />
                {predictions && Object.keys(predictions).length > 0 && (
                  <div className="card-grid" style={{ marginTop: 16 }}>
                    {Object.entries(predictions).map(([name, pred]) => (
                      <article className="prediction-card" key={name}>
                        <h3>{name}</h3>
                        <ul className="prediction-list">
                          {pred.months.map((month, i) => (
                            <li key={month}><span>{month}</span><strong>{compactNumber(pred.arrivals[i])}</strong></li>
                          ))}
                        </ul>
                      </article>
                    ))}
                  </div>
                )}
              </section>

              <div className="zone-divider"><span className="zone-label">Historical Analysis</span></div>

              <section className="panel">
                <div className="panel-head">
                  <span className="panel-title">Monthly arrivals</span>
                  <span className="section-meta">{label(selectedCountry)}</span>
                </div>
                <HistoryLineChart records={records} theme={theme}
                  emptyText={historyLoading ? "Loading…" : "No data for this country."} />
              </section>

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
                  </div>
                  <SeasonalDonutChart seasonAverage={history?.season_average || []} theme={theme} />
                </section>
              </div>

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
            </>
          )}
        </div>
      </div>
    </div>
  );
}
