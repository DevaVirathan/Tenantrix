import { useEffect, useState } from "react"
import { useParams, useNavigate, Link } from "react-router-dom"
import { CheckCircle, XCircle, Loader2, Mail } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { apiClient } from "@/lib/api-client"
import { useAppStore } from "@/store/app-store"

type Status = "checking" | "accepting" | "success" | "error" | "needs-auth"

export function AcceptInvitePage() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const accessToken = useAppStore((s) => s.accessToken)
  const [status, setStatus] = useState<Status>("checking")
  const [orgId, setOrgId] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState("Invalid or expired invite link.")

  const inviteUrl = `/invite/${token}`

  useEffect(() => {
    if (!token) {
      setErrorMessage("No invite token found.")
      setStatus("error")
      return
    }

    // If not logged in, prompt auth
    if (!accessToken) {
      setStatus("needs-auth")
      return
    }

    // Logged in — accept the invite
    setStatus("accepting")
    apiClient
      .post(`organizations/invites/accept/${token}`)
      .json<{ id: string }>()
      .then((data) => {
        setOrgId(data.id)
        setStatus("success")
      })
      .catch(async (err: unknown) => {
        let msg = "Invalid or expired invite link."
        if (err && typeof err === "object" && "response" in err) {
          try {
            const body = await (err as { response: Response }).response.json() as { detail?: string }
            if (body.detail) msg = body.detail
          } catch {
            // ignore
          }
        }
        setErrorMessage(msg)
        setStatus("error")
      })
  }, [token, accessToken])

  // Wrapper for centered layout (since this page is outside AuthLayout)
  const wrapper = (children: React.ReactNode) => (
    <div className="min-h-svh bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Tenantrix</h1>
          <p className="text-sm text-muted-foreground mt-1">Multi-tenant project management</p>
        </div>
        {children}
      </div>
    </div>
  )

  if (status === "checking" || status === "accepting") {
    return wrapper(
      <Card>
        <CardHeader>
          <CardTitle>Accepting invite…</CardTitle>
          <CardDescription>Please wait while we verify your invite.</CardDescription>
        </CardHeader>
        <CardContent className="flex justify-center py-6">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    )
  }

  if (status === "needs-auth") {
    return wrapper(
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5 text-primary" />
            You've been invited!
          </CardTitle>
          <CardDescription>
            Sign in or create an account to accept this invitation and join the organization.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button className="w-full" asChild>
            <Link to={`/login?redirect=${encodeURIComponent(inviteUrl)}`}>
              Sign in to accept
            </Link>
          </Button>
          <Button variant="outline" className="w-full" asChild>
            <Link to={`/register?redirect=${encodeURIComponent(inviteUrl)}`}>
              Create an account
            </Link>
          </Button>
          <p className="text-xs text-muted-foreground text-center pt-2">
            Make sure to use the same email address the invite was sent to.
          </p>
        </CardContent>
      </Card>
    )
  }

  if (status === "success") {
    return wrapper(
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            Invite accepted!
          </CardTitle>
          <CardDescription>You have successfully joined the organization.</CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            className="w-full"
            onClick={() => navigate(orgId ? `/orgs/${orgId}` : "/orgs")}
          >
            Go to dashboard
          </Button>
        </CardContent>
      </Card>
    )
  }

  // Error state
  return wrapper(
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <XCircle className="h-5 w-5 text-destructive" />
          Invite failed
        </CardTitle>
        <CardDescription>{errorMessage}</CardDescription>
      </CardHeader>
      <CardContent>
        <Button variant="outline" className="w-full" onClick={() => navigate("/orgs")}>
          Go to dashboard
        </Button>
      </CardContent>
    </Card>
  )
}
