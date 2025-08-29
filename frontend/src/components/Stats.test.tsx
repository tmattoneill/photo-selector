import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Stats } from './Stats';
import type { StatsResponse } from '../api/types';

const mockStats: StatsResponse = {
  images: 10,
  duplicates: 2,
  rounds: 5,
  by_image: [
    {
      image_id: '1',
      sha256: 'abc123',
      file_path: '/path/to/image1.jpg',
      likes: 3,
      unlikes: 1,
      skips: 0,
      exposures: 4
    },
    {
      image_id: '2',
      sha256: 'def456',
      file_path: '/path/to/image2.jpg',
      likes: 1,
      unlikes: 2,
      skips: 1,
      exposures: 4
    }
  ]
};

describe('Stats Component', () => {
  it('renders statistics correctly', () => {
    render(<Stats stats={mockStats} />);
    
    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getByText('Total Images')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('Duplicates Found')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('Rounds Completed')).toBeInTheDocument();
  });

  it('displays most liked images', () => {
    render(<Stats stats={mockStats} />);
    
    expect(screen.getByText('Most Liked Images')).toBeInTheDocument();
    expect(screen.getByText('image1.jpg')).toBeInTheDocument();
    expect(screen.getByText('image2.jpg')).toBeInTheDocument();
  });
});