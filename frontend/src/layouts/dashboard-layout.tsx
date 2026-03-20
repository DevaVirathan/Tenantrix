import { Outlet, useParams } from "react-router-dom"
import { AuthGuard } from "@/components/shared/auth-guard"
import { TopBar } from "@/components/layout/top-bar"
import { Sidebar } from "@/components/layout/sidebar"
import { CommandPalette } from "@/components/layout/command-palette"
import { useKeyboardShortcuts } from "@/hooks/use-keyboard-shortcuts"
import { useWebSocket } from "@/hooks/use-websocket"

export function DashboardLayout() {
  const { orgId } = useParams<{ orgId?: string }>()
  useKeyboardShortcuts()
  useWebSocket(orgId)

  return (
    <AuthGuard>
      <div className="min-h-svh bg-background flex flex-col relative">
        {/* Subtle ambient glow for dark mode */}
        <div className="pointer-events-none fixed inset-0 overflow-hidden dark:block hidden z-0">
          <div className="absolute top-0 left-1/4 h-[40%] w-[40%] rounded-full bg-primary/3 blur-[150px]" />
          <div className="absolute bottom-0 right-1/4 h-[30%] w-[30%] rounded-full bg-neon-purple/3 blur-[150px]" />
        </div>

        <TopBar />
        <div className="flex flex-1 overflow-hidden relative z-10">
          {orgId && <Sidebar />}
          <main className="flex-1 overflow-y-auto p-6">
            <Outlet />
          </main>
        </div>
        <CommandPalette />
      </div>
    </AuthGuard>
  )
}
