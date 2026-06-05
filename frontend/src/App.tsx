import { Navigate, NavLink, Route, Routes } from "react-router-dom";

import { useAuth } from "./auth";
import ApplicationsPage from "./pages/ApplicationsPage";
import FavoritesPage from "./pages/FavoritesPage";
import JobsPage from "./pages/JobsPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import StatsPage from "./pages/StatsPage";

export default function App() {
  const { loading, logout, user } = useAuth();

  if (loading) {
    return (
      <div className="app-shell">
        <p>Loading...</p>
      </div>
    );
  }

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <div className="app-shell">
      <header className="site-header">
        <div>
          <h1>Tracker</h1>
        </div>
        <div className="header-actions">
          <nav className="nav-links" aria-label="Primary navigation">
            <NavLink to="/" end>
              All
            </NavLink>
            <NavLink to="/favorites">Favorites</NavLink>
            <NavLink to="/jobs">Jobs</NavLink>
            <NavLink to="/stats">Stats</NavLink>
          </nav>
          <div className="user-menu">
            <span>{user.email}</span>
            <button type="button" className="secondary" onClick={() => void logout()}>
              Logout
            </button>
          </div>
        </div>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<ApplicationsPage />} />
          <Route path="/favorites" element={<FavoritesPage />} />
          <Route path="/jobs" element={<JobsPage />} />
          <Route path="/stats" element={<StatsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
