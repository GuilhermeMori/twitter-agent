import axios from 'axios'

/**
 * Axios instance pre-configured for the FastAPI backend.
 * During development, Vite proxies /api → http://localhost:8000.
 * In production, set VITE_API_BASE_URL to the deployed backend URL.
 */
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30_000, // 30 seconds
})

// Response interceptor — normalise error shape
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.message ??
      error.response?.data?.detail ??
      error.message ??
      'An unexpected error occurred'
    return Promise.reject(new Error(message))
  },
)

export default api
