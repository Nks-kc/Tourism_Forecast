const TOKEN_KEY = "tourism_token";
const USERNAME_KEY = "tourism_username";
const ROLE_KEY = "tourism_role";

export function getStoredSession() {
  return {
    token: localStorage.getItem(TOKEN_KEY) || "",
    username: localStorage.getItem(USERNAME_KEY) || "",
    role: localStorage.getItem(ROLE_KEY) || "",
  };
}

export function storeSession({ token, username, role = "" }) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USERNAME_KEY, username);
  localStorage.setItem(ROLE_KEY, role);
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USERNAME_KEY);
  localStorage.removeItem(ROLE_KEY);
}

export async function apiRequest(path, options = {}, token = "") {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(path, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `Request failed: ${response.status}`);
  }
  return data;
}

// ── Health ────────────────────────────────────────────────────
export function getHealth() {
  return apiRequest("/health");
}

// ── Auth ──────────────────────────────────────────────────────
export function login(credentials) {
  return apiRequest("/auth/login", { method: "POST", body: JSON.stringify(credentials) });
}

export function registerAccount(payload) {
  return apiRequest("/auth/register", { method: "POST", body: JSON.stringify(payload) });
}

export function sendOTP(email) {
  return apiRequest("/auth/otp/send", { method: "POST", body: JSON.stringify({ email }) });
}

export function verifyOTP(email, otp) {
  return apiRequest("/auth/otp/verify", { method: "POST", body: JSON.stringify({ email, otp }) });
}

export function getMe(token) {
  return apiRequest("/auth/me", { method: "GET" }, token);
}

// ── Nationwide History ────────────────────────────────────────
export function getHistory(filters) {
  const params = new URLSearchParams(filters);
  return apiRequest(`/history?${params.toString()}`);
}

// ── Countries ─────────────────────────────────────────────────
export function getCountries() {
  return apiRequest("/countries");
}

// ── Per-Country History (public) ──────────────────────────────
export function getCountryHistory(country, filters = {}) {
  const params = new URLSearchParams({ country, ...filters });
  return apiRequest(`/history/country?${params.toString()}`);
}

// ── Nationwide Predictions ────────────────────────────────────
export function getPredictions(horizon, token) {
  return apiRequest("/predict", {
    method: "POST",
    body: JSON.stringify({ horizon })
  }, token);
}

// ── Per-Country Predictions (auth required) ───────────────────
export function getCountryPredictions(country, horizon, token) {
  return apiRequest("/predict/country", {
    method: "POST",
    body: JSON.stringify({ country, horizon })
  }, token);
}

// ── Model Metrics ─────────────────────────────────────────────
export function getMetrics(token) {
  return apiRequest("/evaluate", { method: "GET" }, token);
}

export function getCountryMetrics(token) {
  return apiRequest("/evaluate/country", { method: "GET" }, token);
}

// ── Admin ─────────────────────────────────────────────────────
export function adminGetUsers(token) {
  return apiRequest("/admin/users", { method: "GET" }, token);
}

export function adminStartTraining(token) {
  return apiRequest("/admin/train", { method: "POST" }, token);
}

export function adminGetTrainStatus(token) {
  return apiRequest("/admin/train/status", { method: "GET" }, token);
}

export function adminReloadCache(token) {
  return apiRequest("/admin/reload", { method: "POST" }, token);
}

export function adminAddData(token, entries, year, month, overwrite = true) {
  return apiRequest(
    "/admin/data",
    { method: "POST", body: JSON.stringify({ entries, year, month, overwrite }) },
    token
  );
}

export function adminSetUserRole(token, username, role) {
  return apiRequest(
    `/admin/users/${encodeURIComponent(username)}/role`,
    { method: "PATCH", body: JSON.stringify({ role }) },
    token
  );
}

// ── Watchlist (auth required) ─────────────────────────────────
export function getWatchlist(token) {
  return apiRequest("/watchlist", { method: "GET" }, token);
}

export function pinCountry(country, token) {
  return apiRequest("/watchlist/pin", {
    method: "POST",
    body: JSON.stringify({ country }),
  }, token);
}

export function unpinCountry(country, token) {
  return apiRequest("/watchlist/unpin", {
    method: "DELETE",
    body: JSON.stringify({ country }),
  }, token);
}

// ── Reports ───────────────────────────────────────────────────
export function generateReport(countries, horizon, token) {
  return apiRequest("/reports/generate", {
    method: "POST",
    body: JSON.stringify({ countries, horizon })
  }, token);
}

export function generateWatchlistReport(horizon, token) {
  return apiRequest("/reports/generate", {
    method: "POST",
    body: JSON.stringify({ type: "watchlist", horizon })
  }, token);
}

export function listReports(token) {
  return apiRequest("/reports", { method: "GET" }, token);
}

export async function downloadReport(reportId, token) {
  const headers = { Authorization: `Bearer ${token}` };
  const response = await fetch(`/reports/${reportId}/download`, { headers });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: "Download failed" }));
    throw new Error(error.error || "Download failed");
  }
  return response.blob();
}
