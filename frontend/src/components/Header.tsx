import React, { useState } from 'react';
import { apiClient } from '../api/client';

interface HeaderProps {
  totalRounds: number;
  onDirectoryChange?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ totalRounds, onDirectoryChange }) => {
  const [isIngesting, setIsIngesting] = useState(false);
  const [showDirectoryInput, setShowDirectoryInput] = useState(false);
  const [directoryPath, setDirectoryPath] = useState('');
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const handleIngestDirectory = async () => {
    if (!directoryPath.trim()) {
      setMessage({ text: 'Please enter a directory path', type: 'error' });
      return;
    }

    setIsIngesting(true);
    try {
      const result = await apiClient.ingestDirectory({ dir: directoryPath });
      setMessage({
        text: `Ingested ${result.ingested} new images, ${result.duplicates} duplicates found, ${result.existing} already existed`,
        type: 'success',
      });
      setShowDirectoryInput(false);
      setDirectoryPath('');
      onDirectoryChange?.();
    } catch (error) {
      setMessage({
        text: error instanceof Error ? error.message : 'Failed to ingest directory',
        type: 'error',
      });
    } finally {
      setIsIngesting(false);
    }
  };

  const clearMessage = () => setMessage(null);

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-gray-900">
              Image Preference Picker
            </h1>
            <div className="ml-6 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
              Round {totalRounds}
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {!showDirectoryInput ? (
              <button
                onClick={() => setShowDirectoryInput(true)}
                className="btn-secondary text-sm"
                disabled={isIngesting}
              >
                Change Folder
              </button>
            ) : (
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  value={directoryPath}
                  onChange={(e) => setDirectoryPath(e.target.value)}
                  placeholder="Enter directory path..."
                  className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleIngestDirectory();
                    if (e.key === 'Escape') {
                      setShowDirectoryInput(false);
                      setDirectoryPath('');
                    }
                  }}
                  autoFocus
                />
                <button
                  onClick={handleIngestDirectory}
                  disabled={isIngesting}
                  className="btn-primary text-sm"
                >
                  {isIngesting ? 'Ingesting...' : 'Ingest'}
                </button>
                <button
                  onClick={() => {
                    setShowDirectoryInput(false);
                    setDirectoryPath('');
                  }}
                  className="btn-secondary text-sm"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Toast Message */}
      {message && (
        <div className={`fixed top-20 right-4 max-w-md p-4 rounded-lg shadow-lg z-50 animate-slide-up ${
          message.type === 'success' ? 'bg-green-100 text-green-800 border border-green-200' : 'bg-red-100 text-red-800 border border-red-200'
        }`}>
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">{message.text}</p>
            <button
              onClick={clearMessage}
              className="ml-3 text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          </div>
        </div>
      )}
    </header>
  );
};