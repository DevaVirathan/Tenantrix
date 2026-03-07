import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { ConfirmDialog } from "@/components/shared/confirm-dialog"
import { useOrg, useUpdateOrg, useDeleteOrg } from "@/hooks/use-orgs"
import { updateOrgSchema, type UpdateOrgValues } from "@/validations/org.schema"

export function OrgSettingsPage() {
  const { orgId } = useParams<{ orgId: string }>()
  const { data: org, isLoading } = useOrg(orgId!)
  const updateOrg = useUpdateOrg(orgId!)
  const deleteOrg = useDeleteOrg(orgId!)
  const [confirmDelete, setConfirmDelete] = useState(false)

  const form = useForm<UpdateOrgValues>({
    resolver: zodResolver(updateOrgSchema),
    defaultValues: { name: "", description: "" },
  })

  useEffect(() => {
    if (org) {
      form.reset({ name: org.name, description: org.description ?? "" })
    }
  }, [org, form])

  if (isLoading) {
    return (
      <div className="max-w-2xl space-y-6">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-semibold">Settings</h1>

      {/* General settings */}
      <Card>
        <CardHeader>
          <CardTitle>General</CardTitle>
          <CardDescription>Update your organization's name and description.</CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit((v) => updateOrg.mutate(v))} className="space-y-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Name</FormLabel>
                    <FormControl>
                      <Input {...field} value={field.value ?? ""} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description <span className="text-muted-foreground">(optional)</span></FormLabel>
                    <FormControl>
                      <Input {...field} value={field.value ?? ""} placeholder="What does this org do?" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="pt-1">
                <Button type="submit" disabled={updateOrg.isPending}>
                  {updateOrg.isPending ? "Saving…" : "Save changes"}
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>

      {/* Danger zone */}
      <Card className="border-destructive/40">
        <CardHeader>
          <CardTitle className="text-destructive">Danger zone</CardTitle>
          <CardDescription>Permanently delete this organization and all its data.</CardDescription>
        </CardHeader>
        <CardContent>
          <Separator className="mb-4" />
          <Button
            variant="destructive"
            onClick={() => setConfirmDelete(true)}
          >
            Delete organization
          </Button>
        </CardContent>
      </Card>

      <ConfirmDialog
        open={confirmDelete}
        onOpenChange={setConfirmDelete}
        title="Delete organization"
        description={`Delete "${org?.name}" permanently? This cannot be undone. All projects, tasks, and members will be removed.`}
        confirmLabel="Delete organization"
        isPending={deleteOrg.isPending}
        onConfirm={() => deleteOrg.mutate()}
      />
    </div>
  )
}
