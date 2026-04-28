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
  query: async (country, question, sessionId = 'default') => {
    const res = await apiClient.post('/visa/query', {
      query:      question,
      country,
      session_id: sessionId,
    });
    return res.data;
  },
  getSavedChecklist: async (country, checklistType = 'official') => {
    const res = await apiClient.get('/visa/saved-checklist', {
      params: { country, checklist_type: checklistType },
    });
    return res.data;
  },
  saveChecklist: async (payload) => {
    const res = await apiClient.put('/visa/saved-checklist', payload);
    return res.data;
  },
  clearMemory: async (sessionId) => {
    const res = await apiClient.delete(`/visa/session/${sessionId}`);
    return res.data;
  },
};
