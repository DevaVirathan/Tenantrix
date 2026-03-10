import { Outlet, useParams } from "react-router-dom"
import { AuthGuard } from "@/components/shared/auth-guard"
import { TopBar } from "@/components/layout/top-bar"
import { Sidebar } from "@/components/layout/sidebar"
import { CommandPalette } from "@/components/layout/command-palette"

export function DashboardLayout() {
  const { orgId } = useParams<{ orgId?: string }>()

  return (
    <AuthGuard>
      <div className="min-h-svh bg-background flex flex-col">
        <TopBar />
        <div className="flex flex-1 overflow-hidden">
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
