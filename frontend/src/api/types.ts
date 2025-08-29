export interface ImageData {
  image_id: string;
  sha256: string;
  base64: string;
  w: number;
  h: number;
}

export interface PairResponse {
  round: number;
  left: ImageData;
  right: ImageData;
}

export interface ChoiceRequest {
  round: number;
  left_id: string;
  right_id: string;
  selection: 'LEFT' | 'RIGHT' | 'SKIP';
}

export interface ChoiceResponse {
  saved: boolean;
  next_round: number;
}

export interface IngestRequest {
  dir: string;
}

export interface IngestResponse {
  ingested: number;
  duplicates: number;
  existing: number;
}

export interface ImageStats {
  image_id: string;
  sha256: string;
  file_path: string;
  likes: number;
  unlikes: number;
  skips: number;
  exposures: number;
}

export interface StatsResponse {
  images: number;
  duplicates: number;
  rounds: number;
  by_image: ImageStats[];
}

export type Selection = 'LEFT' | 'RIGHT' | 'SKIP';

// Gallery types
export interface GalleryImage {
  image_id: string;
  sha256: string;
  file_path: string;
  likes: number;
  unlikes: number;
  skips: number;
  exposures: number;
  base64_data: string;
  created_at: string;
}

export interface GalleryResponse {
  images: GalleryImage[];
  total: number;
  offset: number;
  limit: number;
}

export type GalleryFilter = 'liked' | 'skipped';

// Portfolio types
export interface CreatePortfolioRequest {
  name: string;
  description?: string;
  image_ids: string[];
}

export interface PortfolioResponse {
  portfolio_id: string;
  name: string;
  description?: string;
  image_count: number;
  created_at: string;
}

export interface ExportPortfolioRequest {
  directory_path: string;
}

export interface ExportResponse {
  success: boolean;
  exported_count: number;
  export_path: string;
  message: string;
}