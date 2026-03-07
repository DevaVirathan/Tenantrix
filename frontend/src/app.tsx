import { RouterProvider } from "react-router-dom"
import { ThemeProvider } from "@/providers/theme-provider"
import { QueryProvider } from "@/providers/query-provider"
import { Toaster } from "@/components/ui/sonner"
import { TooltipProvider } from "@/components/ui/tooltip"
import { router } from "@/router"

export function App() {
  return (
    <ThemeProvider>
      <QueryProvider>
        <TooltipProvider delayDuration={300}>
          <RouterProvider router={router} />
          <Toaster richColors closeButton position="top-right" />
        </TooltipProvider>
      </QueryProvider>
    </ThemeProvider>
  )
}
