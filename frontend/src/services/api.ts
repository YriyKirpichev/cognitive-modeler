import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.BACKEND_BASE_URL || 'http://localhost:8001/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export default apiClient
