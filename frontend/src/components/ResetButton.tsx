import React, { useState } from 'react';
import { apiClient } from '../api/client';

export const ResetButton: React.FC = () => {
  const [isResetting, setIsResetting] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [resetResult, setResetResult] = useState<string | null>(null);

  const handleReset = async () => {
    setIsResetting(true);
    setResetResult(null);
    
    try {
      await apiClient.resetGalleryData();
      setResetResult(`✅ Reset successful! Redirecting to start...`);
      setShowConfirmation(false);
      
      // Reload the page after successful reset to show welcome screen
      setTimeout(() => {
        window.location.reload();
      }, 1500);
      
    } catch (err) {
      setResetResult(`❌ Reset failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsResetting(false);
    }
  };

  const handleConfirm = () => {
    setShowConfirmation(true);
  };

  const handleCancel = () => {
    setShowConfirmation(false);
  };

  return (
    <div className="relative">
      {!showConfirmation ? (
        <button
          onClick={handleConfirm}
          disabled={isResetting}
          className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
        >
          🔄 Reset Gallery
        </button>
      ) : (
        <div className="bg-white border border-red-200 rounded-lg p-4 shadow-lg min-w-[300px]">
          <div className="mb-3">
            <h3 className="font-semibold text-red-800 mb-2">⚠️ Confirm Reset</h3>
            <p className="text-sm text-gray-700 mb-2">
              This will permanently clear:
            </p>
            <ul className="text-xs text-gray-600 list-disc list-inside mb-3">
              <li>All uploaded images and files</li>
              <li>All likes, unlikes, skips, and exposures</li>
              <li>All choice history and round data</li>
              <li>All portfolios and galleries</li>
              <li>Everything - complete fresh start</li>
            </ul>
            <p className="text-sm text-red-600 font-medium">
              This action cannot be undone!
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={handleReset}
              disabled={isResetting}
              className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm font-medium disabled:opacity-50"
            >
              {isResetting ? 'Resetting...' : 'Yes, Reset All'}
            </button>
            <button
              onClick={handleCancel}
              disabled={isResetting}
              className="bg-gray-300 hover:bg-gray-400 text-gray-700 px-3 py-1 rounded text-sm font-medium disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {resetResult && (
        <div className="absolute top-full left-0 mt-2 bg-white border rounded-lg p-3 shadow-lg min-w-[300px] z-10">
          <div className="text-sm font-medium">
            {resetResult}
          </div>
        </div>
      )}
    </div>
  );
};