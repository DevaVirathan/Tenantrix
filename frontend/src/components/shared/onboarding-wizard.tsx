import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Building2, FolderKanban, Users, Rocket } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from "@/components/ui/dialog"
import { cn } from "@/lib/utils"

interface OnboardingWizardProps {
  open: boolean
  onClose: () => void
  onCreateOrg: (name: string, description: string) => Promise<string>
  onCreateProject: (orgId: string, name: string) => Promise<string>
  onInvite: (orgId: string, email: string) => Promise<void>
}

const STEPS = [
  { icon: Building2, title: "Create your workspace", desc: "Organizations are shared workspaces for your team." },
  { icon: FolderKanban, title: "Create your first project", desc: "Projects contain your tasks, boards, and sprints." },
  { icon: Users, title: "Invite your team", desc: "Add team members to collaborate. You can skip this for now." },
  { icon: Rocket, title: "You're all set!", desc: "Start managing your work with Tenantrix." },
]

export function OnboardingWizard({ open, onClose, onCreateOrg, onCreateProject, onInvite }: OnboardingWizardProps) {
  const navigate = useNavigate()
  const [step, setStep] = useState(0)
  const [orgName, setOrgName] = useState("")
  const [orgDesc, setOrgDesc] = useState("")
  const [projectName, setProjectName] = useState("")
  const [inviteEmail, setInviteEmail] = useState("")
  const [orgId, setOrgId] = useState("")
  const [projectId, setProjectId] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleOrgCreate() {
    if (!orgName.trim()) return
    setLoading(true)
    try {
      const id = await onCreateOrg(orgName.trim(), orgDesc.trim())
      setOrgId(id)
      setStep(1)
    } finally {
      setLoading(false)
    }
  }

  async function handleProjectCreate() {
    if (!projectName.trim()) return
    setLoading(true)
    try {
      const id = await onCreateProject(orgId, projectName.trim())
      setProjectId(id)
      setStep(2)
    } finally {
      setLoading(false)
    }
  }

  async function handleInvite() {
    if (!inviteEmail.trim()) return
    setLoading(true)
    try {
      await onInvite(orgId, inviteEmail.trim())
      setInviteEmail("")
    } finally {
      setLoading(false)
    }
  }

  function handleFinish() {
    onClose()
    if (projectId) {
      navigate(`/orgs/${orgId}/projects/${projectId}/board`)
    } else if (orgId) {
      navigate(`/orgs/${orgId}`)
    }
  }

  const CurrentIcon = STEPS[step].icon

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className="rounded-lg bg-primary/10 p-2.5">
              <CurrentIcon className="h-5 w-5 text-primary" />
            </div>
            <div>
              <DialogTitle>{STEPS[step].title}</DialogTitle>
              <DialogDescription>{STEPS[step].desc}</DialogDescription>
            </div>
          </div>
          {/* Progress dots */}
          <div className="flex items-center gap-1.5 pt-2">
            {STEPS.map((_, i) => (
              <div
                key={i}
                className={cn(
                  "h-1.5 rounded-full transition-all",
                  i === step ? "w-6 bg-primary" : i < step ? "w-1.5 bg-primary/60" : "w-1.5 bg-muted",
                )}
              />
            ))}
          </div>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {step === 0 && (
            <>
              <div className="space-y-2">
                <Label>Organization name</Label>
                <Input
                  placeholder="Acme Inc."
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleOrgCreate()}
                  autoFocus
                />
              </div>
              <div className="space-y-2">
                <Label>Description <span className="text-muted-foreground">(optional)</span></Label>
                <Input
                  placeholder="What does your team work on?"
                  value={orgDesc}
                  onChange={(e) => setOrgDesc(e.target.value)}
                />
              </div>
              <Button onClick={handleOrgCreate} disabled={!orgName.trim() || loading} className="w-full">
                {loading ? "Creating…" : "Create workspace"}
              </Button>
            </>
          )}

          {step === 1 && (
            <>
              <div className="space-y-2">
                <Label>Project name</Label>
                <Input
                  placeholder="My First Project"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleProjectCreate()}
                  autoFocus
                />
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setStep(2)} className="flex-1">
                  Skip
                </Button>
                <Button onClick={handleProjectCreate} disabled={!projectName.trim() || loading} className="flex-1">
                  {loading ? "Creating…" : "Create project"}
                </Button>
              </div>
            </>
          )}

          {step === 2 && (
            <>
              <div className="space-y-2">
                <Label>Email address</Label>
                <div className="flex gap-2">
                  <Input
                    type="email"
                    placeholder="teammate@example.com"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleInvite()}
                    autoFocus
                  />
                  <Button onClick={handleInvite} disabled={!inviteEmail.trim() || loading} size="sm">
                    {loading ? "…" : "Invite"}
                  </Button>
                </div>
              </div>
              <Button onClick={() => setStep(3)} className="w-full">
                Continue
              </Button>
            </>
          )}

          {step === 3 && (
            <Button onClick={handleFinish} className="w-full">
              <Rocket className="h-4 w-4 mr-2" />
              Get started
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
