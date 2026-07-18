import { useState } from "react";

export default function LoginPage({ onLogin, onRegister, message }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ username: "", email: "", password: "" });

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function submit(event) {
    event.preventDefault();
    if (mode === "login") {
      onLogin({ username: form.username, password: form.password });
    } else {
      onRegister(form);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <h2>Tourism <em>Forecasting</em></h2>
          <p>Sign in to access forecasts, model metrics, and historical data analysis.</p>
        </div>

        <div className="login-toggle">
          <button
            className={`login-toggle-btn ${mode === "login" ? "active" : ""}`}
            type="button"
            onClick={() => setMode("login")}
          >
            Sign in
          </button>
          <button
            className={`login-toggle-btn ${mode === "register" ? "active" : ""}`}
            type="button"
            onClick={() => setMode("register")}
          >
            Create account
          </button>
        </div>

        <form className="login-form" onSubmit={submit}>
          <label className="login-field">
            <span>Username</span>
            <input
              value={form.username}
              onChange={(e) => update("username", e.target.value)}
              autoComplete="username"
              placeholder="Enter username"
            />
          </label>

          {mode === "register" && (
            <label className="login-field">
              <span>Email</span>
              <input
                type="email"
                value={form.email}
                onChange={(e) => update("email", e.target.value)}
                autoComplete="email"
                placeholder="you@example.com"
              />
            </label>
          )}

          <label className="login-field">
            <span>Password</span>
            <input
              type="password"
              value={form.password}
              onChange={(e) => update("password", e.target.value)}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              placeholder="••••••••"
            />
          </label>

          <button className="login-submit" type="submit">
            {mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>

        {message?.text && (
          <div className={`login-message ${message.error ? "error" : ""}`}>
            {message.text}
          </div>
        )}

        <div className="login-footer">
          {mode === "login" ? (
            <span>Don't have an account? <button type="button" className="login-link" onClick={() => setMode("register")}>Create one</button></span>
          ) : (
            <span>Already have an account? <button type="button" className="login-link" onClick={() => setMode("login")}>Sign in</button></span>
          )}
        </div>
      </div>
    </div>
  );
}
