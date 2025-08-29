import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Header } from '../components/Header';
import { PairSelector } from '../components/PairSelector';
import { apiClient } from '../api/client';
import type { PairResponse, Selection } from '../api/types';

export const Home: React.FC = () => {
  const [pair, setPair] = useState<PairResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalRounds, setTotalRounds] = useState(0);

  const loadPair = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const newPair = await apiClient.getPair();
      setPair(newPair);
      setTotalRounds(newPair.round);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load image pair');
      console.error('Failed to load pair:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleSelection = useCallback(
    async (selection: Selection) => {
      if (!pair || isSubmitting) return;

      setIsSubmitting(true);
      try {
        await apiClient.submitChoice({
          round: pair.round,
          left_id: pair.left.image_id,
          right_id: pair.right.image_id,
          selection,
        });

        // Load next pair
        await loadPair();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to submit choice');
        console.error('Failed to submit choice:', err);
      } finally {
        setIsSubmitting(false);
      }
    },
    [pair, isSubmitting, loadPair]
  );

  const handleDirectoryChange = useCallback(() => {
    loadPair();
  }, [loadPair]);

  useEffect(() => {
    loadPair();
  }, [loadPair]);

  if (isLoading && !pair) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header totalRounds={totalRounds} onDirectoryChange={handleDirectoryChange} />
        <div className="flex items-center justify-center min-h-[calc(100vh-4rem)]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading images...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header totalRounds={totalRounds} onDirectoryChange={handleDirectoryChange} />
        <div className="flex items-center justify-center min-h-[calc(100vh-4rem)]">
          <div className="text-center max-w-md">
            <div className="text-red-600 text-6xl mb-4">⚠️</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Something went wrong</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <div className="space-x-4">
              <button onClick={loadPair} className="btn-primary">
                Try Again
              </button>
              <Link to="/stats" className="btn-secondary inline-block">
                View Stats
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

  if (!pair) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header totalRounds={totalRounds} onDirectoryChange={handleDirectoryChange} />
        <div className="flex items-center justify-center min-h-[calc(100vh-4rem)]">
          <div className="text-center max-w-md">
            <div className="text-gray-400 text-6xl mb-4">📁</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">No Images Available</h2>
            <p className="text-gray-600 mb-6">
              Please ingest a directory containing images to start comparing.
            </p>
            <div className="space-x-4">
              <Link to="/stats" className="btn-secondary inline-block">
                View Stats
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
      <Header totalRounds={totalRounds} onDirectoryChange={handleDirectoryChange} />
      
      {/* Navigation */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center space-x-6">
          <Link
            to="/stats"
            className="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            📊 View Statistics
          </Link>
          <Link
            to="/gallery"
            className="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            🖼️ View Gallery
          </Link>
        </div>
      </div>

      {/* Main Content */}
      <main className="py-8">
        <PairSelector
          pair={pair}
          onSelection={handleSelection}
          isSubmitting={isSubmitting}
        />
      </main>
    </div>
  );
};