import { useState } from "react"
import { Plus, Building2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { OrgCard } from "@/components/org/org-card"
import { CreateOrgDialog } from "@/components/org/create-org-dialog"
import { useOrgs } from "@/hooks/use-orgs"

export function OrgsPage() {
  const { data: orgs, isLoading } = useOrgs()
  const [dialogOpen, setDialogOpen] = useState(false)

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">Organizations</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Select an organization to get started.
          </p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New organization
        </Button>
      </div>

      {isLoading ? (
        <div className="grid gap-3">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-20 w-full" />)}
        </div>
      ) : orgs && orgs.length > 0 ? (
        <div className="grid gap-3">
          {orgs.map((org) => <OrgCard key={org.id} org={org} />)}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-20 gap-4 text-center">
          <Building2 className="h-10 w-10 text-muted-foreground" />
          <div>
            <p className="font-medium">No organizations yet</p>
            <p className="text-sm text-muted-foreground">Create one to get started.</p>
          </div>
          <Button onClick={() => setDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Create organization
          </Button>
        </div>
      )}

      <CreateOrgDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </div>
  )
}
