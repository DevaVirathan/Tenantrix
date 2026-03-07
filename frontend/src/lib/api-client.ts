import ky, { type KyInstance } from "ky"
import { useAppStore } from "@/store/app-store"
import type { TokenPair } from "@/types/auth"

// Use the Vite dev proxy (/api/* → localhost:8000) so no CORS preflight is needed.
// In production set VITE_API_BASE_URL to the actual API base (e.g. https://api.tenantrix.com).
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ""

// Flag to prevent concurrent refresh storms
let isRefreshing = false
let pendingQueue: Array<{
  resolve: (token: string) => void
  reject: (err: unknown) => void
}> = []

function processQueue(error: unknown, token: string | null) {
  pendingQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error)
    } else {
      resolve(token!)
    }
  })
  pendingQueue = []
}

async function refreshTokens(): Promise<boolean> {
  const { refreshToken, setTokens, logout } = useAppStore.getState()

  if (!refreshToken) {
    logout()
    return false
  }

  if (isRefreshing) {
    // Wait for the in-flight refresh
    return new Promise((resolve) => {
      pendingQueue.push({
        resolve: () => resolve(true),
        reject: () => resolve(false),
      })
    })
  }

  isRefreshing = true

  try {
    const data = await ky
      .post(`${BASE_URL}/api/v1/auth/refresh`, {
        json: { refresh_token: refreshToken },
      })
      .json<TokenPair>()

    setTokens(data.access_token, data.refresh_token)
    processQueue(null, data.access_token)
    return true
  } catch (err) {
    processQueue(err, null)
    logout()
    return false
  } finally {
    isRefreshing = false
  }
}

export const apiClient: KyInstance = ky.create({
  prefixUrl: `${BASE_URL}/api/v1`,
  hooks: {
    beforeRequest: [
      (request) => {
        const token = useAppStore.getState().accessToken
        if (token) {
          request.headers.set("Authorization", `Bearer ${token}`)
        }
      },
    ],
    afterResponse: [
      async (request, _options, response) => {
        if (response.status === 401) {
          const refreshed = await refreshTokens()
          if (refreshed) {
            // Retry with new token
            const token = useAppStore.getState().accessToken
            const newRequest = request.clone()
            if (token) newRequest.headers.set("Authorization", `Bearer ${token}`)
            return ky(newRequest)
          }
          // Redirect to login after failed refresh
          window.location.href = "/login"
        }
      },
    ],
  },
})
