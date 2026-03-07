import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
import type { ReactNode } from "react"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 2, // 2 minutes default
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors
        if (error instanceof Error && "status" in error) {
          const status = (error as { status: number }).status
          if (status >= 400 && status < 500) return false
        }
        return failureCount < 2
      },
    },
  },
})

export function QueryProvider({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
