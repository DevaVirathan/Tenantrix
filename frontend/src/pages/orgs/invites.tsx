import { useState } from "react"
import { useParams } from "react-router-dom"
import { Plus, Clock } from "lucide-react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { RoleBadge } from "@/components/shared/role-badge"
import { useInvites, useCreateInvite } from "@/hooks/use-invites"
import { useAppStore } from "@/store/app-store"
import { hasRole } from "@/lib/rbac"
import { createInviteSchema, type CreateInviteValues } from "@/validations/org.schema"

export function InvitesPage() {
  const { orgId } = useParams<{ orgId: string }>()
  const { data: invites, isLoading } = useInvites(orgId!)
  const createInvite = useCreateInvite(orgId!)
  const activeMembership = useAppStore((s) => s.activeMembership)
  const canInvite = hasRole(activeMembership?.role, "admin")
  const [dialogOpen, setDialogOpen] = useState(false)

  const form = useForm<CreateInviteValues>({
    resolver: zodResolver(createInviteSchema),
    defaultValues: { email: "", role: "member" as const },
  })

  async function onSubmit(values: CreateInviteValues) {
    await createInvite.mutateAsync(values)
    form.reset()
    setDialogOpen(false)
  }

  const now = new Date()

  if (isLoading) {
    return (
      <div className="space-y-4 max-w-3xl">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-40 w-full" />
      </div>
    )
  }

  return (
    <div className="max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Invites</h1>
        {canInvite && (
          <Button onClick={() => setDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Invite member
          </Button>
        )}
      </div>

      {invites && invites.length > 0 ? (
        <div className="rounded-lg border divide-y">
          {invites.map((invite) => {
            const expired = new Date(invite.expires_at) < now
            return (
              <div key={invite.id} className="flex items-center justify-between px-4 py-3">
                <div className="flex items-center gap-3">
                  <Clock className="h-4 w-4 text-muted-foreground shrink-0" />
                  <div>
                    <p className="text-sm font-medium">{invite.email}</p>
                    <p className="text-xs text-muted-foreground">
                      Expires {new Date(invite.expires_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <RoleBadge role={invite.role} />
                  {expired ? (
                    <Badge variant="outline" className="text-xs text-destructive border-destructive/30">
                      Expired
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-xs text-yellow-500 border-yellow-500/30">
                      Pending
                    </Badge>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-16 gap-3 text-center">
          <Clock className="h-8 w-8 text-muted-foreground" />
          <div>
            <p className="font-medium">No pending invites</p>
            <p className="text-sm text-muted-foreground">Invite people to join your organization.</p>
          </div>
        </div>
      )}

      {/* Invite dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Invite member</DialogTitle>
            <DialogDescription>Send an invite link to a new team member.</DialogDescription>
          </DialogHeader>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input type="email" placeholder="colleague@example.com" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="role"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Role</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="admin">Admin</SelectItem>
                        <SelectItem value="member">Member</SelectItem>
                        <SelectItem value="viewer">Viewer</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createInvite.isPending}>
                  {createInvite.isPending ? "Sending…" : "Send invite"}
                </Button>
              </div>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
