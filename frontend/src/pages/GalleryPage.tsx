import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiClient, getImageUrl } from '../api/client';
import type { GalleryImage, GalleryFilter } from '../api/types';
import { PortfolioModal } from '../components/PortfolioModal';

export const GalleryPage: React.FC = () => {
  const [images, setImages] = useState<GalleryImage[]>([]);
  const [filter, setFilter] = useState<GalleryFilter>('liked');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedImages, setSelectedImages] = useState<Set<string>>(new Set());
  const [showPortfolioModal, setShowPortfolioModal] = useState(false);
  const [total, setTotal] = useState(0);
  const limit = 20;

  const loadImages = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.getGalleryImages(filter, limit);
      setImages(response.images);
      setTotal(response.total);
      setSelectedImages(new Set()); // Clear selection when filter changes
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load images');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadImages();
  }, [filter]);

  const handleImageSelect = (imageId: string) => {
    const newSelection = new Set(selectedImages);
    if (newSelection.has(imageId)) {
      newSelection.delete(imageId);
    } else {
      newSelection.add(imageId);
    }
    setSelectedImages(newSelection);
  };

  const handleSelectAll = () => {
    if (selectedImages.size === images.length) {
      setSelectedImages(new Set());
    } else {
      setSelectedImages(new Set(images.map(img => img.image_id)));
    }
  };

  const handleCreatePortfolio = () => {
    if (selectedImages.size === 0) {
      return; // Button is disabled, but handle gracefully
    }
    setShowPortfolioModal(true);
  };

  const handlePortfolioCreated = () => {
    setShowPortfolioModal(false);
    setSelectedImages(new Set());
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-6">
              <h1 className="text-2xl font-bold text-gray-900">Gallery</h1>
              <nav className="flex space-x-4">
                <Link to="/" className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                  Home
                </Link>
                <Link to="/stats" className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                  Stats
                </Link>
                <span className="text-gray-900 px-3 py-2 rounded-md text-sm font-medium bg-gray-100">
                  Gallery
                </span>
              </nav>
            </div>

            <div className="flex items-center space-x-4">
              {/* Filter Dropdown */}
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value as GalleryFilter)}
                className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="liked">Liked Images</option>
                <option value="skipped">Skipped Images</option>
              </select>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Controls */}
        {!loading && images.length > 0 && (
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">
                {total} {filter} images found
              </span>
              <button
                onClick={handleSelectAll}
                className="text-blue-600 hover:text-blue-700 text-sm font-medium"
              >
                {selectedImages.size === images.length ? 'Deselect All' : 'Select All'}
              </button>
            </div>

            <div className="flex items-center space-x-4">
              {selectedImages.size > 0 && (
                <span className="text-gray-700">
                  {selectedImages.size} selected
                </span>
              )}
              <div className="flex flex-col items-end">
                <button
                  onClick={handleCreatePortfolio}
                  disabled={selectedImages.size === 0}
                  className={`${
                    selectedImages.size > 0 
                      ? 'btn-primary' 
                      : 'px-4 py-2 bg-gray-300 text-gray-500 rounded-lg cursor-not-allowed'
                  }`}
                >
                  Create Portfolio
                </button>
                {selectedImages.size === 0 && (
                  <span className="text-xs text-gray-500 mt-1">
                    Select images to create portfolio
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="text-gray-600">Loading images...</div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-100 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            Error: {error}
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && images.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-500 mb-4">
              {filter === 'liked' ? 'No liked images found' : 'No skipped images found'}
            </div>
            <Link to="/" className="text-blue-600 hover:text-blue-700">
              Go back to image selection
            </Link>
          </div>
        )}

        {/* Image Grid */}
        {!loading && images.length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {images.map((image) => (
              <div
                key={image.image_id}
                className={`relative group cursor-pointer rounded-lg overflow-hidden shadow-md hover:shadow-lg transition-all ${
                  selectedImages.has(image.image_id) ? 'ring-4 ring-blue-500' : ''
                }`}
                onClick={() => handleImageSelect(image.image_id)}
              >
                <img
                  src={getImageUrl(image.base64_data)}
                  alt={`Image ${image.sha256.substring(0, 8)}`}
                  className="w-full h-48 object-cover"
                />
                
                {/* Overlay with stats */}
                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-all">
                  <div className="absolute top-2 left-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="bg-white bg-opacity-90 rounded px-2 py-1 text-xs">
                      {filter === 'liked' ? (
                        <span className="text-green-700">👍 {image.likes}</span>
                      ) : (
                        <span className="text-orange-700">⏭️ {image.skips}</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Selection checkbox */}
                <div className="absolute top-2 right-2">
                  <div className={`w-6 h-6 rounded border-2 flex items-center justify-center ${
                    selectedImages.has(image.image_id)
                      ? 'bg-blue-500 border-blue-500 text-white'
                      : 'bg-white border-gray-300 group-hover:border-blue-400'
                  }`}>
                    {selectedImages.has(image.image_id) && (
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Portfolio Creation Modal */}
      {showPortfolioModal && (
        <PortfolioModal
          imageIds={Array.from(selectedImages)}
          onClose={() => setShowPortfolioModal(false)}
          onSuccess={handlePortfolioCreated}
        />
      )}
    </div>
  );
};