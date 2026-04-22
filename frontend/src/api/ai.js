import apiClient from './client';

export const aiAPI = {
  generateChecklist: (country, profile = {}) =>
    apiClient.post('/ai/generate-checklist', { country, profile }).then(r => r.data),

  generateTimeline: (intake, countries = [], profile = {}, current_status = {}) =>
    apiClient.post('/ai/generate-timeline', { intake, countries, profile, current_status }).then(r => r.data),

  analyzeProfile: (profile) =>
    apiClient.post('/ai/analyze-profile', { profile }).then(r => r.data),

  chat: (message, profile = {}, history = []) =>
    apiClient.post('/ai/chat', { message, profile, history }).then(r => r.data),

  generateSop: (profile = {}, university = '', program = '') =>
    apiClient.post('/ai/generate-sop', { profile, university, program }).then(r => r.data),
};
