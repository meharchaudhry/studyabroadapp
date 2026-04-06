import apiClient from './client';

export const jobsAPI = {
  searchJobs: async (location, jobType, keywords) => {
    const params = new URLSearchParams({
      location,
      job_type: jobType,
      keywords
    });
    const response = await apiClient.get(`/jobs/search?${params.toString()}`);
    return response.data;
  },
  
  saveJob: async (jobId) => {
    const response = await apiClient.post('/jobs/saved', { job_id: jobId });
    return response.data;
  }
};
