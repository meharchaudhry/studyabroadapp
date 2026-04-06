import apiClient from './client';

export const visaAPI = {
  getCountries: async () => {
    const res = await apiClient.get('/visa/countries');
    return res.data;
  },
  getChecklist: async (country) => {
    const res = await apiClient.get(`/visa/checklist/${country}`);
    return res.data;
  },
  query: async (country, question) => {
    const res = await apiClient.post('/visa/query', { query: question, country });
    return res.data;
  },
};

export const housingAPI = {
  getCountries: async () => {
    const res = await apiClient.get('/housing/countries');
    return res.data;
  },
  getListings: async (params = {}) => {
    const res = await apiClient.get('/housing/listings', { params });
    return res.data;
  },
};

export const jobsAPI_ext = {
  getCountries: async () => {
    const res = await apiClient.get('/jobs/countries');
    return res.data;
  },
  getPortals: async (params = {}) => {
    const res = await apiClient.get('/jobs/portals', { params });
    return res.data;
  },
};
