import { X } from "lucide-react"
import { cn } from "@/lib/utils"
import type { Label } from "@/types/task"

interface LabelBadgeProps {
  label: Label
  onRemove?: () => void
  className?: string
}

export function LabelBadge({ label, onRemove, className }: LabelBadgeProps) {
  const style = label.color
    ? { backgroundColor: `${label.color}26`, color: label.color, borderColor: `${label.color}66` }
    : undefined

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium",
        !label.color && "bg-accent text-accent-foreground border-border",
        className
      )}
      style={style}
    >
      {label.name}
      {onRemove && (
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); onRemove() }}
          className="ml-0.5 rounded-full hover:opacity-70"
          aria-label={`Remove label ${label.name}`}
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </span>
  )
}
