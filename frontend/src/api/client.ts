import axios from 'axios';
import type {
  PairResponse,
  ChoiceRequest,
  ChoiceResponse,
  DirectoryRequest,
  DirectoryResponse,
  StatsResponse,
  GalleryResponse,
  GalleryFilter,
  CreatePortfolioRequest,
  PortfolioResponse,
  ExportPortfolioRequest,
  ExportResponse,
  ResetResponse,
} from './types';

const BASE_URL = 'http://localhost:8000/api';
const BACKEND_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
});

// Helper function for constructing image URLs
export const getImageUrl = (imagePath: string): string => {
  return `${BACKEND_URL}${imagePath}`;
};

export const apiClient = {
  async healthCheck(): Promise<{ status: string }> {
    const response = await api.get('/health');
    return response.data;
  },

  async getPair(): Promise<PairResponse> {
    const response = await api.get('/pair');
    return response.data;
  },

  async submitChoice(choice: ChoiceRequest): Promise<ChoiceResponse> {
    const response = await api.post('/choice', choice);
    return response.data;
  },

  async setDirectory(request: DirectoryRequest): Promise<DirectoryResponse> {
    const response = await api.post('/directory', request);
    return response.data;
  },

  async getStats(): Promise<StatsResponse> {
    const response = await api.get('/stats');
    return response.data;
  },

  async getGalleryImages(filter: GalleryFilter, limit: number = 20, offset: number = 0): Promise<GalleryResponse> {
    const response = await api.get('/gallery', {
      params: { filter, limit, offset }
    });
    return response.data;
  },

  async createPortfolio(request: CreatePortfolioRequest): Promise<PortfolioResponse> {
    const response = await api.post('/portfolio', request);
    return response.data;
  },

  async getPortfolio(portfolioId: string): Promise<PortfolioResponse> {
    const response = await api.get(`/portfolio/${portfolioId}`);
    return response.data;
  },

  async exportPortfolio(portfolioId: string, request: ExportPortfolioRequest): Promise<ExportResponse> {
    const response = await api.post(`/portfolio/${portfolioId}/export`, request);
    return response.data;
  },

  async resetGalleryData(): Promise<ResetResponse> {
    const response = await api.post('/reset');
    return response.data;
  },
};

export default apiClient;