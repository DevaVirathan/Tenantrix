import { useEffect, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { CheckCircle, XCircle, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { apiClient } from "@/lib/api-client"

interface AcceptInviteResponse {
  organization_id: string
  message: string
}

type Status = "loading" | "success" | "error"

export function AcceptInvitePage() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const [status, setStatus] = useState<Status>("loading")
  const [orgId, setOrgId] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string>("Invalid or expired invite link.")

  useEffect(() => {
    if (!token) {
      setStatus("error")
      setErrorMessage("No invite token found.")
      return
    }

    apiClient
      .post(`organizations/invites/accept/${token}`)
      .json<AcceptInviteResponse>()
      .then((data) => {
        setOrgId(data.organization_id)
        setStatus("success")
      })
      .catch(async (err: unknown) => {
        let msg = "Invalid or expired invite link."
        if (err && typeof err === "object" && "response" in err) {
          try {
            const body = await (err as { response: Response }).response.json() as { detail?: string }
            if (body.detail) msg = body.detail
          } catch {
            // ignore JSON parse errors
          }
        }
        setErrorMessage(msg)
        setStatus("error")
      })
  }, [token])

  if (status === "loading") {
    return (
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

  if (status === "success") {
    return (
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

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <XCircle className="h-5 w-5 text-destructive" />
          Invite failed
        </CardTitle>
        <CardDescription>{errorMessage}</CardDescription>
      </CardHeader>
      <CardContent>
        <Button variant="outline" className="w-full" onClick={() => navigate("/login")}>
          Back to login
        </Button>
      </CardContent>
    </Card>
  )
}
