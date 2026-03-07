import { create } from "zustand"
import { persist } from "zustand/middleware"
import type { User } from "@/types/auth"
import type { Organization, OrgRole } from "@/types/org"

interface AppState {
  // Auth
  user: User | null
  accessToken: string | null
  refreshToken: string | null

  // Active org
  activeOrg: Organization | null
  activeMembership: { role: OrgRole } | null
  sidebarOpen: boolean

  // Actions
  setTokens: (accessToken: string, refreshToken: string) => void
  setUser: (user: User) => void
  setActiveOrg: (org: Organization, role: OrgRole) => void
  setSidebarOpen: (open: boolean) => void
  logout: () => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      activeOrg: null,
      activeMembership: null,
      sidebarOpen: true,

      setTokens: (accessToken, refreshToken) =>
        set({ accessToken, refreshToken }),

      setUser: (user) => set({ user }),

      setActiveOrg: (org, role) =>
        set({ activeOrg: org, activeMembership: { role } }),

      setSidebarOpen: (open) => set({ sidebarOpen: open }),

      logout: () =>
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          activeOrg: null,
          activeMembership: null,
        }),
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
