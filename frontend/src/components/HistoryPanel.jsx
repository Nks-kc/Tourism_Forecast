import { useState } from "react";
import HistoryLineChart from "./HistoryLineChart";
import YearlyBarChart from "./YearlyBarChart";
import { average, seasonColors, seasonLabels } from "../lib/format";
import AnimatedCounter from "./AnimatedCounter";

export default function HistoryPanel({ filters, setFilters, history, loading, theme }) {
  const [view, setView] = useState("monthly");
  const records = history?.records || [];
  const values = records.map((row) => row.arrivals);
  const latest = records.at(-1);

  return (
    <section className="panel">
      <div className="panel-head">
        <span className="panel-title">Historical arrivals</span>
        <div className="panel-head-right">
          <div className="chip-group">
            <button className={`chip ${view === "monthly" ? "active" : ""}`} type="button" onClick={() => setView("monthly")}>Monthly</button>
            <button className={`chip ${view === "yearly" ? "active" : ""}`} type="button" onClick={() => setView("yearly")}>Yearly</button>
          </div>
          <span className="section-meta">{loading ? "loading…" : `${records.length} months`}</span>
        </div>
      </div>

      <div className="form-grid compact">
        <label className="field">
          <span>Start year</span>
          <input type="number" min={history?.meta?.min_year || 1991} max={history?.meta?.max_year || 2026} value={filters.start_year} onChange={(e) => setFilters({ ...filters, start_year: e.target.value })} />
        </label>
        <label className="field">
          <span>End year</span>
          <input type="number" min={history?.meta?.min_year || 1991} max={history?.meta?.max_year || 2026} value={filters.end_year} onChange={(e) => setFilters({ ...filters, end_year: e.target.value })} />
        </label>
        <label className="field">
          <span>Season filter</span>
          <select value={filters.season} onChange={(e) => setFilters({ ...filters, season: e.target.value })}>
            <option value="all">All seasons</option>
            <option value="monsoon">Monsoon</option>
            <option value="spring_trek">Spring trekking</option>
            <option value="autumn_trek">Autumn trekking</option>
            <option value="shoulder">Shoulder months</option>
          </select>
        </label>
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
