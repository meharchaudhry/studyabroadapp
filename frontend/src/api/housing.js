import apiClient from './client';

export const housingAPI = {
  getListings: async ({ country = '', minPrice, maxPrice, studentFriendly, limit = 24, offset = 0 } = {}) => {
    const params = { limit, offset };
    if (country && country !== 'All') params.country = country;
    if (minPrice != null) params.min_price = minPrice;
    if (maxPrice != null) params.max_price = maxPrice;
    if (studentFriendly != null) params.student_friendly = studentFriendly;
    const response = await apiClient.get('/housing/listings', { params });
    return response.data;
  },
};
