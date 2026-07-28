import { useRef, useState, useEffect } from "react";
import HistoryLineChart from "./HistoryLineChart";
import YearlyBarChart from "./YearlyBarChart";
import { average, seasonColors, seasonLabels } from "../lib/format";
import AnimatedCounter from "./AnimatedCounter";

const SEASON_LABELS = {
  all: "All seasons",
  monsoon: "Monsoon",
  spring_trek: "Spring trekking",
  autumn_trek: "Autumn trekking",
  shoulder: "Shoulder months",
};

export default function HistoryPanel({ filters, setFilters, history, loading, theme }) {
  const [view, setView] = useState("monthly");
  const [filterOpen, setFilterOpen] = useState(false);
  const [draft, setDraft] = useState(filters);
  const popoverRef = useRef(null);

  const records = history?.records || [];
  const values = records.map((row) => row.arrivals);
  const latest = records.at(-1);

  // Close popover on outside click
  useEffect(() => {
    if (!filterOpen) return;
    function handleClick(e) {
      if (popoverRef.current && !popoverRef.current.contains(e.target)) {
        setFilterOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [filterOpen]);

  // Sync draft when filters change externally
  useEffect(() => { setDraft(filters); }, [filters]);

  function applyFilters() {
    setFilters(draft);
    setFilterOpen(false);
  }

  function resetFilters() {
    const defaults = { start_year: "2016", end_year: "2026", season: "all" };
    setDraft(defaults);
    setFilters(defaults);
    setFilterOpen(false);
  }

  // Active filter summary for the button label
  const isFiltered = filters.season !== "all"
    || filters.start_year !== "2016"
    || filters.end_year !== "2026";
  const filterLabel = isFiltered
    ? `${filters.start_year}–${filters.end_year} · ${SEASON_LABELS[filters.season] ?? filters.season}`
    : "Filters";

  return (
    <section className="panel">
      <div className="panel-head">
        <span className="panel-title">Historical arrivals</span>
        <div className="panel-head-right">
          <div className="chip-group">
            <button className={`chip ${view === "monthly" ? "active" : ""}`} type="button" onClick={() => setView("monthly")}>Monthly</button>
            <button className={`chip ${view === "yearly" ? "active" : ""}`} type="button" onClick={() => setView("yearly")}>Yearly</button>
          </div>

          {/* Filter toggle */}
          <div className="filter-anchor" ref={popoverRef}>
            <button
              className={`ghost-btn filter-toggle-btn ${isFiltered ? "filter-toggle-btn--active" : ""}`}
              type="button"
              onClick={() => setFilterOpen((o) => !o)}
              aria-expanded={filterOpen}
            >
              <svg width="13" height="13" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M2 4h12M4 8h8M6 12h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
              {filterLabel}
            </button>

            {filterOpen && (
              <div className="filter-popover">
                <div className="filter-popover-row">
                  <label className="filter-field">
                    <span>Start year</span>
                    <input
                      type="number"
                      min={history?.meta?.min_year || 1991}
                      max={history?.meta?.max_year || 2026}
                      value={draft.start_year}
                      onChange={(e) => setDraft((d) => ({ ...d, start_year: e.target.value }))}
                    />
                  </label>
                  <label className="filter-field">
                    <span>End year</span>
                    <input
                      type="number"
                      min={history?.meta?.min_year || 1991}
                      max={history?.meta?.max_year || 2026}
                      value={draft.end_year}
                      onChange={(e) => setDraft((d) => ({ ...d, end_year: e.target.value }))}
                    />
                  </label>
                  <label className="filter-field">
                    <span>Season</span>
                    <select value={draft.season} onChange={(e) => setDraft((d) => ({ ...d, season: e.target.value }))}>
                      <option value="all">All seasons</option>
                      <option value="monsoon">Monsoon</option>
                      <option value="spring_trek">Spring trekking</option>
                      <option value="autumn_trek">Autumn trekking</option>
                      <option value="shoulder">Shoulder months</option>
                    </select>
                  </label>
                </div>
                <div className="filter-popover-actions">
                  <button className="ghost-btn" type="button" onClick={resetFilters}>Reset</button>
                  <button className="primary-btn" type="button" onClick={applyFilters}>Apply</button>
                </div>
              </div>
            )}
          </div>

          <span className="section-meta">{loading ? "loading…" : `${records.length} months`}</span>
        </div>
      </div>

      {view === "monthly" ? (
        <HistoryLineChart records={records} theme={theme} emptyText="No historical records match this filter." />
      ) : (
        <YearlyBarChart records={records} theme={theme} emptyText="No historical records match this filter." />
      )}

      <div className="history-summary">
        <div className="summary-pill">
          <span>Average</span>
          <strong className="teal"><AnimatedCounter value={Math.round(average(values))} /></strong>
        </div>
        <div className="summary-pill">
          <span>Latest</span>
          <strong className="gold"><AnimatedCounter value={latest?.arrivals} /></strong>
        </div>
        {(history?.season_average || []).slice(0, 4).map((row) => (
          <div className="summary-pill" key={row.season}>
            <span>{seasonLabels[row.season] || row.season}</span>
            <strong style={{ color: seasonColors[row.season] }}><AnimatedCounter value={Math.round(row.average_arrivals)} /></strong>
          </div>
        ))}
      </div>
    </section>
  );
}
