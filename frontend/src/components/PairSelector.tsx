import React, { useState, useCallback } from 'react';
import { ImageCard } from './ImageCard';
import { useKeyboard } from '../hooks/useKeyboard';
import type { PairResponse, Selection } from '../api/types';

interface PairSelectorProps {
  pair: PairResponse;
  onSelection: (selection: Selection) => void;
  isSubmitting: boolean;
}

export const PairSelector: React.FC<PairSelectorProps> = ({
  pair,
  onSelection,
  isSubmitting,
}) => {
  const [selectedSide, setSelectedSide] = useState<Selection | null>(null);

  const handleSelection = useCallback(
    (selection: Selection) => {
      if (isSubmitting) return;
      
      setSelectedSide(selection);
      
      // Small delay for visual feedback
      setTimeout(() => {
        onSelection(selection);
        setSelectedSide(null);
      }, 150);
    },
    [onSelection, isSubmitting]
  );

  useKeyboard({
    onKeyPress: handleSelection,
    enabled: !isSubmitting,
  });

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">
          Which image do you prefer?
        </h2>
        <p className="text-gray-600">
          Use keyboard shortcuts: <kbd className="px-2 py-1 bg-gray-100 rounded text-sm">1</kbd> for left,{' '}
          <kbd className="px-2 py-1 bg-gray-100 rounded text-sm">2</kbd> for right,{' '}
          <kbd className="px-2 py-1 bg-gray-100 rounded text-sm">3</kbd> to skip
        </p>
      </div>

      {/* Image Pair */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <ImageCard
          image={pair.left}
          title="Image A"
          onClick={() => handleSelection('LEFT')}
          className={`transition-all duration-150 ${
            selectedSide === 'LEFT'
              ? 'ring-4 ring-blue-500 scale-[1.02]'
              : isSubmitting
              ? 'opacity-50 pointer-events-none'
              : 'hover:ring-2 hover:ring-blue-300'
          }`}
        />
        <ImageCard
          image={pair.right}
          title="Image B"
          onClick={() => handleSelection('RIGHT')}
          className={`transition-all duration-150 ${
            selectedSide === 'RIGHT'
              ? 'ring-4 ring-blue-500 scale-[1.02]'
              : isSubmitting
              ? 'opacity-50 pointer-events-none'
              : 'hover:ring-2 hover:ring-blue-300'
          }`}
        />
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row justify-center items-center space-y-4 sm:space-y-0 sm:space-x-6">
        <button
          onClick={() => handleSelection('LEFT')}
          disabled={isSubmitting}
          className={`btn-primary min-w-[140px] ${
            selectedSide === 'LEFT' ? 'bg-blue-700' : ''
          }`}
        >
          <span className="flex items-center justify-center">
            <kbd className="mr-2 px-1.5 py-0.5 bg-blue-500 text-white text-xs rounded">1</kbd>
            Prefer Left
          </span>
        </button>

        <button
          onClick={() => handleSelection('RIGHT')}
          disabled={isSubmitting}
          className={`btn-primary min-w-[140px] ${
            selectedSide === 'RIGHT' ? 'bg-blue-700' : ''
          }`}
        >
          <span className="flex items-center justify-center">
            <kbd className="mr-2 px-1.5 py-0.5 bg-blue-500 text-white text-xs rounded">2</kbd>
            Prefer Right
          </span>
        </button>

        <button
          onClick={() => handleSelection('SKIP')}
          disabled={isSubmitting}
          className={`btn-secondary min-w-[140px] ${
            selectedSide === 'SKIP' ? 'bg-gray-400' : ''
          }`}
        >
          <span className="flex items-center justify-center">
            <kbd className="mr-2 px-1.5 py-0.5 bg-gray-400 text-white text-xs rounded">3</kbd>
            Skip Both
          </span>
        </button>
      </div>

      {isSubmitting && (
        <div className="flex justify-center mt-6">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        </div>
      )}
    </div>
  );
};