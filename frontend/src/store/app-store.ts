import { create } from "zustand"
import { persist } from "zustand/middleware"
import type { User } from "@/types/auth"

interface AppState {
  // Auth
  user: User | null
  accessToken: string | null
  refreshToken: string | null

  // Actions
  setTokens: (accessToken: string, refreshToken: string) => void
  setUser: (user: User) => void
  logout: () => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,

      setTokens: (accessToken, refreshToken) =>
        set({ accessToken, refreshToken }),

      setUser: (user) => set({ user }),

      logout: () =>
        set({ user: null, accessToken: null, refreshToken: null }),
    }),
    {
      name: "tenantrix-auth",
      // Only persist tokens in sessionStorage (clears on tab close)
      storage: {
        getItem: (key) => {
          const val = sessionStorage.getItem(key)
          return val ? JSON.parse(val) : null
        },
        setItem: (key, value) => sessionStorage.setItem(key, JSON.stringify(value)),
        removeItem: (key) => sessionStorage.removeItem(key),
      },
    }
  )
)
