import React from 'react';
import type { ImageData } from '../api/types';
import { getImageUrl } from '../api/client';

interface ImageCardProps {
  image: ImageData;
  title: string;
  onClick: () => void;
  className?: string;
}

export const ImageCard: React.FC<ImageCardProps> = ({
  image,
  title,
  onClick,
  className = '',
}) => {
  return (
    <div
      className={`image-card cursor-pointer ${className}`}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
      aria-label={`Select ${title}`}
    >
      <div className="aspect-square overflow-hidden rounded-lg bg-gray-100">
        <img
          src={getImageUrl(image.base64)}
          alt={title}
          className="w-full h-full object-cover transition-transform hover:scale-105"
          loading="lazy"
        />
      </div>
      <div className="mt-3 text-center">
        <h3 className="text-lg font-medium text-gray-900">{title}</h3>
        <p className="text-sm text-gray-500 mt-1">
          {image.w} × {image.h}
        </p>
      </div>
    </div>
  );
};