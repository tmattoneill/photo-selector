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
  ResetResponse,
} from './types';

const BASE_URL = '/api';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
});

// Helper function for constructing image URLs
export const getImageUrl = (imagePath: string): string => {
  return imagePath; // Use relative paths for nginx proxy
};

export const apiClient = {
  async healthCheck(): Promise<{ status: string }> {
    const response = await api.get('/health');
    return response.data;
  },

  async getPair(): Promise<PairResponse> {
    try {
      const response = await api.get('/pair');
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        // Re-throw with the server's detailed error message
        throw new Error(error.response.data.detail);
      }
      throw error;
    }
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

  async downloadPortfolio(portfolioId: string): Promise<void> {
    const response = await api.get(`/portfolio/${portfolioId}/download`, {
      responseType: 'blob'
    });
    
    // Create a download link and trigger it
    const blob = new Blob([response.data], { type: 'application/zip' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    
    // Get filename from Content-Disposition header or use default
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'portfolio.zip';
    if (contentDisposition) {
      const matches = /filename="?([^"]+)"?/i.exec(contentDisposition);
      if (matches) {
        filename = matches[1];
      }
    }
    
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },


  async resetGalleryData(): Promise<ResetResponse> {
    const response = await api.post('/reset');
    return response.data;
  },
};

export default apiClient;