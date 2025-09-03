import React, { useState } from 'react';

interface ProgressBarProps {
  progress: number;
  portfolioReady: boolean;
  quality: string;
  onClick?: () => void;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  portfolioReady,
  quality,
  onClick
}) => {
  const [isHovered, setIsHovered] = useState(false);

  // Get color scheme based on progress
  const getColorScheme = () => {
    if (progress >= 85) {
      return {
        gradient: 'from-blue-500 to-blue-400',
        glow: 'shadow-blue-400/30',
        text: 'text-white',
        bg: 'bg-blue-50'
      };
    } else if (progress >= 67) {
      return {
        gradient: 'from-green-500 to-green-400',
        glow: 'shadow-green-400/30',
        text: 'text-white',
        bg: 'bg-green-50'
      };
    } else if (progress >= 34) {
      return {
        gradient: 'from-yellow-500 to-yellow-400',
        glow: 'shadow-yellow-400/30',
        text: 'text-white',
        bg: 'bg-yellow-50'
      };
    } else {
      return {
        gradient: 'from-red-500 to-red-400',
        glow: 'shadow-red-400/30',
        text: 'text-white',
        bg: 'bg-red-50'
      };
    }
  };

  const colorScheme = getColorScheme();
  
  // Calculate estimated remaining comparisons (rough estimate)
  const remainingComparisons = Math.max(0, Math.round((100 - progress) * 2));

  // Get milestone indicators
  const milestones = [25, 50, 75, 85];
  
  // Quality message
  const getQualityMessage = () => {
    switch (quality) {
      case 'excellent': return 'Excellent results!';
      case 'very good': return 'Portfolio ready!';
      case 'good': return 'Good progress';
      case 'fair': return 'Making progress';
      case 'early': return 'Just getting started';
      default: return 'Building portfolio';
    }
  };

  return (
    <div
      className={`relative group cursor-pointer transition-all duration-300 ${
        isHovered ? 'scale-105' : ''
      }`}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Main Progress Bar */}
      <div 
        className={`
          relative w-48 h-7 rounded-full overflow-hidden backdrop-blur-sm
          border border-white/20 ${colorScheme.bg}
          transition-all duration-500 ease-out
          ${isHovered ? `shadow-lg ${colorScheme.glow}` : 'shadow-sm'}
        `}
      >
        {/* Background with subtle pattern */}
        <div className="absolute inset-0 bg-gradient-to-r from-gray-100 to-gray-50 opacity-50" />
        
        {/* Milestone markers */}
        {milestones.map((milestone) => (
          <div
            key={milestone}
            className={`
              absolute top-0 bottom-0 w-0.5 bg-gray-300/50
              transition-opacity duration-300
              ${progress >= milestone ? 'opacity-100' : 'opacity-30'}
            `}
            style={{ left: `${milestone}%` }}
          />
        ))}
        
        {/* Progress fill with gradient */}
        <div
          className={`
            absolute left-0 top-0 bottom-0 
            bg-gradient-to-r ${colorScheme.gradient}
            transition-all duration-700 ease-out
            ${portfolioReady ? 'animate-pulse' : ''}
          `}
          style={{ width: `${Math.min(progress, 100)}%` }}
        >
          {/* Shimmer effect */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -skew-x-12 animate-shimmer" />
        </div>
        
        {/* Progress text */}
        <div className={`
          absolute inset-0 flex items-center justify-center
          text-xs font-semibold ${colorScheme.text}
          drop-shadow-sm transition-all duration-300
        `}>
          {progress >= 85 ? '✨' : ''} {progress.toFixed(0)}%
        </div>
      </div>

      {/* Tooltip on hover */}
      {isHovered && (
        <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 z-50">
          <div className="bg-gray-900 text-white text-xs rounded-lg px-3 py-2 shadow-lg whitespace-nowrap">
            <div className="font-semibold">{getQualityMessage()}</div>
            <div className="text-gray-300 mt-1">
              {remainingComparisons > 0 ? 
                `~${remainingComparisons} more comparisons` : 
                'Portfolio complete!'
              }
            </div>
            {portfolioReady && (
              <div className="text-blue-300 mt-1">🎯 Ready to create portfolio</div>
            )}
            {/* Tooltip arrow */}
            <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-gray-900 rotate-45" />
          </div>
        </div>
      )}
    </div>
  );
};