import apiClient from './client';

export const universitiesAPI = {
  getCountries: async () => {
    const res = await apiClient.get('/universities/countries');
    return res.data;
  },
  getRecommendations: async () => {
    const res = await apiClient.post('/universities/recommendations');
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
};
