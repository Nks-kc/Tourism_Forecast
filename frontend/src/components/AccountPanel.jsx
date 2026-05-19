import { useState } from "react";

export default function AccountPanel({ username, onLogin, onRegister, onLogout, message }) {
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

  if (username) {
    return (
      <section className="panel account-panel">
        <div className="panel-head">
          <span className="panel-title">Account</span>
          <span className="section-meta">signed in</span>
        </div>
        <div className="signed-in">
          <div>
            <span className="section-meta">Current session</span>
            <strong>{username}</strong>
          </div>
          <button className="ghost-btn" type="button" onClick={onLogout}>Logout</button>
        </div>
      </section>
    );
  }

  return (
    <section className="panel account-panel">
      <div className="panel-head">
        <span className="panel-title">Account</span>
        <div className="chip-group">
          <button className={`chip ${mode === "login" ? "active" : ""}`} type="button" onClick={() => setMode("login")}>Login</button>
          <button className={`chip ${mode === "register" ? "active" : ""}`} type="button" onClick={() => setMode("register")}>Register</button>
        </div>
      </div>

      <form className="form-grid account-form" onSubmit={submit}>
        <label className="field">
          <span>Username</span>
          <input value={form.username} onChange={(event) => update("username", event.target.value)} autoComplete="username" />
        </label>
        {mode === "register" && (
          <label className="field">
            <span>Email</span>
            <input type="email" value={form.email} onChange={(event) => update("email", event.target.value)} autoComplete="email" />
          </label>
        )}
        <label className="field">
          <span>Password</span>
          <input type="password" value={form.password} onChange={(event) => update("password", event.target.value)} autoComplete={mode === "login" ? "current-password" : "new-password"} />
        </label>
        <label className="field submit-field">
          <span>&nbsp;</span>
          <button className="primary-btn" type="submit">{mode === "login" ? "Login" : "Create Account"}</button>
        </label>
      </form>

      <div className={`message ${message?.error ? "error" : ""}`}>{message?.text}</div>
    </section>
  );
}
