import { useEffect, useRef, useState } from "react";
import ThemeToggle from "./ThemeToggle";

const authedTabs = [
  ["dashboard", "Dashboard"],
  ["countries", "Countries"],
  ["models", "Models"],
  ["about", "About"],
];

function UserMenu({ username, onLogout }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  const initial = username?.[0]?.toUpperCase() || "?";

  return (
    <div className="user-menu-anchor" ref={ref}>
      <button
        className="user-avatar-btn"
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label="User menu"
        aria-expanded={open}
      >
        <span className="user-avatar-initial">{initial}</span>
      </button>

      {open && (
        <div className="user-dropdown">
          <div className="user-dropdown-name">{username}</div>
          <button
            className="user-dropdown-logout"
            type="button"
            onClick={() => { setOpen(false); onLogout(); }}
          >
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}

export default function Nav({ activeTab, onTabChange, username, role, onLogout, theme, onThemeToggle }) {
  const isAdmin = role === "admin";
  return (
    <nav>
      <button className="nav-brand" type="button" onClick={() => onTabChange("dashboard")}>
        <span className="nav-title">Nepal Tourism Forecast</span>
      </button>

      <div className="nav-links">
        {username ? (
          <>
            {authedTabs.map(([id, label]) => (
              <button
                key={id}
                className={`nav-btn ${activeTab === id ? "active" : ""}`}
                type="button"
                onClick={() => onTabChange(id)}
              >
                {label}
              </button>
            ))}
            {isAdmin && (
              <button
                id="nav-admin"
                className={`nav-btn nav-admin-btn ${activeTab === "admin" ? "active" : ""}`}
                type="button"
                onClick={() => onTabChange("admin")}
              >
                ⚙ Admin
              </button>
            )}
            <ThemeToggle theme={theme} onToggle={onThemeToggle} />
            <UserMenu username={username} onLogout={onLogout} />
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
