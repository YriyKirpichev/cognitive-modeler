const isDev = process.env.NODE_ENV !== 'production'

const config = {
  backend: {
    host: process.env.BACKEND_HOST || 'localhost',
    port: parseInt(process.env.BACKEND_PORT || '8001', 10),
    get url() {
      return `http://${this.host}:${this.port}`
    }
  },

  frontend: {
    port: parseInt(process.env.FRONTEND_PORT || '5175', 10),
    get devUrl() {
      return `http://localhost:${this.port}`
    }
  },

  electron: {
    window: {
      width: parseInt(process.env.WINDOW_WIDTH || '1400', 10),
      height: parseInt(process.env.WINDOW_HEIGHT || '900', 10)
    }
  },

  isDev,
  enableDevTools: isDev || process.env.ENABLE_DEVTOOLS === 'true'
}

module.exports = config