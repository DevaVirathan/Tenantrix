import { Outlet } from "react-router-dom"
import { AuthGuard } from "@/components/shared/auth-guard"
import { TopBar } from "@/components/layout/top-bar"

export function DashboardLayout() {
  return (
    <AuthGuard>
      <div className="min-h-svh bg-background flex flex-col">
        <TopBar />
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </AuthGuard>
  )
}
