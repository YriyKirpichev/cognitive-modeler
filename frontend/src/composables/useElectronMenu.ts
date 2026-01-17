import { onMounted, onUnmounted } from 'vue'
import { useProjectStore } from '@/stores/project'

export function useElectronMenu() {
  const projectStore = useProjectStore()

  onMounted(() => {
    if (!window.electronAPI) return

    window.electronAPI.onMenuNewProject(() => {
      projectStore.createNewProject()
    })

    window.electronAPI.onMenuOpenProject(async (filePath: string) => {
      await projectStore.openProject(filePath)
    })

    window.electronAPI.onMenuSaveProject(async () => {
      await projectStore.saveProject()
    })

    window.electronAPI.onMenuSaveProjectAs(async (filePath: string) => {
      await projectStore.saveProjectAs(filePath)
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
