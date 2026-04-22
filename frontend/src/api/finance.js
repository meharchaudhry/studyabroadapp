import apiClient from './client';

export const financeAPI = {
  getROIAnalysis: async (data) => {
    const res = await apiClient.post('/finance/roi', data);
    return res.data;
  },
};
