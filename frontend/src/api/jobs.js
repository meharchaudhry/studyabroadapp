import apiClient from './client';

export const jobsAPI = {
  searchJobs: async (location = 'London', jobType = 'all', keywords = '', source = '', page = 1, limit = 12) => {
    const response = await apiClient.get('/jobs/search', {
      params: { location, job_type: jobType, keywords, source: source || undefined, page, limit },
    });
    return response.data;
  },
  getFilters: async () => {
    const response = await apiClient.get('/jobs/filters');
    return response.data;
  },
  saveJob: async (jobId) => {
    const response = await apiClient.post('/jobs/saved', { job_id: jobId });
    return response.data;
  },
};
