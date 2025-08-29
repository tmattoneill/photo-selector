import React from 'react';
import type { StatsResponse } from '../api/types';

interface StatsProps {
  stats: StatsResponse;
}

export const Stats: React.FC<StatsProps> = ({ stats }) => {
  const topLiked = [...stats.by_image]
    .sort((a, b) => b.likes - a.likes)
    .slice(0, 5);

  const mostExposed = [...stats.by_image]
    .sort((a, b) => b.exposures - a.exposures)
    .slice(0, 5);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Statistics</h1>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-2xl font-bold text-blue-600">{stats.images}</div>
          <div className="text-gray-600">Total Images</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-2xl font-bold text-green-600">{stats.duplicates}</div>
          <div className="text-gray-600">Duplicates Found</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-2xl font-bold text-purple-600">{stats.rounds}</div>
          <div className="text-gray-600">Rounds Completed</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-2xl font-bold text-orange-600">
            {stats.by_image.reduce((sum, img) => sum + img.exposures, 0)}
          </div>
          <div className="text-gray-600">Total Exposures</div>
        </div>
      </div>

      {/* Top Lists */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Most Liked */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Most Liked Images</h2>
          </div>
          <div className="p-6">
            {topLiked.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No data available</p>
            ) : (
              <div className="space-y-4">
                {topLiked.map((image, index) => (
                  <div key={image.image_id} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <span className="w-6 h-6 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-sm font-medium mr-3">
                        {index + 1}
                      </span>
                      <div>
                        <div className="font-medium text-gray-900 truncate max-w-xs">
                          {image.file_path.split('/').pop() || 'Unknown'}
                        </div>
                        <div className="text-sm text-gray-500">
                          {image.exposures} exposures, {image.unlikes} unlikes, {image.skips} skips
                        </div>
                      </div>
                    </div>
                    <div className="text-lg font-semibold text-green-600">
                      {image.likes}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Most Exposed */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Most Exposed Images</h2>
          </div>
          <div className="p-6">
            {mostExposed.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No data available</p>
            ) : (
              <div className="space-y-4">
                {mostExposed.map((image, index) => (
                  <div key={image.image_id} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <span className="w-6 h-6 bg-purple-100 text-purple-800 rounded-full flex items-center justify-center text-sm font-medium mr-3">
                        {index + 1}
                      </span>
                      <div>
                        <div className="font-medium text-gray-900 truncate max-w-xs">
                          {image.file_path.split('/').pop() || 'Unknown'}
                        </div>
                        <div className="text-sm text-gray-500">
                          {image.likes} likes, {image.unlikes} unlikes, {image.skips} skips
                        </div>
                      </div>
                    </div>
                    <div className="text-lg font-semibold text-purple-600">
                      {image.exposures}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};