import { useEffect, useState } from "react";
import {
  generateReport,
  generateWatchlistReport,
  getCountries,
  getWatchlist,
  listReports,
  downloadReport,
} from "../lib/api";

const HORIZONS = [1, 3, 6, 12];

export default function ReportsPanel({ session }) {
  const [reports, setReports] = useState([]);
  const [reportsLoading, setReportsLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [message, setMessage] = useState({ text: "", error: false });

  const [availableCountries, setAvailableCountries] = useState([]);
  const [selectedCountries, setSelectedCountries] = useState([]);
  const [horizon, setHorizon] = useState(6);
  const [watchlist, setWatchlist] = useState([]);
  const [downloadingId, setDownloadingId] = useState(null);

  useEffect(() => {
    if (session?.token) {
      loadReports();
      loadCountries();
      loadWatchlist();
    }
  }, [session?.token]);

  async function loadReports() {
    setReportsLoading(true);
    try {
      const data = await listReports(session.token);
      setReports(data.reports || []);
    } catch (error) {
      setMessage({ text: error.message, error: true });
    } finally {
      setReportsLoading(false);
    }
  }

  async function loadCountries() {
    try {
      const data = await getCountries();
      setAvailableCountries(data.countries || []);
    } catch {
      // silently ignore
    }
  }

  async function loadWatchlist() {
    try {
      const data = await getWatchlist(session.token);
      setWatchlist(data.watchlist?.map((w) => w.country ?? w) || []);
    } catch {
      // silently ignore
    }
  }

  async function handleGenerate() {
    if (selectedCountries.length === 0) {
      setMessage({ text: "Select at least one country to generate a report.", error: true });
      return;
    }
    setGenerating(true);
    setMessage({ text: "" });
    try {
      await generateReport(selectedCountries, horizon, session.token);
      setMessage({ text: "Report generated successfully.", error: false });
      setSelectedCountries([]);
      loadReports();
    } catch (error) {
      setMessage({ text: error.message, error: true });
    } finally {
      setGenerating(false);
    }
  }

  async function handleGenerateWatchlist() {
    if (watchlist.length === 0) {
      setMessage({ text: "Your watchlist is empty. Pin some countries first.", error: true });
      return;
    }
    setGenerating(true);
    setMessage({ text: "" });
    try {
      await generateWatchlistReport(horizon, session.token);
      setMessage({ text: "Watchlist report generated.", error: false });
      loadReports();
    } catch (error) {
      setMessage({ text: error.message, error: true });
    } finally {
      setGenerating(false);
    }
  }

  async function handleDownload(reportId, countries) {
    setDownloadingId(reportId);
    try {
      const blob = await downloadReport(reportId, session.token);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `tourism_report_${countries.join("_")}_${reportId}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      setMessage({ text: error.message, error: true });
    } finally {
      setDownloadingId(null);
    }
  }

  function toggle(country) {
    setSelectedCountries((prev) =>
      prev.includes(country) ? prev.filter((c) => c !== country) : [...prev, country]
    );
  }

  return (
    <div className="reports-panel">

      {/* ── Generate ── */}
      <section className="panel">
        <div className="panel-head">
          <span className="panel-title">Generate Report</span>
          <span className="section-meta">PDF · Multi-model forecast</span>
        </div>

        {message.text && (
          <div className={`report-message${message.error ? " error" : ""}`}>
            {message.text}
          </div>
        )}

        {/* Horizon */}
        <div className="report-field">
          <span className="report-field-label">Forecast horizon</span>
          <div className="chip-group">
            {HORIZONS.map((h) => (
              <button
                key={h}
                className={`chip${horizon === h ? " active" : ""}`}
                type="button"
                onClick={() => setHorizon(h)}
              >
                {h} {h === 1 ? "month" : "months"}
              </button>
            ))}
          </div>
        </div>

        {/* Country selection */}
        <div className="report-field">
          <div className="report-selection-header">
            <span className="report-field-label">
              Countries
              {selectedCountries.length > 0 && (
                <span className="report-selected-count">{selectedCountries.length} selected</span>
              )}
            </span>
            <div className="report-selection-actions">
              <button type="button" className="report-action-btn" onClick={() => setSelectedCountries([...availableCountries])}>
                All
              </button>
              <button
                type="button"
                className="report-action-btn"
                onClick={() => setSelectedCountries([...watchlist])}
                disabled={watchlist.length === 0}
              >
                Watchlist
              </button>
              <button
                type="button"
                className="report-action-btn report-action-btn--muted"
                onClick={() => setSelectedCountries([])}
                disabled={selectedCountries.length === 0}
              >
                Clear
              </button>
            </div>
          </div>

          <div className="report-country-grid">
            {availableCountries.map((country) => (
              <label key={country} className={`report-country-item${selectedCountries.includes(country) ? " selected" : ""}`}>
                <input
                  type="checkbox"
                  checked={selectedCountries.includes(country)}
                  onChange={() => toggle(country)}
                />
                <span>{country.replace(/_/g, " ")}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="report-actions">
          <button
            className="primary-btn report-generate-btn"
            type="button"
            disabled={generating || selectedCountries.length === 0}
            onClick={handleGenerate}
          >
            {generating ? <><span className="regen-spinner" /> Generating…</> : "Generate Report"}
          </button>
          {watchlist.length > 0 && (
            <button
              className="ghost-btn"
              type="button"
              disabled={generating}
              onClick={handleGenerateWatchlist}
            >
              From Watchlist ({watchlist.length})
            </button>
          )}
        </div>
      </section>

      {/* ── History ── */}
      <section className="panel">
        <div className="panel-head">
          <span className="panel-title">Generated Reports</span>
          <span className="section-meta">
            {reportsLoading ? "Loading…" : `${reports.length} ${reports.length === 1 ? "report" : "reports"}`}
          </span>
        </div>

        {reportsLoading ? (
          <div className="report-loading">
            <span className="regen-spinner" />
            <span>Loading…</span>
          </div>
        ) : reports.length === 0 ? (
          <div className="empty">No reports yet. Generate one above.</div>
        ) : (
          <div className="reports-list">
            {reports.map((report) => (
              <article key={report.id} className="report-card">
                <div className="report-card-body">
                  <div className="report-card-info">
                    <div className="report-card-name">
                      {report.countries.join(", ").replace(/_/g, " ")}
                    </div>
                    <div className="report-card-meta">
                      {new Date(report.generated_at).toLocaleString("en-US", {
                        year: "numeric", month: "short", day: "numeric",
                        hour: "2-digit", minute: "2-digit",
                      })}
                      <span className="report-card-dot" />
                      {report.countries.length} {report.countries.length === 1 ? "country" : "countries"}
                      <span className="report-card-dot" />
                      {report.report_type}
                    </div>
                  </div>
                  <button
                    className="ghost-btn report-download-btn"
                    type="button"
                    disabled={downloadingId === report.id}
                    onClick={() => handleDownload(report.id, report.countries)}
                  >
                    {downloadingId === report.id
                      ? <><span className="regen-spinner" /> Downloading…</>
                      : "Download PDF"}
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
