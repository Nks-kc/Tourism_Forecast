import { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";
import AccountPanel from "./components/AccountPanel";
import ForecastPanel from "./components/ForecastPanel";
import Header from "./components/Header";
import HistoryPanel from "./components/HistoryPanel";
import ModelsPanel from "./components/ModelsPanel";
import Nav from "./components/Nav";
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

function App() {
  const stored = getStoredSession();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [apiOnline, setApiOnline] = useState(false);
  const [session, setSession] = useState(stored);
  const [historyFilters, setHistoryFilters] = useState({ start_year: "2016", end_year: "2026", season: "all" });
  const [history, setHistory] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [horizon, setHorizon] = useState(3);
  const [predictions, setPredictions] = useState({});
  const [forecastLoading, setForecastLoading] = useState(false);
  const [metrics, setMetrics] = useState({});
  const [accountMessage, setAccountMessage] = useState({ text: "Login or create an account to request forecasts." });
  const [forecastMessage, setForecastMessage] = useState({ text: "" });

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

  useEffect(() => {
    getHealth()
      .then(() => setApiOnline(true))
      .catch(() => setApiOnline(false));
  }, []);

  useEffect(() => {
    let ignore = false;
    setHistoryLoading(true);
    getHistory(historyFilters)
      .then((data) => {
        if (!ignore) setHistory(data);
      })
      .catch(() => {
        if (!ignore) setHistory(null);
      })
      .finally(() => {
        if (!ignore) setHistoryLoading(false);
      });
    return () => {
      ignore = true;
    };
  }, [historyFilters]);

  useEffect(() => {
    if (!session.token) return;
    getMe(session.token)
      .then((user) => {
        setSession((current) => ({ ...current, username: user.username }));
        storeSession({ token: session.token, username: user.username });
        setAccountMessage({ text: "Ready to call protected API routes." });
      })
      .catch(() => handleLogout("Session expired. Login again."));
  }, []);

  async function handleLogin(credentials) {
    try {
      const data = await login(credentials);
      const nextSession = { token: data.token, username: data.username };
      setSession(nextSession);
      storeSession(nextSession);
      setAccountMessage({ text: `Signed in as ${data.username}.` });
      setActiveTab("dashboard");
      await loadMetrics(data.token);
    } catch (error) {
      setAccountMessage({ text: error.message, error: true });
    }
  }

  async function handleRegister(payload) {
    try {
      await registerAccount(payload);
      setAccountMessage({ text: "Account created. You can login now." });
    } catch (error) {
      setAccountMessage({ text: error.message, error: true });
    }
  }

  function handleLogout(message = "Logged out.") {
    clearSession();
    setSession({ token: "", username: "" });
    setPredictions({});
    setMetrics({});
    setForecastMessage({ text: "" });
    setAccountMessage({ text: message });
  }

  async function generateForecast() {
    if (!session.token) {
      setForecastMessage({ text: "Login first.", error: true });
      setActiveTab("account");
      return;
    }

    setForecastLoading(true);
    setForecastMessage({ text: "Generating forecast..." });
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

  return (
    <>
      <Nav activeTab={activeTab} onTabChange={setActiveTab} username={session.username} onLogout={() => handleLogout()} />
      <Header apiOnline={apiOnline} {...heroStats} />
      <main className="section">
        <div className="tab-bar">
          {["dashboard", "models", "forecast", "account", "about"].map((tab) => (
            <button key={tab} className={`tab-btn ${activeTab === tab ? "active" : ""}`} type="button" onClick={() => setActiveTab(tab)}>
              {tab[0].toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {activeTab === "dashboard" && (
          <>
            <div className="stat-grid">
              <StatCard label="Best model" value={bestModel || "--"} tone="teal" sub="Lowest saved test MAPE" />
              <StatCard label="Records" value={history?.meta?.records || "--"} tone="gold" sub="Current history filter" />
              <StatCard label="Data range" value={history ? `${history.meta.min_year}-${history.meta.max_year}` : "--"} sub="Foreign arrivals" />
              <StatCard label="Auth status" value={session.username || "Signed out"} tone={session.username ? "teal" : "red"} sub={session.username ? "Token saved in this browser" : "Login to call protected routes"} />
            </div>
            <HistoryPanel filters={historyFilters} setFilters={setHistoryFilters} history={history} loading={historyLoading} />
            <ForecastPanel
              horizon={horizon}
              setHorizon={setHorizon}
              predictions={predictions}
              onGenerate={generateForecast}
              loading={forecastLoading}
              isLoggedIn={Boolean(session.token)}
              message={forecastMessage}
            />
          </>
        )}

        {activeTab === "models" && <ModelsPanel metrics={metrics} onRefresh={() => loadMetrics()} isLoggedIn={Boolean(session.token)} bestModel={bestModel} />}
        {activeTab === "forecast" && (
          <ForecastPanel
            horizon={horizon}
            setHorizon={setHorizon}
            predictions={predictions}
            onGenerate={generateForecast}
            loading={forecastLoading}
            isLoggedIn={Boolean(session.token)}
            message={forecastMessage}
          />
        )}
        {activeTab === "account" && (
          <AccountPanel username={session.username} onLogin={handleLogin} onRegister={handleRegister} onLogout={() => handleLogout()} message={accountMessage} />
        )}
        {activeTab === "about" && <AboutPanel />}
      </main>
      <footer>
        <span><strong>Nepal Tourism Forecast</strong> · Flask API + React frontend</span>
        <span>Models: MLP · SARIMA · Holt-Winters · Linear Regression</span>
      </footer>
    </>
  );
}

function StatCard({ label, value, tone = "", sub }) {
  return (
    <article className="stat-card">
      <div className="stat-label">{label}</div>
      <div className={`stat-value ${tone}`}>{typeof value === "number" ? compactNumber(value) : value}</div>
      <div className="stat-sub">{sub}</div>
    </article>
  );
}

function AboutPanel() {
  return (
    <section className="about-grid">
      <article className="about-card">
        <h3>Project Scope</h3>
        <p>This app forecasts monthly foreign tourist arrivals in Nepal using engineered seasonal, trend, COVID, and lag features.</p>
      </article>
      <article className="about-card">
        <h3>Frontend Structure</h3>
        <p>The UI now runs as a Vite React app with componentized dashboard, history, forecast, model, and account flows.</p>
      </article>
    </section>
  );
}

createRoot(document.getElementById("root")).render(<App />);
