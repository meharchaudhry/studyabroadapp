import apiClient from './client';

export const universitiesAPI = {
  getCountries: async () => {
    const res = await apiClient.get('/universities/countries');
    return res.data;
  },
  getFinanceBenchmarks: async () => {
    const res = await apiClient.get('/universities/finance/benchmarks');
    return res.data;
  },
  // Fast rule-based recommendations — includes match_score, top_reason, match_label
  getRecommendations: async (limit = 15) => {
    const res = await apiClient.get('/universities/recommendations', { params: { limit } });
    return res.data;
  },
  list: async (params = {}) => {
    const res = await apiClient.get('/universities', { params });
    return res.data;
  },
  getById: async (id) => {
    const res = await apiClient.get(`/universities/${id}`);
    return res.data;
  },
  // Detailed match explanation — includes AI analysis (Gemini)
  explain: async (id) => {
    const res = await apiClient.get(`/universities/${id}/explain`);
    return res.data;
  },
};
