import { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";
import AdminPanel from "./components/AdminPanel";
import ForecastPanel from "./components/ForecastPanel";
import Header from "./components/Header";
import HistoryPanel from "./components/HistoryPanel";
import LoginPage from "./components/LoginPage";
import ModelsPanel from "./components/ModelsPanel";
import Nav from "./components/Nav";
import YoYChart from "./components/YoYChart";
import SeasonalDonutChart from "./components/SeasonalDonutChart";
import MonthlyAverageChart from "./components/MonthlyAverageChart";
import AnimatedCounter from "./components/AnimatedCounter";
import CountryExplorer from "./components/CountryExplorer";
import {
  clearSession,
  getHealth,
  getHistory,
  getMe,
  getMetrics,
  getPredictions,
  getStoredSession,
  login,
  registerAccount,
  storeSession
} from "./lib/api";
import { compactNumber } from "./lib/format";

const THEME_KEY = "tourism_theme";

function App() {
  const stored = getStoredSession();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [session, setSession] = useState(stored);
  const [historyFilters, setHistoryFilters] = useState({ start_year: "2016", end_year: "2026", season: "all" });
  const [history, setHistory] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [horizon, setHorizon] = useState(3);
  const [predictions, setPredictions] = useState({});
  const [forecastLoading, setForecastLoading] = useState(false);
  const [metrics, setMetrics] = useState({});
  const [accountMessage, setAccountMessage] = useState({ text: "" });
  const [forecastMessage, setForecastMessage] = useState({ text: "" });
  const [theme, setTheme] = useState(() => localStorage.getItem(THEME_KEY) || "dark");
  const [apiOnline, setApiOnline] = useState(false);

  const isLoggedIn = Boolean(session.token);

  // Sync theme to DOM
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  function toggleTheme() {
    setTheme((t) => (t === "dark" ? "light" : "dark"));
  }

  const bestModel = useMemo(() => {
    const names = Object.keys(metrics || {});
    if (!names.length) return "";
    return names.reduce((winner, name) => metrics[name].MAPE < metrics[winner].MAPE ? name : winner, names[0]);
  }, [metrics]);

  const heroStats = useMemo(() => {
    const firstModel = predictions.SARIMA || Object.values(predictions)[0];
    const nextArrival = firstModel?.arrivals?.[0] || null;
    const totalForecast = firstModel?.arrivals?.reduce((sum, value) => sum + Number(value), 0) || null;
    const bestMape = bestModel ? metrics[bestModel].MAPE : null;
    const datasetLastMonth = history?.records?.at(-1)?.date || null;
    return { nextArrival, totalForecast, bestMape, datasetLastMonth };
  }, [predictions, bestModel, metrics, history]);

  // Health check
  useEffect(() => {
    getHealth()
      .then(() => setApiOnline(true))
      .catch(() => setApiOnline(false));
  }, []);

  // Load history data on login
  useEffect(() => {
    if (!isLoggedIn) return;
    let ignore = false;
    setHistoryLoading(true);
    getHistory(historyFilters)
      .then((data) => { if (!ignore) setHistory(data); })
      .catch(() => { if (!ignore) setHistory(null); })
      .finally(() => { if (!ignore) setHistoryLoading(false); });
    return () => { ignore = true; };
  }, [historyFilters, isLoggedIn]);

  // Validate stored session on mount
  useEffect(() => {
    if (!session.token) return;
    getMe(session.token)
      .then((user) => {
        const updated = { token: session.token, username: user.username, role: user.role };
        setSession(updated);
        storeSession(updated);
      })
      .catch(() => handleLogout("Session expired. Please sign in again."));
  }, []);

  // Load metrics on login
  useEffect(() => {
    if (isLoggedIn) loadMetrics();
  }, [isLoggedIn]);

  // Auto-generate forecast on login using default horizon — populates both hero and forecast panel
  useEffect(() => {
    if (!isLoggedIn || Object.keys(predictions).length > 0) return;
    setForecastLoading(true);
    getPredictions(horizon, session.token)
      .then((data) => setPredictions(data.predictions || {}))
      .catch(() => {})
      .finally(() => setForecastLoading(false));
  }, [isLoggedIn]);

  async function handleLogin(credentials) {
    try {
      const data = await login(credentials);
      // Fetch full profile to get role
      const profile = await getMe(data.token).catch(() => ({}));
      const nextSession = { token: data.token, username: data.username, role: profile.role || "user" };
      setSession(nextSession);
      storeSession(nextSession);
      setAccountMessage({ text: "" });
      setActiveTab("dashboard");
    } catch (error) {
      setAccountMessage({ text: error.message, error: true });
    }
  }

  async function handleRegister(payload) {
    try {
      await registerAccount(payload);
      setAccountMessage({ text: "Account created! You can sign in now." });
    } catch (error) {
      setAccountMessage({ text: error.message, error: true });
    }
  }

  function handleLogout(message = "") {
    clearSession();
    setSession({ token: "", username: "", role: "" });
    setPredictions({});
    setMetrics({});
    setHistory(null);
    setForecastMessage({ text: "" });
    setAccountMessage({ text: message });
    setActiveTab("dashboard");
  }

  async function generateForecast() {
    setForecastLoading(true);
    setForecastMessage({ text: "Generating forecast…" });
    try {
      const data = await getPredictions(horizon, session.token);
      setPredictions(data.predictions || {});
      setForecastMessage({ text: "Forecast generated." });
    } catch (error) {
      setForecastMessage({ text: error.message, error: true });
    } finally {
      setForecastLoading(false);
    }
  }

  async function loadMetrics(token = session.token) {
    if (!token) return;
    try {
      const data = await getMetrics(token);
      setMetrics(data.metrics || {});
    } catch {
      setMetrics({});
    }
  }

  // ── Not logged in: show login page ──
  if (!isLoggedIn) {
    return (
      <>
        <Nav activeTab={activeTab} onTabChange={setActiveTab} username="" onLogout={() => {}} theme={theme} onThemeToggle={toggleTheme} />
        <LoginPage onLogin={handleLogin} onRegister={handleRegister} message={accountMessage} />
      </>
    );
  }

  // ── Logged in: show dashboard ──
  return (
    <>
      <Nav activeTab={activeTab} onTabChange={setActiveTab} username={session.username} role={session.role} onLogout={() => handleLogout()} theme={theme} onThemeToggle={toggleTheme} />
      {activeTab === "dashboard" && <Header {...heroStats} bestModel={bestModel} forecastLoading={forecastLoading} />}
      <main className="section">
        {activeTab === "dashboard" && (
          <>
            <ForecastPanel
              horizon={horizon}
              setHorizon={setHorizon}
              predictions={predictions}
              onGenerate={generateForecast}
              loading={forecastLoading}
              isLoggedIn={true}
              message={forecastMessage}
              theme={theme}
            />

            <ModelsPanel metrics={metrics} bestModel={bestModel} />

            {/* ── Zone 2: Historical Analysis ── */}
            <div className="zone-divider">
              <span className="zone-label">Historical Analysis</span>
            </div>

            <HistoryPanel filters={historyFilters} setFilters={setHistoryFilters} history={history} loading={historyLoading} theme={theme} />

            <div className="dashboard-charts">
              <section className="panel">
                <div className="panel-head">
                  <span className="panel-title">Year-over-year comparison</span>
                  <span className="section-meta">Monthly arrivals by year</span>
                </div>
                <YoYChart records={history?.records || []} theme={theme} />
              </section>

              <section className="panel">
                <div className="panel-head">
                  <span className="panel-title">Seasonal breakdown</span>
                  <span className="section-meta">Average arrivals by season</span>
                </div>
                <SeasonalDonutChart seasonAverage={history?.season_average || []} theme={theme} />
              </section>
            </div>

            <section className="panel">
              <div className="panel-head">
                <span className="panel-title">Monthly average arrivals</span>
                <span className="section-meta">{history ? `${history.meta.start_year}–${history.meta.end_year}` : "—"}</span>
              </div>
              <MonthlyAverageChart monthlyAverage={history?.monthly_average || []} theme={theme} />
            </section>
          </>
        )}

        {activeTab === "countries" && (
          <CountryExplorer session={session} theme={theme} />
        )}

        {activeTab === "models" && <ModelsPanel metrics={metrics} bestModel={bestModel} />}

        {activeTab === "about" && <AboutPanel />}

        {activeTab === "admin" && session.role === "admin" && (
          <AdminPanel session={session} />
        )}
      </main>
      <footer>
        <span><strong>Nepal Tourism Forecast</strong> · Flask API + React frontend</span>
        <span>Models: MLP · SARIMA · Holt-Winters · Linear Regression</span>
      </footer>
    </>
  );
}

function StatCard({ label, value, tone = "", sub, animated = false }) {
  return (
    <article className="stat-card animate-in">
      <div className="stat-label">{label}</div>
      <div className={`stat-value ${tone}`}>
        {animated && typeof value === "number" ? (
          <AnimatedCounter value={value} />
        ) : (
          typeof value === "number" ? compactNumber(value) : value
        )}
      </div>
      <div className="stat-sub">{sub}</div>
    </article>
  );
}

function AboutPanel() {
  return (
    <section className="about-grid">
      <article className="about-card">
        <h3>Project Scope</h3>
        <p>This app forecasts monthly foreign tourist arrivals to Nepal — both nationwide totals and per-country breakdowns — using four machine learning models with seasonal and trend features.</p>
      </article>
      <article className="about-card">
        <h3>Tech Stack</h3>
        <p>React 19 frontend with Chart.js interactive visualizations, served by a Flask REST API with JWT authentication, SQLite user storage, and per-country model routing.</p>
      </article>
      <article className="about-card">
        <h3>Models</h3>
        <p>SARIMA, Holt-Winters exponential smoothing, Linear Regression, and Multi-Layer Perceptron (MLP) neural network — evaluated by MAE, RMSE, and MAPE for both total and per-country series.</p>
      </article>
      <article className="about-card">
        <h3>Data Source</h3>
        <p>Historical monthly foreign arrivals from 19 source countries, processed with seasonal engineering, trend extraction, COVID-period flagging, and one-hot country encoding.</p>
      </article>
    </section>
  );
}

createRoot(document.getElementById("root")).render(<App />);
