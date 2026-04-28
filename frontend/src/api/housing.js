import apiClient from './client';

export const housingAPI = {
  getListings: async (params = {}) => {
    const query = {};
    if (params.country && params.country !== 'All') query.country = params.country;
    if (params.city)                  query.city             = params.city;
    if (params.max_budget_inr != null) query.max_budget_inr  = params.max_budget_inr;
    if (params.student_friendly != null) query.student_friendly = params.student_friendly;
    // legacy aliases
    if (params.maxPrice != null)      query.max_budget_inr   = params.maxPrice;
    const response = await apiClient.get('/housing/listings', { params: query });
    return response.data;
  },
};
