import apiClient from './client';

export const jobsAPI = {
  searchJobs: async (location = 'London', jobType = 'all', keywords = '') => {
    const response = await apiClient.get('/jobs/search', {
      params: { location, job_type: jobType, keywords },
    });
    return response.data;
  },
  saveJob: async (jobId) => {
    const response = await apiClient.post('/jobs/saved', { job_id: jobId });
    return response.data;
  },
};
