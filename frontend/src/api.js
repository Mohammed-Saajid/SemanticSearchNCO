// Centralized API client for the frontend
// Vite exposes env variables prefixed with VITE_ via import.meta.env
// Ensure you have a .env file at the project root with VITE_BACKEND_URL defined.

import axios from 'axios';

const baseURL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL,
  timeout: 10000, // 10 seconds timeout for all requests
  headers: {
    'Content-Type': 'application/json',
  },
});

// Optional: Add request interceptor for logging or auth tokens in future
apiClient.interceptors.request.use((config) => {
  // Trim whitespace from string payloads (e.g., query)
  if (config.data && typeof config.data === 'object') {
    Object.keys(config.data).forEach((key) => {
      if (typeof config.data[key] === 'string') {
        config.data[key] = config.data[key].trim();
      }
    });
  }
  return config;
});

export default apiClient;

