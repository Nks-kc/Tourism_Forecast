const TOKEN_KEY = "tourism_token";
const USERNAME_KEY = "tourism_username";

export function getStoredSession() {
  return {
    token: localStorage.getItem(TOKEN_KEY) || "",
    username: localStorage.getItem(USERNAME_KEY) || ""
  };
}

export function storeSession({ token, username }) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USERNAME_KEY, username);
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USERNAME_KEY);
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

export function getHealth() {
  return apiRequest("/health");
}

export function getHistory(filters) {
  const params = new URLSearchParams(filters);
  return apiRequest(`/history?${params.toString()}`);
}

export function login(credentials) {
  return apiRequest("/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials)
  });
}

export function registerAccount(payload) {
  return apiRequest("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getMe(token) {
  return apiRequest("/auth/me", { method: "GET" }, token);
}

export function getPredictions(horizon, token) {
  return apiRequest("/predict", {
    method: "POST",
    body: JSON.stringify({ horizon })
  }, token);
}

export function getMetrics(token) {
  return apiRequest("/evaluate", { method: "GET" }, token);
}
