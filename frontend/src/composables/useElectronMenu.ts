import { onMounted, onUnmounted } from 'vue'
import { ElNotification } from 'element-plus'
import { useProjectStore } from '@/stores/project'

export function useElectronMenu() {
  const projectStore = useProjectStore()

  const getFileName = (filePath: string): string => {
    const parts = filePath.replace(/\\/g, '/').split('/')
    return parts[parts.length - 1] || filePath
  }

  onMounted(() => {
    if (!window.electronAPI) return

    window.electronAPI.onMenuNewProject(async (filePath: string) => {
      try {
        await projectStore.createNewProject(filePath)
        ElNotification({
          title: 'Success',
          message: `New project "${getFileName(filePath)}" created successfully`,
          type: 'success',
          duration: 3000,
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error occurred'
        ElNotification({
          title: 'Error Creating Project',
          message: `Failed to create "${getFileName(filePath)}": ${message}`,
          type: 'error',
          duration: 5000,
        })
      }
    })

    window.electronAPI.onMenuOpenProject(async (filePath: string) => {
      try {
        await projectStore.openProject(filePath)
        ElNotification({
          title: 'Success',
          message: `Project "${getFileName(filePath)}" opened successfully`,
          type: 'success',
          duration: 3000,
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error occurred'
        ElNotification({
          title: 'Error Opening Project',
          message: `Failed to open "${getFileName(filePath)}": ${message}`,
          type: 'error',
          duration: 5000,
        })
      }
    })

    window.electronAPI.onMenuSaveProject(async () => {
      try {
        await projectStore.saveProject()
      } catch (err) {
        console.error('Failed to save project:', err)
      }
    })

    window.electronAPI.onMenuSaveProjectAs(async (filePath: string) => {
      try {
        await projectStore.saveProjectAs(filePath)
        ElNotification({
          title: 'Success',
          message: `Project saved as "${getFileName(filePath)}"`,
          type: 'success',
          duration: 3000,
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error occurred'
        ElNotification({
          title: 'Error Saving Project',
          message: `Failed to save "${getFileName(filePath)}": ${message}`,
          type: 'error',
          duration: 5000,
        })
      }
    })

    window.electronAPI.onMenuUndo(() => {
      projectStore.undo()
    })

    window.electronAPI.onMenuRedo(() => {
      projectStore.redo()
    })
  })

  onUnmounted(() => {
    if (window.electronAPI) {
      window.electronAPI.removeMenuListeners()
    }
  })
}
