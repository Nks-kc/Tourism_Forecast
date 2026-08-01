import { useState } from "react";

export default function LoginPage({ onLogin, onRegister, onSendOTP, onVerifyOTP, message }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ username: "", email: "", password: "", otp: "" });
  const [showOTPStep, setShowOTPStep] = useState(false);
  const [pendingEmail, setPendingEmail] = useState("");

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function submit(event) {
    event.preventDefault();
    if (mode === "login") {
      onLogin({ username: form.username, password: form.password });
    } else {
      if (!showOTPStep) {
        // Step 1: Register and show OTP form
        onRegister(form, (email) => {
          setPendingEmail(email);
          setShowOTPStep(true);
        });
      } else {
        // Step 2: Verify OTP
        onVerifyOTP(pendingEmail, form.otp, () => {
          setShowOTPStep(false);
          setPendingEmail("");
          setForm({ username: "", email: "", password: "", otp: "" });
          setMode("login");
        });
      }
    }
  }

  function handleSendOTP() {
    onSendOTP(pendingEmail);
  }

  function cancelOTP() {
    setShowOTPStep(false);
    setPendingEmail("");
    setForm({ username: "", email: "", password: "", otp: "" });
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <h2>Tourism <em>Forecasting</em></h2>
          <p>Sign in to access forecasts, model metrics, and historical data analysis.</p>
        </div>

        {!showOTPStep && (
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
        )}

        {showOTPStep ? (
          <div className="otp-verification">
            <div className="otp-info">
              <h3>Verify Your Email</h3>
              <p>We've sent a verification code to <strong>{pendingEmail}</strong></p>
              <p className="otp-subtitle">Enter the code to complete registration</p>
            </div>
            
            <form className="login-form" onSubmit={submit}>
              <label className="login-field">
                <span>Verification Code</span>
                <input
                  type="text"
                  value={form.otp}
                  onChange={(e) => update("otp", e.target.value)}
                  placeholder="Enter 6-digit code"
                  maxLength="6"
                  pattern="\d*"
                  autoFocus
                />
              </label>

              <button className="login-submit" type="submit">
                Verify & Complete Registration
              </button>

              <div className="otp-actions">
                <button type="button" className="login-link" onClick={handleSendOTP}>
                  Resend Code
                </button>
                <button type="button" className="login-link" onClick={cancelOTP}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        ) : (
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
        )}

        {message?.text && (
          <div className={`login-message ${message.error ? "error" : ""}`}>
            {message.text}
          </div>
        )}

        {!showOTPStep && (
          <div className="login-footer">
            {mode === "login" ? (
              <span>Don't have an account? <button type="button" className="login-link" onClick={() => setMode("register")}>Create one</button></span>
            ) : (
              <span>Already have an account? <button type="button" className="login-link" onClick={() => setMode("login")}>Sign in</button></span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
