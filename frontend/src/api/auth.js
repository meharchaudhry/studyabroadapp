import apiClient from './client';

export const authAPI = {
  login: async (email, password) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    const res = await apiClient.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    return res.data;
  },
  register: async (userData) => {
    const res = await apiClient.post('/auth/register', userData);
    return res.data;
  },
  sendOTP: async (email) => {
    const res = await apiClient.post('/auth/send-otp', { email });
    return res.data;
  },
  verifyOTP: async (email, otp) => {
    const res = await apiClient.post('/auth/verify-otp', { email, otp });
    return res.data;
  },
  getProfile: async () => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },
};
