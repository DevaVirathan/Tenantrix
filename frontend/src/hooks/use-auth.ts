import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate, useSearchParams } from "react-router-dom"
import { apiClient } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import { useAppStore } from "@/store/app-store"
import type { User, TokenPair, MessageOut } from "@/types/auth"
import type { LoginFormValues, RegisterFormValues } from "@/validations/auth.schema"
import ky from "ky"

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"

// GET /auth/me
export function useCurrentUser() {
  const { accessToken } = useAppStore()

  return useQuery({
    queryKey: queryKeys.user(),
    queryFn: async () => {
      return await apiClient.get("auth/me").json<User>()
    },
    enabled: !!accessToken,
    staleTime: 1000 * 60 * 5,
    retry: false,
  })
}

// POST /auth/register
export function useRegister() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { setTokens, setUser } = useAppStore()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: RegisterFormValues) => {
      // Register returns UserOut (not tokens) — then auto-login
      await ky.post(`${BASE_URL}/api/v1/auth/register`, { json: data }).json<User>()
      // Auto-login after register
      const tokens = await ky
        .post(`${BASE_URL}/api/v1/auth/login`, {
          json: { email: data.email, password: data.password },
        })
        .json<TokenPair>()
      return tokens
    },
    onSuccess: async (tokens) => {
      setTokens(tokens.access_token, tokens.refresh_token)
      const user = await ky
        .get(`${BASE_URL}/api/v1/auth/me`, {
          headers: { Authorization: `Bearer ${tokens.access_token}` },
        })
        .json<User>()
      setUser(user)
      queryClient.setQueryData(queryKeys.user(), user)
      const redirect = searchParams.get("redirect")
      navigate(redirect || "/orgs")
    },
  })
}

// POST /auth/login
export function useLogin() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { setTokens, setUser } = useAppStore()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: LoginFormValues) => {
      return await ky
        .post(`${BASE_URL}/api/v1/auth/login`, { json: data })
        .json<TokenPair>()
    },
    onSuccess: async (tokens) => {
      setTokens(tokens.access_token, tokens.refresh_token)
      const user = await ky
        .get(`${BASE_URL}/api/v1/auth/me`, {
          headers: { Authorization: `Bearer ${tokens.access_token}` },
        })
        .json<User>()
      setUser(user)
      queryClient.setQueryData(queryKeys.user(), user)
      const redirect = searchParams.get("redirect")
      navigate(redirect || "/orgs")
    },
  })
}

// POST /auth/logout
export function useLogout() {
  const navigate = useNavigate()
  const { refreshToken, logout } = useAppStore()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      if (refreshToken) {
        await apiClient
          .post("auth/logout", { json: { refresh_token: refreshToken } })
          .json<MessageOut>()
      }
    },
    onSettled: () => {
      logout()
      queryClient.clear()
      navigate("/login")
    },
  })
}
