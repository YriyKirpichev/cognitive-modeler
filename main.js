const { app, BrowserWindow, Menu, dialog } = require('electron')
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

const userDataDir = app.getPath('userData')
const sessionFilePath = path.join(userDataDir, 'session.json')

const sleep = promisify(setTimeout)

let pythonProcess = null
let mainWindow = null

const isDev = !app.isPackaged

function ensureSessionFile() {
  try {
    if (!fs.existsSync(userDataDir)) {
      fs.mkdirSync(userDataDir, { recursive: true })
    }
    
    if (!fs.existsSync(sessionFilePath)) {
      const defaultConfig = {
        settings: {},
        lastOpened: null
      }
      fs.writeFileSync(sessionFilePath, JSON.stringify(defaultConfig, null, 2), 'utf-8')
      console.log(`Created config file at: ${sessionFilePath}`)
    } else {
      console.log(`Config file exists at: ${sessionFilePath}`)
    }
    
    return sessionFilePath
  } catch (error) {
    console.error('Error ensuring config file:', error)
    throw error
  }
}

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

  const actualSessionPath = ensureSessionFile()

  if (isDev) {
    console.log('Starting backend in development mode...')
    const backendDir = path.join(__dirname, 'backend')
    
    pythonProcess = spawn('uv', ['run', 'uvicorn', 'app.main:app', '--port', config.backend.port.toString(), '--reload'], {
      cwd: backendDir,
      shell: true,
      stdio: ['ignore', 'pipe', 'pipe'],
      env: {
        ...process.env,
        BACKEND_PORT: config.backend.port.toString(),
        BACKEND_HOST: config.backend.host,
        SESSION_FILE_PATH: actualSessionPath
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
        BACKEND_HOST: config.backend.host,
        SESSION_FILE_PATH: actualSessionPath
      }
    })
  }

  pythonProcess.stdout.on('data', (data) => {
    console.log(`[Backend] ${data.toString().trim()}`)
  })

  pythonProcess.stderr.on('data', (data) => {
    console.error(`[Backend Log] ${data.toString().trim()}`)
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
      preload: path.join(__dirname, 'electron/preload.js'),
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
  createMenu()
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

function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'New Project',
          accelerator: 'CmdOrCtrl+N',
          click: async () => {
            mainWindow.webContents.send('menu-new-project')
          }
        },
        {
          label: 'Open Project...',
          accelerator: 'CmdOrCtrl+O',
          click: async () => {
            const result = await dialog.showOpenDialog(mainWindow, {
              title: 'Open Cognitive Map Project',
              filters: [
                { name: 'JSON Files', extensions: ['json'] },
                { name: 'All Files', extensions: ['*'] }
              ],
              properties: ['openFile']
            })

            if (!result.canceled && result.filePaths.length > 0) {
              const filePath = result.filePaths[0]
              mainWindow.webContents.send('menu-open-project', filePath)
            }
          }
        },
        {
          label: 'Save',
          accelerator: 'CmdOrCtrl+S',
          click: async () => {
            mainWindow.webContents.send('menu-save-project')
          }
        },
        {
          label: 'Save As...',
          accelerator: 'CmdOrCtrl+Shift+S',
          click: async () => {
            const result = await dialog.showSaveDialog(mainWindow, {
              title: 'Save Cognitive Map Project',
              defaultPath: 'cognitive_map.json',
              filters: [
                { name: 'JSON Files', extensions: ['json'] },
                { name: 'All Files', extensions: ['*'] }
              ]
            })

            if (!result.canceled && result.filePath) {
              mainWindow.webContents.send('menu-save-project-as', result.filePath)
            }
          }
        },
        { type: 'separator' },
        {
          label: 'Export...',
          submenu: []
        },
        { type: 'separator' },
        {
          label: 'Exit',
          accelerator: 'CmdOrCtrl+Q',
          click: () => {
            app.quit()
          }
        }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        {
          label: 'Undo',
          accelerator: 'CmdOrCtrl+Z',
          click: () => {
            mainWindow.webContents.send('menu-undo')
          }
        },
        {
          label: 'Redo',
          accelerator: 'CmdOrCtrl+Shift+Z',
          click: () => {
            mainWindow.webContents.send('menu-redo')
          }
        },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectAll' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About Cognitive Maps',
              message: 'Cognitive Maps Editor',
              detail: 'Version 1.0.0\n\nA tool for creating and editing cognitive maps.'
            })
          }
        }
      ]
    }
  ]

  const menu = Menu.buildFromTemplate(template)
  Menu.setApplicationMenu(menu)
}