import { useState } from "react"
import { Plus, Tag } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { LabelBadge } from "./label-badge"
import { useAddLabel, useRemoveLabel } from "@/hooks/use-tasks"
import type { Label } from "@/types/task"

interface LabelPickerProps {
  orgId: string
  projectId: string
  taskId: string
  currentLabels: Label[]
  disabled?: boolean
  compact?: boolean  // smaller add-label trigger for properties panel
}

const PRESET_COLORS = [
  "#ef4444", "#f97316", "#eab308", "#22c55e",
  "#3b82f6", "#8b5cf6", "#ec4899", "#6b7280",
]

export function LabelPicker({ orgId, projectId, taskId, currentLabels, disabled, compact }: LabelPickerProps) {
  const [open, setOpen] = useState(false)
  const [newName, setNewName] = useState("")
  const [newColor, setNewColor] = useState(PRESET_COLORS[0])
  const { mutate: addLabel, isPending: isAdding } = useAddLabel(orgId, projectId, taskId)
  const { mutate: removeLabel } = useRemoveLabel(orgId, projectId, taskId)

  function handleAdd() {
    const trimmed = newName.trim()
    if (!trimmed) return
    addLabel({ name: trimmed, color: newColor }, {
      onSuccess: () => { setNewName("") },
    })
  }

  return (
    <div className="flex flex-wrap gap-1 items-center">
      {currentLabels.map((label) => (
        <LabelBadge
          key={label.id}
          label={label}
          onRemove={disabled ? undefined : () => removeLabel(label.name)}
        />
      ))}
      {!disabled && (
        <Popover open={open} onOpenChange={setOpen}>
          <PopoverTrigger asChild>
            {compact ? (
              <button className="flex items-center gap-1 rounded px-1 py-0.5 text-xs text-muted-foreground hover:bg-accent hover:text-foreground transition-colors">
                <Tag className="h-3 w-3" />
                Select label
              </button>
            ) : (
              <Button variant="ghost" size="sm" className="h-6 px-2 gap-1 text-xs text-muted-foreground">
                <Tag className="h-3 w-3" />
                Add label
              </Button>
            )}
          </PopoverTrigger>
          <PopoverContent className="w-64 p-3 space-y-3">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">New label</p>
            <Input
              placeholder="Label name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAdd()}
              className="h-8 text-sm"
            />
            <div className="flex gap-1.5 flex-wrap">
              {PRESET_COLORS.map((c) => (
                <button
                  key={c}
                  type="button"
                  className="h-5 w-5 rounded-full border-2 transition-transform hover:scale-110"
                  style={{
                    backgroundColor: c,
                    borderColor: newColor === c ? "white" : "transparent",
                  }}
                  onClick={() => setNewColor(c)}
                  aria-label={`Color ${c}`}
                />
              ))}
            </div>
            <Button
              size="sm"
              className="w-full gap-1"
              disabled={!newName.trim() || isAdding}
              onClick={handleAdd}
            >
              <Plus className="h-3.5 w-3.5" />
              {isAdding ? "Adding…" : "Add label"}
            </Button>
          </PopoverContent>
        </Popover>
      )}
    </div>
  )
}
