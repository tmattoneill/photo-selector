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