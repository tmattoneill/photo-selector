import React, { useState } from 'react';

interface HeaderProps {
  totalRounds: number;
  onDirectoryChange?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ totalRounds, onDirectoryChange }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [showUploadArea, setShowUploadArea] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);


  const handleDirectorySelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
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
      setMessage({
        text: 'No image files found in selected directory',
        type: 'error',
      });
      return;
    }

    setIsUploading(true);
    setMessage({
      text: `Processing ${imageFiles.length} images...`,
      type: 'success',
    });

    try {
      // Upload images in batches to avoid size limits
      const batchSize = 10; // Upload 10 images at a time
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
          setMessage({
            text: `Uploaded ${totalUploaded} of ${imageFiles.length} images...`,
            type: 'success',
          });
          
        } catch (batchError) {
          errors.push(`Batch ${Math.floor(i/batchSize) + 1}: ${batchError}`);
        }
      }

      if (totalUploaded > 0) {
        setMessage({
          text: `Successfully uploaded ${totalUploaded} images${errors.length > 0 ? ` (${errors.length} batches failed)` : ''}`,
          type: totalUploaded === imageFiles.length ? 'success' : 'error',
        });
        setShowUploadArea(false);
        onDirectoryChange?.();
      } else {
        setMessage({
          text: `Failed to upload images: ${errors.join('; ')}`,
          type: 'error',
        });
      }
      
    } catch (error) {
      setMessage({
        text: error instanceof Error ? error.message : 'Failed to upload images',
        type: 'error',
      });
    } finally {
      setIsUploading(false);
      // Reset the file input
      event.target.value = '';
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
            {!showUploadArea ? (
              <button
                onClick={() => setShowUploadArea(true)}
                className="btn-secondary text-sm"
                disabled={isUploading}
              >
                📁 Select Folder
              </button>
            ) : (
              <div className="flex items-center space-x-2">
                <input
                  type="file"
                  id="directory-picker"
                  {...({ webkitdirectory: "" } as any)}
                  {...({ directory: "" } as any)}
                  multiple
                  onChange={handleDirectorySelect}
                  disabled={isUploading}
                  className="hidden"
                />
                <label
                  htmlFor="directory-picker"
                  className={`px-3 py-1 border border-gray-300 rounded-lg text-sm cursor-pointer transition-colors ${
                    isUploading 
                      ? 'opacity-50 cursor-not-allowed bg-gray-100' 
                      : 'hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500'
                  }`}
                  title="Select folder containing images"
                >
                  {isUploading ? 'Processing...' : '📁 Choose Folder'}
                </label>
                <button
                  onClick={() => setShowUploadArea(false)}
                  className="btn-secondary text-sm"
                  disabled={isUploading}
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