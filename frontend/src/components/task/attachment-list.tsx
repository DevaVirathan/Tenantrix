import { useCallback, useRef, useState } from "react"
import { Paperclip, Upload, Trash2, Download, FileText, Image, File } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useAttachments, useUploadAttachment, useDeleteAttachment, useDownloadAttachment } from "@/hooks/use-attachments"
import { cn } from "@/lib/utils"

interface AttachmentListProps {
  orgId: string
  taskId: string
  canEdit: boolean
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function FileIcon({ mime }: { mime: string }) {
  if (mime.startsWith("image/")) return <Image className="h-4 w-4 text-blue-500" />
  if (mime.includes("pdf")) return <FileText className="h-4 w-4 text-red-500" />
  return <File className="h-4 w-4 text-muted-foreground" />
}

export function AttachmentList({ orgId, taskId, canEdit }: AttachmentListProps) {
  const { data: attachments = [] } = useAttachments(orgId, taskId)
  const upload = useUploadAttachment(orgId, taskId)
  const deleteAttachment = useDeleteAttachment(orgId, taskId)
  const download = useDownloadAttachment(orgId)
  const fileRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)

  const handleFiles = useCallback((files: FileList | null) => {
    if (!files) return
    Array.from(files).forEach((file) => upload.mutate(file))
  }, [upload])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    handleFiles(e.dataTransfer.files)
  }, [handleFiles])

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <Paperclip className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-semibold">Attachments</span>
        <span className="text-xs text-muted-foreground">({attachments.length})</span>
      </div>

      {/* Drop zone */}
      {canEdit && (
        <div
          className={cn(
            "rounded-md border-2 border-dashed px-4 py-3 text-center text-xs text-muted-foreground transition-colors cursor-pointer",
            dragOver ? "border-primary bg-primary/5" : "border-border hover:border-primary/50",
          )}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileRef.current?.click()}
        >
          <Upload className="h-4 w-4 mx-auto mb-1" />
          Drop files here or click to upload
          <input
            ref={fileRef}
            type="file"
            multiple
            className="hidden"
            onChange={(e) => handleFiles(e.target.files)}
          />
        </div>
      )}

      {/* File list */}
      {attachments.length > 0 && (
        <div className="flex flex-col gap-1">
          {attachments.map((att) => (
            <div
              key={att.id}
              className="flex items-center gap-2 rounded-md px-2 py-1.5 text-xs hover:bg-accent/50 transition-colors group"
            >
              <FileIcon mime={att.mime_type} />
              <span className="flex-1 truncate">{att.filename}</span>
              <span className="text-muted-foreground shrink-0">{formatSize(att.file_size)}</span>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={() => download(att.id)}
              >
                <Download className="h-3 w-3" />
              </Button>
              {canEdit && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity text-destructive"
                  onClick={() => deleteAttachment.mutate(att.id)}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
