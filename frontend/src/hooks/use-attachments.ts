import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { apiClient } from "@/lib/api-client"
import type { Attachment } from "@/types/attachment"

export function useAttachments(orgId: string, taskId: string) {
  return useQuery({
    queryKey: ["org", orgId, "task", taskId, "attachments"],
    queryFn: () =>
      apiClient
        .get(`organizations/${orgId}/tasks/${taskId}/attachments`)
        .json<Attachment[]>(),
    enabled: !!orgId && !!taskId,
  })
}

export function useUploadAttachment(orgId: string, taskId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData()
      formData.append("file", file)
      return apiClient
        .post(`organizations/${orgId}/tasks/${taskId}/attachments`, { body: formData })
        .json<Attachment>()
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["org", orgId, "task", taskId, "attachments"] })
      toast.success("File uploaded")
    },
    onError: () => {
      toast.error("Failed to upload file")
    },
  })
}

export function useDeleteAttachment(orgId: string, taskId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (attachmentId: string) =>
      apiClient.delete(`organizations/${orgId}/attachments/${attachmentId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["org", orgId, "task", taskId, "attachments"] })
      toast.success("Attachment deleted")
    },
    onError: () => {
      toast.error("Failed to delete attachment")
    },
  })
}

export function useDownloadAttachment(orgId: string) {
  return (attachmentId: string) => {
    window.open(`/api/v1/organizations/${orgId}/attachments/${attachmentId}/download`, "_blank")
  }
}
