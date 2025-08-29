import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Stats } from '../components/Stats';
import { apiClient } from '../api/client';
import type { StatsResponse } from '../api/types';

export const StatsPage: React.FC = () => {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadStats = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const statsData = await apiClient.getStats();
        setStats(statsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load statistics');
        console.error('Failed to load stats:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadStats();
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center space-x-6">
                <h1 className="text-2xl font-bold text-gray-900">Statistics</h1>
                <nav className="flex space-x-4">
                  <Link to="/" className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                    Home
                  </Link>
                  <span className="text-gray-900 px-3 py-2 rounded-md text-sm font-medium bg-gray-100">
                    Stats
                  </span>
                  <Link to="/gallery" className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                    Gallery
                  </Link>
                </nav>
              </div>
            </div>
          </div>
        </header>
        <div className="flex items-center justify-center min-h-[calc(100vh-4rem)]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading statistics...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center space-x-6">
                <h1 className="text-2xl font-bold text-gray-900">Statistics</h1>
                <nav className="flex space-x-4">
                  <Link to="/" className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                    Home
                  </Link>
                  <span className="text-gray-900 px-3 py-2 rounded-md text-sm font-medium bg-gray-100">
                    Stats
                  </span>
                  <Link to="/gallery" className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                    Gallery
                  </Link>
                </nav>
              </div>
            </div>
          </div>
        </header>
        <div className="flex items-center justify-center min-h-[calc(100vh-4rem)]">
          <div className="text-center max-w-md">
            <div className="text-red-600 text-6xl mb-4">⚠️</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Failed to Load Stats</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <div className="space-x-4">
              <button onClick={() => window.location.reload()} className="btn-primary">
                Try Again
              </button>
              <Link to="/" className="btn-secondary inline-block">
                Back to Picker
              </Link>
              <Link to="/gallery" className="btn-secondary inline-block">
                View Gallery
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <h1 className="text-2xl font-bold text-gray-900">Statistics</h1>
            <Link to="/" className="btn-secondary">
              Back to Picker
            </Link>
          </div>
        </div>
      </header>
      {stats && <Stats stats={stats} />}
    </div>
  );
};