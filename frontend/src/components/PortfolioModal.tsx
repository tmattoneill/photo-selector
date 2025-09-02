import React, { useState } from 'react';
import { apiClient } from '../api/client';
import type { CreatePortfolioRequest } from '../api/types';

interface PortfolioModalProps {
  imageIds: string[];
  onClose: () => void;
  onSuccess: () => void;
}

export const PortfolioModal: React.FC<PortfolioModalProps> = ({
  imageIds,
  onClose,
  onSuccess,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [portfolioId, setPortfolioId] = useState<string | null>(null);
  const [downloadResult, setDownloadResult] = useState<string | null>(null);

  const handleCreatePortfolio = async () => {
    if (!name.trim()) {
      setError('Please enter a portfolio name');
      return;
    }

    setIsCreating(true);
    setError(null);

    try {
      const request: CreatePortfolioRequest = {
        name: name.trim(),
        description: description.trim() || undefined,
        image_ids: imageIds,
      };

      const response = await apiClient.createPortfolio(request);
      setPortfolioId(response.portfolio_id);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create portfolio');
    } finally {
      setIsCreating(false);
    }
  };

  const handleDownloadPortfolio = async () => {
    if (!portfolioId) return;

    setIsDownloading(true);
    setError(null);

    try {
      await apiClient.downloadPortfolio(portfolioId);
      setDownloadResult(`Successfully downloaded portfolio "${name}" as a zip file`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download portfolio');
    } finally {
      setIsDownloading(false);
    }
  };

  const handleComplete = () => {
    onSuccess();
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900">
              Create Portfolio
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="mb-4">
            <p className="text-sm text-gray-600 mb-4">
              Creating portfolio with {imageIds.length} selected images
            </p>
          </div>

          {!portfolioId ? (
            // Step 1: Create Portfolio
            <>
              <div className="space-y-4">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                    Portfolio Name *
                  </label>
                  <input
                    id="name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Enter portfolio name..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    maxLength={255}
                  />
                </div>

                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                    Description (optional)
                  </label>
                  <textarea
                    id="description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Enter description..."
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  />
                </div>
              </div>

              {error && (
                <div className="mt-4 bg-red-100 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">
                  {error}
                </div>
              )}

              <div className="flex items-center justify-end space-x-3 mt-6">
                <button
                  onClick={onClose}
                  className="btn-secondary"
                  disabled={isCreating}
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreatePortfolio}
                  disabled={isCreating || !name.trim()}
                  className="btn-primary"
                >
                  {isCreating ? 'Creating...' : 'Create Portfolio'}
                </button>
              </div>
            </>
          ) : (
            // Step 2: Download Portfolio
            <>
              {!downloadResult ? (
                <>
                  <div className="mb-4">
                    <div className="bg-green-100 border border-green-200 text-green-700 px-3 py-2 rounded-lg text-sm mb-4">
                      ✅ Portfolio "{name}" created successfully!
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="text-center">
                      <p className="text-gray-700 mb-4">
                        Ready to download your portfolio as a zip file?
                      </p>
                      <p className="text-sm text-gray-500">
                        The zip file will contain all {imageIds.length} selected images and will be saved to your browser's default download folder.
                      </p>
                    </div>
                  </div>

                  {error && (
                    <div className="mt-4 bg-red-100 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">
                      {error}
                    </div>
                  )}

                  <div className="flex items-center justify-end space-x-3 mt-6">
                    <button
                      onClick={handleComplete}
                      className="btn-secondary"
                      disabled={isDownloading}
                    >
                      Skip Download
                    </button>
                    <button
                      onClick={handleDownloadPortfolio}
                      disabled={isDownloading}
                      className="btn-primary"
                    >
                      {isDownloading ? 'Downloading...' : '📁 Download Portfolio'}
                    </button>
                  </div>
                </>
              ) : (
                // Step 3: Success
                <>
                  <div className="bg-green-100 border border-green-200 text-green-700 px-3 py-2 rounded-lg text-sm mb-4">
                    ✅ {downloadResult}
                  </div>

                  <div className="flex items-center justify-end space-x-3 mt-6">
                    <button
                      onClick={handleComplete}
                      className="btn-primary"
                    >
                      Done
                    </button>
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};