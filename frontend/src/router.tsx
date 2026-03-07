import { createBrowserRouter, Navigate } from "react-router-dom"
import { AuthLayout } from "@/layouts/auth-layout"
import { DashboardLayout } from "@/layouts/dashboard-layout"
import { LoginPage } from "@/pages/auth/login"
import { RegisterPage } from "@/pages/auth/register"
import { AcceptInvitePage } from "@/pages/auth/accept-invite"
import { OrgsPage } from "@/pages/orgs/index"

function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4">
      <h1 className="text-4xl font-bold">404</h1>
      <p className="text-muted-foreground">Page not found.</p>
      <a href="/orgs" className="text-primary hover:underline">
        Go home
      </a>
    </div>
  )
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/orgs" replace />,
  },
  {
    element: <AuthLayout />,
    children: [
      { path: "/login", element: <LoginPage /> },
      { path: "/register", element: <RegisterPage /> },
      { path: "/invite/:token", element: <AcceptInvitePage /> },
    ],
  },
  {
    element: <DashboardLayout />,
    children: [
      { path: "/orgs", element: <OrgsPage /> },
    ],
  },
  {
    path: "*",
    element: <NotFoundPage />,
  },
])
