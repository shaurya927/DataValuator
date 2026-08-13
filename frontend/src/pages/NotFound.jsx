import React from 'react';
import { Link } from 'react-router-dom';

const NotFound = () => {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center p-8">
      <div className="glass-card p-12 max-w-md w-full flex flex-col items-center">
        <h1 className="text-6xl font-bold mb-4 text-emerald-400">404</h1>
        <h2 className="text-2xl font-semibold mb-6">Page not found</h2>
        <p className="text-slate-400 mb-8">
          The page you are looking for doesn't exist or has been moved.
        </p>
        <Link to="/dashboard" className="btn-primary">
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
};

export default NotFound;
