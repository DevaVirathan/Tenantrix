import { Navigate, Outlet, useSearchParams } from "react-router-dom"
import { useAppStore } from "@/store/app-store"

export function AuthLayout() {
  const { accessToken } = useAppStore()
  const [searchParams] = useSearchParams()

  // Already logged in — honor redirect param or go to orgs
  if (accessToken) {
    const redirect = searchParams.get("redirect")
    return <Navigate to={redirect || "/orgs"} replace />
  }

  return (
    <div className="min-h-svh bg-background flex items-center justify-center p-4 relative overflow-hidden">
      {/* Subtle background glow */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden dark:block hidden">
        <div className="absolute -top-[30%] -left-[15%] h-[60%] w-[50%] rounded-full bg-primary/5 blur-[120px]" />
        <div className="absolute -bottom-[20%] -right-[10%] h-[50%] w-[40%] rounded-full bg-neon-purple/5 blur-[120px]" />
      </div>

      <div className="w-full max-w-md relative z-10">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold tracking-tight text-primary">
            Tenantrix
          </h1>
          <p className="text-sm text-muted-foreground mt-1.5">
            Multi-tenant project management
          </p>
        </div>
        <Outlet />
      </div>
    </div>
  )
}
