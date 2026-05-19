import LineChart from "./LineChart";
import { average, compactNumber, seasonColors, seasonLabels } from "../lib/format";

export default function HistoryPanel({ filters, setFilters, history, loading }) {
  const records = history?.records || [];
  const labels = records.map((row) => row.date);
  const values = records.map((row) => row.arrivals);
  const pointColors = records.map((row) => seasonColors[row.season] || "#e8e6df");
  const seasonAverage = history?.season_average || [];
  const latest = records.at(-1);

  return (
    <section className="panel">
      <div className="panel-head">
        <span className="panel-title">Historical arrivals by season</span>
        <span className="section-meta">{loading ? "loading" : `${records.length} months`}</span>
      </div>

      <div className="form-grid compact">
        <label className="field">
          <span>Start year</span>
          <input
            type="number"
            min={history?.meta?.min_year || 1991}
            max={history?.meta?.max_year || 2026}
            value={filters.start_year}
            onChange={(event) => setFilters({ ...filters, start_year: event.target.value })}
          />
        </label>
        <label className="field">
          <span>End year</span>
          <input
            type="number"
            min={history?.meta?.min_year || 1991}
            max={history?.meta?.max_year || 2026}
            value={filters.end_year}
            onChange={(event) => setFilters({ ...filters, end_year: event.target.value })}
          />
        </label>
        <label className="field">
          <span>Season filter</span>
          <select value={filters.season} onChange={(event) => setFilters({ ...filters, season: event.target.value })}>
            <option value="all">All seasons</option>
            <option value="monsoon">Monsoon</option>
            <option value="spring_trek">Spring trekking</option>
            <option value="autumn_trek">Autumn trekking</option>
            <option value="shoulder">Shoulder months</option>
          </select>
        </label>
      </div>

      <LineChart
        labels={labels}
        series={[{ name: "Monthly arrivals", values, color: "#e8e6df", pointColors }]}
        emptyText="No historical records match this filter."
      />

      <div className="history-summary">
        <div className="summary-pill">
          <span>Average selected</span>
          <strong className="teal">{compactNumber(Math.round(average(values)))}</strong>
        </div>
        <div className="summary-pill">
          <span>Latest selected</span>
          <strong className="gold">{latest ? compactNumber(latest.arrivals) : "--"}</strong>
        </div>
        {seasonAverage.slice(0, 4).map((row) => (
          <div className="summary-pill" key={row.season}>
            <span>{seasonLabels[row.season] || row.season}</span>
            <strong style={{ color: seasonColors[row.season] }}>{compactNumber(Math.round(row.average_arrivals))}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
