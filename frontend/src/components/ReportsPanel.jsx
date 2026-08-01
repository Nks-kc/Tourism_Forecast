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

export default function ReportsPanel({ session, theme }) {
  const [reports, setReports] = useState([]);
  const [reportsLoading, setReportsLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [message, setMessage] = useState({ text: "", error: false });

  // Generation form state
  const [countries, setCountries] = useState([]);
  const [availableCountries, setAvailableCountries] = useState([]);
  const [selectedCountries, setSelectedCountries] = useState([]);
  const [horizon, setHorizon] = useState(6);
  const [watchlist, setWatchlist] = useState([]);
  const [downloadingId, setDownloadingId] = useState(null);

  // Load reports on mount
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
      setCountries(data.countries || []);
      setAvailableCountries(data.countries || []);
    } catch (error) {
      console.error("Failed to load countries:", error);
    }
  }

  async function loadWatchlist() {
    try {
      const data = await getWatchlist(session.token);
      setWatchlist(data.watchlist?.map((w) => w.country) || []);
    } catch (error) {
      console.error("Failed to load watchlist:", error);
    }
  }

  async function handleGenerateReport() {
    if (selectedCountries.length === 0) {
      setMessage({ text: "Please select at least one country", error: true });
      return;
    }

    setGenerating(true);
    setMessage({ text: "Generating report..." });

    try {
      const data = await generateReport(selectedCountries, horizon, session.token);
      setMessage({ text: "Report generated successfully!" });
      setSelectedCountries([]);
      loadReports();
    } catch (error) {
      setMessage({ text: error.message, error: true });
    } finally {
      setGenerating(false);
    }
  }

  async function handleGenerateWatchlistReport() {
    if (watchlist.length === 0) {
      setMessage({ text: "Your watchlist is empty. Pin some countries first.", error: true });
      return;
    }

    setGenerating(true);
    setMessage({ text: "Generating watchlist report..." });

    try {
      const data = await generateWatchlistReport(horizon, session.token);
      setMessage({ text: "Watchlist report generated successfully!" });
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
      setMessage({ text: "Report downloaded successfully!" });
    } catch (error) {
      setMessage({ text: error.message, error: true });
    } finally {
      setDownloadingId(null);
    }
  }

  function toggleCountrySelection(country) {
    if (selectedCountries.includes(country)) {
      setSelectedCountries(selectedCountries.filter((c) => c !== country));
    } else {
      setSelectedCountries([...selectedCountries, country]);
    }
  }

  function selectAllCountries() {
    setSelectedCountries([...availableCountries]);
  }

  function clearSelection() {
    setSelectedCountries([]);
  }

  function selectWatchlistCountries() {
    setSelectedCountries([...watchlist]);
  }

  return (
    <div className="reports-panel">
      {/* Generation Section */}
      <section className="panel">
        <div className="panel-head">
          <span className="panel-title">Generate New Report</span>
          <span className="section-meta">Create PDF forecast reports</span>
        </div>

        {message.text && (
          <div className={`report-message ${message.error ? "error" : ""}`}>
            {message.text}
          </div>
        )}

        {/* Horizon Selector */}
        <div className="report-form-row">
          <label className="report-label">
            <span>Forecast Horizon</span>
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
          </label>
        </div>

        {/* Quick Actions */}
        <div className="report-quick-actions">
          <button
            className="primary-btn"
            type="button"
            disabled={generating || watchlist.length === 0}
            onClick={handleGenerateWatchlistReport}
          >
            {generating ? (
              <>
                <span className="regen-spinner" />
                Generating...
              </>
            ) : (
              <>📌 Generate from Watchlist ({watchlist.length})</>
            )}
          </button>
          <span className="report-divider">or</span>
          <span className="report-hint">Select specific countries below</span>
        </div>

        {/* Country Selection */}
        <div className="report-country-selection">
          <div className="report-selection-header">
            <span className="report-label">Select Countries ({selectedCountries.length} selected)</span>
            <div className="report-selection-actions">
              <button type="button" className="report-action-btn" onClick={selectAllCountries}>
                Select All
              </button>
              <button type="button" className="report-action-btn" onClick={selectWatchlistCountries} disabled={watchlist.length === 0}>
                Select Watchlist
              </button>
              <button type="button" className="report-action-btn" onClick={clearSelection}>
                Clear
              </button>
            </div>
          </div>

          <div className="report-country-grid">
            {availableCountries.map((country) => (
              <label key={country} className="report-country-checkbox">
                <input
                  type="checkbox"
                  checked={selectedCountries.includes(country)}
                  onChange={() => toggleCountrySelection(country)}
                />
                <span>{country.replace(/_/g, " ")}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Generate Button */}
        <button
          className="primary-btn report-generate-btn"
          type="button"
          disabled={generating || selectedCountries.length === 0}
          onClick={handleGenerateReport}
        >
          {generating ? (
            <>
              <span className="regen-spinner" />
              Generating Report...
            </>
          ) : (
            <>📄 Generate Report</>
          )}
        </button>
      </section>

      {/* Reports List Section */}
      <section className="panel">
        <div className="panel-head">
          <span className="panel-title">Generated Reports</span>
          <span className="section-meta">
            {reportsLoading ? "Loading..." : `${reports.length} report${reports.length !== 1 ? "s" : ""}`}
          </span>
        </div>

        {reportsLoading ? (
          <div className="report-loading">
            <span className="regen-spinner" />
            <span>Loading reports...</span>
          </div>
        ) : reports.length === 0 ? (
          <div className="empty">
            No reports generated yet. Create your first report above!
          </div>
        ) : (
          <div className="reports-list">
            {reports.map((report) => (
              <article key={report.id} className="report-card">
                <div className="report-card-header">
                  <div className="report-card-title">
                    <span className="report-card-icon">📊</span>
                    <div>
                      <div className="report-card-name">
                        {report.countries.join(", ").replace(/_/g, " ")}
                      </div>
                      <div className="report-card-meta">
                        Report #{report.id} · {report.report_type}
                      </div>
                    </div>
                  </div>
                  <button
                    className="primary-btn report-download-btn"
                    type="button"
                    disabled={downloadingId === report.id}
                    onClick={() => handleDownload(report.id, report.countries)}
                  >
                    {downloadingId === report.id ? (
                      <>
                        <span className="regen-spinner" />
                        Downloading...
                      </>
                    ) : (
                      <>⬇ Download PDF</>
                    )}
                  </button>
                </div>
                <div className="report-card-footer">
                  <span>Generated: {new Date(report.generated_at).toLocaleString()}</span>
                  <span>{report.countries.length} {report.countries.length === 1 ? "country" : "countries"}</span>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
