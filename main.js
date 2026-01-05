const { app, BrowserWindow } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const { promisify } = require('util')
const net = require('net')
const url = require('url')

const fs = require('fs')
const envPath = path.join(__dirname, '.env')
if (fs.existsSync(envPath)) {
  require('dotenv').config({ path: envPath })
}

const config = require('./config')

const sleep = promisify(setTimeout)

let pythonProcess = null
let mainWindow = null

const isDev = !app.isPackaged

async function isPortAvailable(port) {
  return new Promise((resolve) => {
    const server = net.createServer()
    server.once('error', () => resolve(false))
    server.once('listening', () => {
      server.close()
      resolve(true)
    })
    server.listen(port)
  })
}

async function waitForBackend(maxAttempts = 30) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const response = await fetch(config.backend.url)
      if (response.ok) {
        console.log('Backend is ready!')
        return true
      }
    } catch (error) {
      console.log(`Waiting for backend... Attempt ${i + 1}/${maxAttempts}`)
      await sleep(1000)
    }
  }
  throw new Error('Backend failed to start within timeout')
}

async function startBackend() {
  const portAvailable = await isPortAvailable(config.backend.port)
  if (!portAvailable) {
    console.warn(`Port ${config.backend.port} is already in use. Assuming backend is running externally.`)
    return
  }

  if (isDev) {
    console.log('Starting backend in development mode...')
    const backendDir = path.join(__dirname, 'backend')
    
    pythonProcess = spawn('uv', ['run', 'fastapi', 'dev', 'app/main.py', '--port', config.backend.port.toString()], {
      cwd: backendDir,
      shell: true,
      stdio: ['ignore', 'pipe', 'pipe'],
      env: {
        ...process.env,
        BACKEND_PORT: config.backend.port.toString(),
        BACKEND_HOST: config.backend.host
      }
    })
  } else {
    console.log('Starting backend in production mode...')
    const platform = process.platform
    const exeName = platform === 'win32' ? 'cognitive-modeler-backend.exe' : 'cognitive-modeler-backend'
    const backendPath = path.join(process.resourcesPath, 'backend', exeName)
    
    console.log(`Backend executable path: ${backendPath}`)
    
    pythonProcess = spawn(backendPath, [], {
      stdio: ['ignore', 'pipe', 'pipe'],
      env: {
        ...process.env,
        BACKEND_PORT: config.backend.port.toString(),
        BACKEND_HOST: config.backend.host
      }
    })
  }

  pythonProcess.stdout.on('data', (data) => {
    console.log(`[Backend] ${data.toString().trim()}`)
  })

  pythonProcess.stderr.on('data', (data) => {
    console.error(`[Backend Error] ${data.toString().trim()}`)
  })

  pythonProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`)
  })

  pythonProcess.on('error', (error) => {
    console.error('Failed to start backend:', error)
  })
}

async function createWindow() {
  try {
    await startBackend()
    await waitForBackend()
  } catch (error) {
    console.error('Failed to start backend:', error)
    app.quit()
    return
  }

  mainWindow = new BrowserWindow({
    width: config.electron.window.width,
    height: config.electron.window.height,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
    icon: path.join(__dirname, 'resources', 'assets', 'icon.png')
  })

  if (isDev) {
    mainWindow.loadURL(config.frontend.devUrl)
    if (config.enableDevTools) {
      mainWindow.webContents.openDevTools()
    }
  } else {
    const indexPath = path.join(__dirname, 'frontend', 'dist', 'index.html')
    console.log(`Loading frontend from: ${indexPath}`)
    
    mainWindow.loadURL(
      url.format({
        pathname: indexPath,
        protocol: 'file:',
        slashes: true
      })
    )

    if (config.enableDevTools) {
      mainWindow.webContents.openDevTools()
    }
  }

  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
    console.error('Failed to load:', validatedURL, errorDescription)
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

app.whenReady().then(() => {
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (pythonProcess && !pythonProcess.killed) {
    console.log('Killing backend process...')
    pythonProcess.kill('SIGTERM')

    setTimeout(() => {
      if (pythonProcess && !pythonProcess.killed) {
        pythonProcess.kill('SIGKILL')
      }
    }, 2000)
  }
  
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  if (pythonProcess && !pythonProcess.killed) {
    pythonProcess.kill('SIGTERM')
  }
})