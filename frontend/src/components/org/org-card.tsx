import { Building2, ChevronRight } from "lucide-react"
import { useNavigate } from "react-router-dom"
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import type { Organization } from "@/types/org"

interface OrgCardProps {
  org: Organization
}

export function OrgCard({ org }: OrgCardProps) {
  const navigate = useNavigate()

  return (
    <Card
      className="cursor-pointer transition-colors hover:bg-accent/30"
      onClick={() => navigate(`/orgs/${org.id}`)}
    >
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <Building2 className="h-5 w-5 text-primary" />
          </div>
          <div>
            <CardTitle className="text-base">{org.name}</CardTitle>
            <CardDescription className="text-xs font-mono">/{org.slug}</CardDescription>
          </div>
        </div>
        <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0">
          <ChevronRight className="h-4 w-4" />
        </Button>
      </CardHeader>
      {org.description && (
        <div className="px-6 pb-4 text-sm text-muted-foreground line-clamp-2">
          {org.description}
        </div>
      )}
    </Card>
  )
}
