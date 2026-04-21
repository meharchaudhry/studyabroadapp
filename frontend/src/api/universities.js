import apiClient from './client';

export const universitiesAPI = {
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
  explain: async (id) => {
    const res = await apiClient.get(`/universities/${id}/explain`);
    return res.data;
  },
};
