import { Navigate, Outlet } from "react-router-dom"
import { useAppStore } from "@/store/app-store"

export function AuthLayout() {
  const { accessToken } = useAppStore()

  // Already logged in — redirect to orgs
  if (accessToken) {
    return <Navigate to="/orgs" replace />
  }

  return (
    <div className="min-h-svh bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Tenantrix
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Multi-tenant project management
          </p>
        </div>
        <Outlet />
      </div>
    </div>
  )
}
