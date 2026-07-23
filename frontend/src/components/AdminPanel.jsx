import { useEffect, useRef, useState } from "react";
import {
  adminAddData,
  adminGetTrainStatus,
  adminGetUsers,
  adminReloadCache,
  adminSetUserRole,
  adminStartTraining,
} from "../lib/api";


/* ─────────────────────────────────────────────────────────────── */
/* Tiny helpers                                                     */
/* ─────────────────────────────────────────────────────────────── */
function Badge({ role }) {
  const cls = role === "admin" ? "badge badge-admin" : "badge badge-user";
  return <span className={cls}>{role}</span>;
}

function StatusDot({ ok }) {
  return (
    <span
      className="status-dot"
      style={{ background: ok ? "var(--teal)" : "var(--danger, #e55)" }}
    />
  );
}

function SectionTitle({ icon, children }) {
  return (
    <div className="admin-section-title">
      <span className="admin-section-icon">{icon}</span>
      <h2>{children}</h2>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────── */
/* User table                                                       */
/* ─────────────────────────────────────────────────────────────── */
function UsersSection({ token }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [roleMsg, setRoleMsg] = useState("");

  function fetchUsers() {
    setLoading(true);
    setError("");
    setRoleMsg("");
    adminGetUsers(token)
      .then((d) => setUsers(d.users || []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  async function toggleRole(user) {
    const newRole = user.role === "admin" ? "user" : "admin";
    try {
      await adminSetUserRole(token, user.username, newRole);
      setRoleMsg(`✓ ${user.username} is now '${newRole}'`);
      fetchUsers();
    } catch (e) {
      setRoleMsg(`✗ ${e.message}`);
    }
  }

  useEffect(() => {
    fetchUsers();
  }, []);

  return (
    <section className="admin-card">
      <div className="admin-card-head">
        <SectionTitle>Registered Users</SectionTitle>
        <button
          id="btn-admin-refresh-users"
          className="chip active"
          type="button"
          onClick={fetchUsers}
          disabled={loading}
        >
          {loading ? "Loading…" : "↻ Refresh"}
        </button>
      </div>

      {error && <p className="admin-msg error">{error}</p>}
      {roleMsg && <p className="admin-msg">{roleMsg}</p>}

      <div className="admin-table-wrap">
        <table className="admin-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Username</th>
              <th>Email</th>
              <th>Role</th>
              <th>Joined</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {users.length === 0 && !loading ? (
              <tr>
                <td colSpan={5} style={{ textAlign: "center", color: "var(--muted)" }}>
                  No users found.
                </td>
              </tr>
            ) : (
              users.map((u) => (
                <tr key={u.id}>
                  <td>{u.id}</td>
                  <td>
                    <strong>{u.username}</strong>
                  </td>
                  <td>{u.email}</td>
                  <td>
                    <Badge role={u.role} />
                  </td>
                  <td>{u.created_at ? u.created_at.slice(0, 10) : "—"}</td>
                  <td>
                    <button
                      className="chip"
                      type="button"
                      onClick={() => toggleRole(u)}
                      title={u.role === "admin" ? "Demote to user" : "Promote to admin"}
                    >
                      {u.role === "admin" ? "↓ user" : "↑ admin"}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <p className="admin-hint">{users.length} account{users.length !== 1 ? "s" : ""} total</p>
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────── */
/* Model training controls                                          */
/* ─────────────────────────────────────────────────────────────── */
function TrainingSection({ token }) {
  const [status, setStatus] = useState(null);
  const [msg, setMsg] = useState({ text: "" });
  const [polling, setPolling] = useState(false);
  const [elapsedSec, setElapsedSec] = useState(0);
  const pollRef = useRef(null);
  const timerRef = useRef(null);

  function clearPoll() {
    if (pollRef.current) clearInterval(pollRef.current);
    if (timerRef.current) clearInterval(timerRef.current);
    pollRef.current = null;
    timerRef.current = null;
  }

  function startPolling() {
    clearPoll();
    setPolling(true);
    setElapsedSec(0);
    const startTime = Date.now();

    // Elapsed timer
    timerRef.current = setInterval(() => {
      setElapsedSec(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    // Status poller
    pollRef.current = setInterval(() => {
      adminGetTrainStatus(token)
        .then((d) => {
          setStatus(d);
          if (!d.in_progress) {
            clearPoll();
            setPolling(false);
            setMsg({ text: "✓ Training complete! Click Reload Cache to activate the new models." });
          }
        })
        .catch((e) => {
          clearPoll();
          setPolling(false);
          setMsg({ text: `Polling error: ${e.message}`, error: true });
        });
    }, 3000);
  }

  useEffect(() => {
    adminGetTrainStatus(token)
      .then(setStatus)
      .catch((e) => setMsg({ text: `Status check failed: ${e.message}`, error: true }));
    return clearPoll;
  }, [token]);

  async function handleStartTraining() {
    setMsg({ text: "Sending request…" });
    try {
      const d = await adminStartTraining(token);
      setStatus({ in_progress: true });
      setMsg({ text: d.message || "Training started in background. Polling for updates…" });
      startPolling();
    } catch (e) {
      setMsg({ text: `Error: ${e.message}`, error: true });
    }
  }

  async function handleReload() {
    setMsg({ text: "Reloading cache…" });
    try {
      const d = await adminReloadCache(token);
      setMsg({ text: `✓ Cache cleared (${(d.cleared || []).length} caches reset)` });
    } catch (e) {
      setMsg({ text: `Error: ${e.message}`, error: true });
    }
  }

  const inProgress = status?.in_progress ?? false;

  return (
    <section className="admin-card">
      <div className="admin-card-head">
        <SectionTitle>Model Training</SectionTitle>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <StatusDot ok={!inProgress} />
          <span className="admin-hint" style={{ margin: 0 }}>
            {inProgress
              ? `Training… ${polling ? `${elapsedSec}s elapsed` : ""}`
              : status === null ? "Checking…" : "Idle"}
          </span>
        </div>
      </div>

      <p className="admin-hint">
        Retrain all four models (MLP, SARIMA, Holt-Winters, Linear Regression) on the
        current dataset. Runs <code>train.py</code> in a background thread — typically
        2–5 minutes. After training completes, click <strong>Reload Cache</strong> to
        activate the new models.
      </p>

      <div className="admin-action-row">
        <button
          id="btn-admin-train"
          className="primary-btn"
          type="button"
          onClick={handleStartTraining}
          disabled={inProgress || polling}
        >
          {inProgress ? `Training… (${elapsedSec}s)` : "▶ Start Training"}
        </button>

        <button
          id="btn-admin-reload"
          className="ghost-btn"
          type="button"
          onClick={handleReload}
        >
          Reload Cache
        </button>

      </div>

      {msg.text && (
        <p className={`admin-msg ${msg.error ? "error" : ""}`}>{msg.text}</p>
      )}
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────── */
/* Data ingestion                                                   */
/* ─────────────────────────────────────────────────────────────── */
const BLANK_ENTRY = { country: "", arrivals: "" };

function DataIngestionSection({ token }) {
  const [year, setYear] = useState(() => new Date().getFullYear());
  const [month, setMonth] = useState(() => new Date().getMonth() + 1);
  const [overwrite, setOverwrite] = useState(true);
  const [entries, setEntries] = useState([{ ...BLANK_ENTRY }]);
  const [msg, setMsg] = useState({ text: "" });
  const [loading, setLoading] = useState(false);

  function addEntry() {
    setEntries((e) => [...e, { ...BLANK_ENTRY }]);
  }

  function removeEntry(i) {
    setEntries((e) => e.filter((_, idx) => idx !== i));
  }

  function updateEntry(i, field, value) {
    setEntries((prev) =>
      prev.map((row, idx) => (idx === i ? { ...row, [field]: value } : row))
    );
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const cleaned = entries
      .filter((r) => r.country.trim() && r.arrivals !== "")
      .map((r) => ({ country: r.country.trim(), arrivals: Number(r.arrivals) }));

    if (!cleaned.length) {
      setMsg({ text: "Add at least one valid entry.", error: true });
      return;
    }

    setLoading(true);
    setMsg({ text: "Submitting…" });
    try {
      const d = await adminAddData(token, cleaned, year, month, overwrite);
      setMsg({
        text: `✓ Ingested — added: ${d.added}, updated: ${d.updated}, total rows: ${d.total_rows}`,
      });
      setEntries([{ ...BLANK_ENTRY }]);
    } catch (err) {
      setMsg({ text: err.message, error: true });
    } finally {
      setLoading(false);
    }
  }

  const months = [
    "Jan","Feb","Mar","Apr","May","Jun",
    "Jul","Aug","Sep","Oct","Nov","Dec",
  ];

  return (
    <section className="admin-card">
      <SectionTitle>Ingest Monthly Data</SectionTitle>
      <p className="admin-hint">
        Add or update arrival records for a specific year/month. After ingesting, run
        training so models reflect the new data.
      </p>

      <form className="admin-form" onSubmit={handleSubmit}>
        {/* Year / Month / Overwrite */}
        <div className="admin-form-row">
          <label className="admin-label">
            Year
            <input
              className="admin-input"
              type="number"
              min={2000}
              max={2100}
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
              required
            />
          </label>
          <label className="admin-label">
            Month
            <select
              className="admin-input"
              value={month}
              onChange={(e) => setMonth(Number(e.target.value))}
            >
              {months.map((m, i) => (
                <option key={m} value={i + 1}>
                  {i + 1} — {m}
                </option>
              ))}
            </select>
          </label>
          <label className="admin-label" style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
            <input
              type="checkbox"
              checked={overwrite}
              onChange={(e) => setOverwrite(e.target.checked)}
              style={{ width: 16, height: 16 }}
            />
            Overwrite existing
          </label>
        </div>

        {/* Entries */}
        <div className="admin-entries">
          {entries.map((row, i) => (
            <div className="admin-entry-row" key={i}>
              <input
                className="admin-input"
                placeholder="Country (e.g. India)"
                value={row.country}
                onChange={(e) => updateEntry(i, "country", e.target.value)}
              />
              <input
                className="admin-input"
                type="number"
                min={0}
                placeholder="Arrivals"
                value={row.arrivals}
                onChange={(e) => updateEntry(i, "arrivals", e.target.value)}
              />
              {entries.length > 1 && (
                <button
                  type="button"
                  className="chip"
                  style={{ color: "var(--danger, #e55)" }}
                  onClick={() => removeEntry(i)}
                >
                  ✕
                </button>
              )}
            </div>
          ))}
        </div>

        <div className="admin-action-row" style={{ marginTop: 8 }}>
          <button type="button" className="chip active" onClick={addEntry}>
            + Add row
          </button>
          <button
            id="btn-admin-ingest"
            className="primary-btn"
            type="submit"
            disabled={loading}
          >
            {loading ? "Submitting…" : "Submit Data"}
          </button>
        </div>

        {msg.text && (
          <p className={`admin-msg ${msg.error ? "error" : ""}`}>{msg.text}</p>
        )}
      </form>
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────── */
/* Root panel                                                       */
/* ─────────────────────────────────────────────────────────────── */
export default function AdminPanel({ session }) {
  const { token, username } = session;

  return (
    <div className="admin-panel">
      <div className="admin-header">
        <div>
          <h1 className="admin-title">Admin Panel</h1>
          <p className="admin-subtitle">
            Signed in as <strong>{username}</strong> · Full system access
          </p>
        </div>
        <span className="badge badge-admin" style={{ fontSize: 14, padding: "6px 14px" }}>
          Admin
        </span>
      </div>

      <UsersSection token={token} />
      <TrainingSection token={token} />
      <DataIngestionSection token={token} />
    </div>
  );
}
