import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import LandingPage from './pages/LandingPage';
import Dashboard from './pages/Dashboard';
import Datasets from './pages/Datasets';
import Training from './pages/Training';
import Explorer from './pages/Explorer';
import Experiments from './pages/Experiments';
import NotFound from './pages/NotFound';
import { ToastProvider } from './components/Toast';

function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
      <Routes>
        {/* Landing page renders without sidebar */}
        <Route path="/" element={<LandingPage />} />
        
        {/* App routes with sidebar layout */}
        <Route path="/dashboard" element={<Layout><Dashboard /></Layout>} />
        <Route path="/datasets" element={<Layout><Datasets /></Layout>} />
        <Route path="/training" element={<Layout><Training /></Layout>} />
        <Route path="/explorer" element={<Layout><Explorer /></Layout>} />
        <Route path="/experiments" element={<Layout><Experiments /></Layout>} />
        
        {/* Catch-all 404 */}
        <Route path="*" element={<Layout><NotFound /></Layout>} />
      </Routes>
    </BrowserRouter>
    </ToastProvider>
  );
}

export default App;
