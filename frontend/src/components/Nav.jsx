const tabs = [
  ["dashboard", "Dashboard"],
  ["models", "Models"],
  ["forecast", "Forecast"],
  ["account", "Account"],
  ["about", "About"]
];

export default function Nav({ activeTab, onTabChange, username, onLogout }) {
  return (
    <nav>
      <button className="nav-brand" type="button" onClick={() => onTabChange("dashboard")}>
        <span>
          <span className="nav-title">Nepal Tourism Forecast</span>
          <span className="nav-sub">Foreign arrivals dashboard</span>
        </span>
      </button>
      <div className="nav-links">
        {tabs.map(([id, label]) => (
          <button key={id} className={`nav-btn ${activeTab === id ? "active" : ""}`} type="button" onClick={() => onTabChange(id)}>
            {label}
          </button>
        ))}
        {username ? (
          <button className="nav-btn" type="button" onClick={onLogout}>Logout</button>
        ) : (
          <button className="nav-btn accent" type="button" onClick={() => onTabChange("account")}>Login</button>
        )}
      </div>
    </nav>
  );
}
