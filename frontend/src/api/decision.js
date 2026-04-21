import apiClient from './client';

export const decisionAPI = {
  /**
   * Run the full 5-agent Decision Dashboard pipeline.
   * Returns { top_universities, synthesis, agent_steps }.
   */
  getDecision: async () => {
    const response = await apiClient.get('/decision/');
    return response.data;
  },

  /**
   * Legacy single-university recommendation (backward-compatible).
   * Returns { best_option, explanation }.
   */
  getSimpleDecision: async () => {
    const response = await apiClient.get('/decision/simple');
    return response.data;
  },
};
