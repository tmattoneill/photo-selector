import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Header } from '../components/Header';
import { PairSelector } from '../components/PairSelector';
import { ResetButton } from '../components/ResetButton';
import { apiClient } from '../api/client';
import type { PairResponse, Selection } from '../api/types';

export const Home: React.FC = () => {
  const [pair, setPair] = useState<PairResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalRounds, setTotalRounds] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const loadPair = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const newPair = await apiClient.getPair();
      setPair(newPair);
      setTotalRounds(newPair.round);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load image pair';
      
      // Check if this is a "no images" state rather than an actual error
      if (errorMessage.includes('No images found') || errorMessage.includes('Not enough images')) {
        setPair(null);  // Trigger the welcome screen instead of error screen
        setError(null);
      } else {
        setError(errorMessage);
      }
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
          left_sha256: pair.left.sha256,
          right_sha256: pair.right.sha256,
          selection,
        });

        // Update round counter immediately
        setTotalRounds(prev => prev + 1);

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

  const handleDirectoryUpload = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) {
      return;
    }

    // Filter for image files only
    const imageFiles = Array.from(files).filter(file => 
      file.type.startsWith('image/') && 
      ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'].includes(file.type)
    );

    if (imageFiles.length === 0) {
      setUploadMessage({
        text: 'No image files found in selected directory',
        type: 'error',
      });
      return;
    }

    setIsUploading(true);
    setUploadMessage({
      text: `Processing ${imageFiles.length} images...`,
      type: 'success',
    });

    try {
      // Upload images in batches to avoid size limits
      const batchSize = 3;
      let totalUploaded = 0;
      const errors: string[] = [];

      for (let i = 0; i < imageFiles.length; i += batchSize) {
        const batch = imageFiles.slice(i, i + batchSize);
        
        const formData = new FormData();
        batch.forEach((file) => {
          formData.append(`images`, file);
        });

        try {
          const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
          });

          if (!response.ok) {
            const errorText = await response.text();
            errors.push(`Batch ${Math.floor(i/batchSize) + 1}: ${errorText}`);
            continue;
          }

          const result = await response.json();
          totalUploaded += result.uploaded;
          
          // Update progress message
          setUploadMessage({
            text: `Uploaded ${totalUploaded} of ${imageFiles.length} images...`,
            type: 'success',
          });
          
        } catch (batchError) {
          errors.push(`Batch ${Math.floor(i/batchSize) + 1}: ${batchError}`);
        }
      }

      if (totalUploaded > 0) {
        setUploadMessage({
          text: `Successfully uploaded ${totalUploaded} images${errors.length > 0 ? ` (${errors.length} batches failed)` : ''}`,
          type: totalUploaded === imageFiles.length ? 'success' : 'error',
        });
        // Load the first pair after successful upload
        await loadPair();
      } else {
        setUploadMessage({
          text: `Failed to upload images: ${errors.join('; ')}`,
          type: 'error',
        });
      }
      
    } catch (error) {
      setUploadMessage({
        text: error instanceof Error ? error.message : 'Failed to upload images',
        type: 'error',
      });
    } finally {
      setIsUploading(false);
      // Reset the file input
      event.target.value = '';
    }
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
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <Header totalRounds={totalRounds} onDirectoryChange={handleDirectoryChange} />
        <div className="flex items-center justify-center min-h-[calc(100vh-4rem)]">
          <div className="text-center max-w-2xl mx-auto px-6">
            <div className="text-6xl mb-6">🎯</div>
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              Welcome to Image Preference Picker
            </h1>
            <p className="text-xl text-gray-700 mb-8 leading-relaxed">
              Build your perfect image portfolio through smart pairwise comparisons using advanced Elo ranking.
            </p>
            
            <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">Get Started</h2>
              <div className="space-y-4 text-left">
                <div className="flex items-start space-x-3">
                  <div className="bg-blue-100 rounded-full p-2 mt-1">
                    <span className="text-blue-600 font-bold text-sm">1</span>
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Choose Your Images</h3>
                    <p className="text-gray-600 text-sm">Click "📁 Select Image Folder" to choose a directory, or "🖼️ Select Images" to pick individual files</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="bg-blue-100 rounded-full p-2 mt-1">
                    <span className="text-blue-600 font-bold text-sm">2</span>
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Make Comparisons</h3>
                    <p className="text-gray-600 text-sm">Compare image pairs and pick your favorites using keyboard shortcuts (1, 2, 3)</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="bg-blue-100 rounded-full p-2 mt-1">
                    <span className="text-blue-600 font-bold text-sm">3</span>
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Build Your Portfolio</h3>
                    <p className="text-gray-600 text-sm">Export your top-rated images or create custom portfolios to save locally</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-x-4 flex flex-wrap justify-center gap-4">
              {/* Folder Selection */}
              <input
                type="file"
                id="welcome-directory-picker"
                {...({ webkitdirectory: "" } as any)}
                {...({ directory: "" } as any)}
                multiple
                onChange={handleDirectoryUpload}
                disabled={isUploading}
                className="hidden"
                accept="image/*"
              />
              <label
                htmlFor="welcome-directory-picker"
                className={`bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors inline-flex items-center space-x-2 cursor-pointer ${
                  isUploading ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                <span>📁</span>
                <span>{isUploading ? 'Processing...' : 'Select Image Folder'}</span>
              </label>

              {/* Individual Files Selection */}
              <input
                type="file"
                id="welcome-files-picker"
                multiple
                onChange={handleDirectoryUpload}
                disabled={isUploading}
                className="hidden"
                accept="image/jpeg,image/jpg,image/png,image/webp,image/gif"
              />
              <label
                htmlFor="welcome-files-picker"
                className={`bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors inline-flex items-center space-x-2 cursor-pointer ${
                  isUploading ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                <span>🖼️</span>
                <span>{isUploading ? 'Processing...' : 'Select Images'}</span>
              </label>

              <Link to="/gallery" className="btn-secondary inline-block py-3 px-6">
                View Gallery
              </Link>
            </div>

            {/* Upload Status Message */}
            {uploadMessage && (
              <div className={`mt-6 p-4 rounded-lg ${
                uploadMessage.type === 'success' ? 'bg-green-100 text-green-800 border border-green-200' : 'bg-red-100 text-red-800 border border-red-200'
              }`}>
                <p className="text-sm font-medium">{uploadMessage.text}</p>
              </div>
            )}
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
        <div className="flex items-center justify-between">
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
          
          <div className="flex items-center">
            <ResetButton />
          </div>
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