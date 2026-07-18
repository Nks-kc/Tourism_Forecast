import ThemeToggle from "./ThemeToggle";

const authedTabs = [
  ["dashboard", "Dashboard"],
  ["countries", "Countries"],
  ["models", "Models"],
  ["forecast", "Forecast"],
  ["about", "About"]
];

export default function Nav({ activeTab, onTabChange, username, onLogout, theme, onThemeToggle }) {
  return (
    <nav>
      <button className="nav-brand" type="button" onClick={() => onTabChange("dashboard")}>
        <span>
          <span className="nav-title">Nepal Tourism Forecast</span>
          <span className="nav-sub">Foreign arrivals dashboard</span>
        </span>
      </button>
      <div className="nav-links">
        {username ? (
          <>
            {authedTabs.map(([id, label]) => (
              <button key={id} className={`nav-btn ${activeTab === id ? "active" : ""}`} type="button" onClick={() => onTabChange(id)}>
                {label}
              </button>
            ))}
            <ThemeToggle theme={theme} onToggle={onThemeToggle} />
            <span className="nav-user">{username}</span>
            <button className="nav-btn nav-logout" type="button" onClick={onLogout}>Logout</button>
          </>
        ) : (
          <>
            <ThemeToggle theme={theme} onToggle={onThemeToggle} />
            <button className="nav-btn accent" type="button" onClick={() => onTabChange("login")}>
              Sign in
            </button>
          </>
        )}
      </div>
    </nav>
  );
}
