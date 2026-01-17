const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  onMenuNewProject: (callback) => {
    ipcRenderer.on('menu-new-project', (_event, filePath) => callback(filePath))
  },
  onMenuOpenProject: (callback) => {
    ipcRenderer.on('menu-open-project', (_event, filePath) => callback(filePath))
  },
  onMenuSaveProject: (callback) => {
    ipcRenderer.on('menu-save-project', callback)
  },
  onMenuSaveProjectAs: (callback) => {
    ipcRenderer.on('menu-save-project-as', (_event, filePath) => callback(filePath))
  },
  onMenuUndo: (callback) => {
    ipcRenderer.on('menu-undo', callback)
  },
  onMenuRedo: (callback) => {
    ipcRenderer.on('menu-redo', callback)
  },

  removeMenuListeners: () => {
    ipcRenderer.removeAllListeners('menu-new-project')
    ipcRenderer.removeAllListeners('menu-open-project')
    ipcRenderer.removeAllListeners('menu-save-project')
    ipcRenderer.removeAllListeners('menu-save-project-as')
    ipcRenderer.removeAllListeners('menu-undo')
    ipcRenderer.removeAllListeners('menu-redo')
  }
})