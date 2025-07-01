/**
 * HTTP Client Factory
 * Creates configurable axios instances with proper dependency injection
 */

import axios from 'axios';
import { getApiBaseURL } from '../utils/environment';

export const createHttpClient = (config = {}) => {
  const defaultConfig = {
    baseURL: getApiBaseURL(),
    headers: {
      'Content-Type': 'application/json',
    },
    timeout: 30000,
    ...config
  };

  const client = axios.create(defaultConfig);

  // Add request interceptor
  client.interceptors.request.use(
    (config) => {
      // Add any auth tokens or common headers here
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Add response interceptor
  client.interceptors.response.use(
    (response) => {
      return response;
    },
    (error) => {
      // Enhanced error handling
      if (error.response) {
        const { status, data } = error.response;
        console.error(`API Error [${status}]:`, data);
        
        // Create a more descriptive error
        const enhancedError = new Error(
          data?.message || data?.detail || `HTTP ${status} Error`
        );
        enhancedError.status = status;
        enhancedError.response = error.response;
        enhancedError.originalError = error;
        
        return Promise.reject(enhancedError);
      } else if (error.request) {
        console.error('No response received:', error.request);
        const networkError = new Error('Network error - no response from server');
        networkError.originalError = error;
        return Promise.reject(networkError);
      } else {
        console.error('Request setup error:', error.message);
        return Promise.reject(error);
      }
    }
  );

  return client;
};

// Default client instance
export const defaultHttpClient = createHttpClient();

// Export axios for direct use if needed (for mocking)
export { axios };