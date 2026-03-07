import { ChevronsUpDown, Plus, Building2 } from "lucide-react"
import { useNavigate } from "react-router-dom"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useOrgs } from "@/hooks/use-orgs"
import { useAppStore } from "@/store/app-store"
import { useMembers } from "@/hooks/use-members"
import type { Organization, OrgRole } from "@/types/org"
import { cn } from "@/lib/utils"
import { useQueryClient } from "@tanstack/react-query"

export function OrgSwitcher() {
  const { data: orgs, isLoading } = useOrgs()
  const { activeOrg, setActiveOrg } = useAppStore()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { data: members } = useMembers(activeOrg?.id ?? "")
  const user = useAppStore((s) => s.user)

  function switchOrg(org: Organization) {
    if (org.id === activeOrg?.id) return
    // Derive the user's role in this org from cached members data
    const cached = qc.getQueryData<{ user_id: string; role: OrgRole }[]>(
      ["org", org.id, "members"]
    )
    const myMembership = cached?.find((m) => m.user_id === user?.id)
    setActiveOrg(org, myMembership?.role ?? "member")
    // Invalidate all org-scoped queries
    qc.invalidateQueries({ queryKey: ["org", org.id] })
    navigate(`/orgs/${org.id}`)
  }

  // Set first org as active if none selected
  if (!activeOrg && orgs && orgs.length > 0) {
    const myMembership = members?.find((m) => m.user_id === user?.id)
    setActiveOrg(orgs[0], myMembership?.role ?? "member")
  }

  if (isLoading) return <Skeleton className="h-9 w-full" />

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="w-full justify-between px-3 font-medium"
        >
          <span className="flex items-center gap-2 truncate">
            <Building2 className="h-4 w-4 shrink-0 text-muted-foreground" />
            <span className="truncate">{activeOrg?.name ?? "Select org"}</span>
          </span>
          <ChevronsUpDown className="h-4 w-4 shrink-0 text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="start">
        <DropdownMenuLabel>Organizations</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {orgs?.map((org) => (
          <DropdownMenuItem
            key={org.id}
            onClick={() => switchOrg(org)}
            className={cn(org.id === activeOrg?.id && "bg-accent")}
          >
            <Building2 className="mr-2 h-4 w-4 text-muted-foreground" />
            <span className="truncate">{org.name}</span>
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => navigate("/orgs/new")}>
          <Plus className="mr-2 h-4 w-4" />
          Create organization
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
