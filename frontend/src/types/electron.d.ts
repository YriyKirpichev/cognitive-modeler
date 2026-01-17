export interface ElectronAPI {
  onMenuNewProject: (callback: () => void) => void
  onMenuOpenProject: (callback: (filePath: string) => void) => void
  onMenuSaveProject: (callback: () => void) => void
  onMenuSaveProjectAs: (callback: (filePath: string) => void) => void
  onMenuUndo: (callback: () => void) => void
  onMenuRedo: (callback: () => void) => void
  removeMenuListeners: () => void
}

declare global {
  interface Window {
    electronAPI: ElectronAPI
  }
}