import { useState } from "react"
import { useParams } from "react-router-dom"
import { Trash2 } from "lucide-react"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { RoleBadge } from "@/components/shared/role-badge"
import { ConfirmDialog } from "@/components/shared/confirm-dialog"
import { useMembers, useUpdateMemberRole, useRemoveMember } from "@/hooks/use-members"
import { useAppStore } from "@/store/app-store"
import { hasRole } from "@/lib/rbac"
import { getInitials } from "@/lib/utils"
import type { Member, OrgRole } from "@/types/org"

export function MembersPage() {
  const { orgId = "" } = useParams<{ orgId: string }>()
  const { data: members, isLoading } = useMembers(orgId!)
  const updateRole = useUpdateMemberRole(orgId!)
  const removeMember = useRemoveMember(orgId!)
  const { user, activeMembership } = useAppStore()
  const myRole = activeMembership?.role ?? null
  const canManage = hasRole(myRole, "admin")

  const [confirmRemove, setConfirmRemove] = useState<Member | null>(null)

  if (isLoading) {
    return (
      <div className="space-y-4 max-w-4xl">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  return (
    <div className="max-w-4xl space-y-4">
      <h1 className="text-2xl font-semibold">Members</h1>

      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Member</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Joined</TableHead>
              {canManage && <TableHead className="w-16" />}
            </TableRow>
          </TableHeader>
          <TableBody>
            {members?.map((member) => {
              const isMe = member.user_id === user?.id
              const isOwner = member.role === "owner"
              return (
                <TableRow key={member.user_id}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                        {getInitials(member.full_name ?? null, member.email ?? "")}
                      </div>
                      <div>
                        <p className="text-sm font-medium">
                          {member.full_name ?? member.email ?? member.user_id.slice(0, 8)}
                          {isMe && <span className="ml-2 text-xs text-muted-foreground">(you)</span>}
                        </p>
                        {member.email && (
                          <p className="text-xs text-muted-foreground">{member.email}</p>
                        )}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    {canManage && !isOwner && !isMe ? (
                      <Select
                        value={member.role}
                        onValueChange={(role) =>
                          updateRole.mutate({ userId: member.user_id, role: role as OrgRole })
                        }
                      >
                        <SelectTrigger className="w-28 h-7 text-xs">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="admin">Admin</SelectItem>
                          <SelectItem value="member">Member</SelectItem>
                          <SelectItem value="viewer">Viewer</SelectItem>
                        </SelectContent>
                      </Select>
                    ) : (
                      <RoleBadge role={member.role} />
                    )}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {new Date(member.joined_at).toLocaleDateString()}
                  </TableCell>
                  {canManage && (
                    <TableCell>
                      {!isOwner && !isMe && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-destructive"
                          onClick={() => setConfirmRemove(member)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </TableCell>
                  )}
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>

      <ConfirmDialog
        open={!!confirmRemove}
        onOpenChange={(open) => !open && setConfirmRemove(null)}
        title="Remove member"
        description={`Remove this member from the organization? They will lose all access.`}
        confirmLabel="Remove"
        isPending={removeMember.isPending}
        onConfirm={() => {
          if (confirmRemove) {
            removeMember.mutate(confirmRemove.user_id, {
              onSuccess: () => setConfirmRemove(null),
            })
          }
        }}
      />
    </div>
  )
}
