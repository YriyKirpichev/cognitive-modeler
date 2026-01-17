import axios from 'axios'

const baseUrl = import.meta.env.BACKEND_BASE_URL || 'http://localhost:8001/api'

const apiClient = axios.create({
  baseURL: baseUrl + '/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default apiClient