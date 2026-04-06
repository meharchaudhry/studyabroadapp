import apiClient from './client';

export const decisionAPI = {
  getDecision: async () => {
    const response = await apiClient.get('/decision/');
    return response.data;
  }
};
