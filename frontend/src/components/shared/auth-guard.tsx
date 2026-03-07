import { Navigate, useLocation } from "react-router-dom"
import { useAppStore } from "@/store/app-store"
import type { ReactNode } from "react"

export function AuthGuard({ children }: { children: ReactNode }) {
  const { accessToken } = useAppStore()
  const location = useLocation()

  if (!accessToken) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}
