import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { MatchProvider } from './context/MatchContext';
import LandingPage from './pages/LandingPage';

// Accounts, onboarding and the dashboard live in the UniCounsel web app (Flask), which has real sign-up,
// login and a database. This site is the public front door and hands people over to it.
export const APP_URL = (import.meta.env.VITE_APP_URL || 'https://unicounsel-flask.vercel.app').replace(/\/+$/, '');

const GoTo = ({ path }: { path: string }) => {
  useEffect(() => {
    window.location.replace(`${APP_URL}${path}`);
  }, [path]);
  return (
    <div className="flex min-h-screen items-center justify-center bg-background text-sm text-muted-foreground">
      Opening UniCounsel...
    </div>
  );
};

const App = () => (
  <MatchProvider>
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<GoTo path="/login" />} />
        <Route path="/signup" element={<GoTo path="/signup" />} />
        <Route path="/onboarding" element={<GoTo path="/onboarding" />} />
        <Route path="/dashboard/*" element={<GoTo path="/dashboard" />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  </MatchProvider>
);

export default App;
