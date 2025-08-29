import axios from 'axios';
import type {
  PairResponse,
  ChoiceRequest,
  ChoiceResponse,
  IngestRequest,
  IngestResponse,
  StatsResponse,
} from './types';

const BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
});

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

  async ingestDirectory(request: IngestRequest): Promise<IngestResponse> {
    const response = await api.post('/ingest', request);
    return response.data;
  },

  async getStats(): Promise<StatsResponse> {
    const response = await api.get('/stats');
    return response.data;
  },
};

export default apiClient;