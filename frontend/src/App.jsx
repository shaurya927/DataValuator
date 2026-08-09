import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import LandingPage from './pages/LandingPage';
import Dashboard from './pages/Dashboard';
import Datasets from './pages/Datasets';
import Training from './pages/Training';
import Explorer from './pages/Explorer';
import Experiments from './pages/Experiments';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Landing page renders without sidebar */}
        <Route path="/" element={<LandingPage />} />
        
        {/* App routes with sidebar layout */}
        <Route element={<Layout><Routes><Route path="*" element={null} /></Routes></Layout>}>
        </Route>
        <Route path="/dashboard" element={<Layout><Dashboard /></Layout>} />
        <Route path="/datasets" element={<Layout><Datasets /></Layout>} />
        <Route path="/training" element={<Layout><Training /></Layout>} />
        <Route path="/explorer" element={<Layout><Explorer /></Layout>} />
        <Route path="/experiments" element={<Layout><Experiments /></Layout>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
