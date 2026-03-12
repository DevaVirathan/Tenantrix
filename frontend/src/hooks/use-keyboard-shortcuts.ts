import { useEffect } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { useAppStore } from "@/store/app-store"

/**
 * Global keyboard shortcuts:
 * - C: Open create task dialog (sets flag in store)
 * - Escape: Close task detail panel
 */
export function useKeyboardShortcuts() {
  const navigate = useNavigate()
  const { orgId, projectId } = useParams<{ orgId?: string; projectId?: string }>()
  const closeTaskPanel = useAppStore((s) => s.closeTaskPanel)
  const taskPanelOpen = useAppStore((s) => s.taskPanelOpen)
  const setCreateDialogOpen = useAppStore((s) => s.setCreateDialogOpen)

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement)?.tagName
      const isInput = ["INPUT", "TEXTAREA", "SELECT"].includes(tag)
      const isEditable = (e.target as HTMLElement)?.isContentEditable

      // Don't trigger shortcuts when typing in inputs
      if (isInput || isEditable) return
      // Don't trigger when modifier keys are held (except for Cmd+K which is handled by command palette)
      if (e.metaKey || e.ctrlKey || e.altKey) return

      switch (e.key) {
        case "c":
          if (projectId) {
            e.preventDefault()
            setCreateDialogOpen?.(true)
          }
          break
        case "Escape":
          if (taskPanelOpen) {
            e.preventDefault()
            closeTaskPanel()
          }
          break
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [navigate, orgId, projectId, taskPanelOpen, closeTaskPanel, setCreateDialogOpen])
}
