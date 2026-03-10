import { X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { AuditFilters } from "@/types/audit"

// All known resource types from the backend
const RESOURCE_TYPES = ["org", "project", "task", "member", "invite", "comment"]

// Known action prefixes derived from backend write_audit calls
const ACTIONS = [
  "org.created", "org.updated",
  "invite.sent", "invite.accepted",
  "member.role_changed", "member.removed",
  "project.created", "project.updated", "project.deleted",
  "task.created", "task.updated", "task.deleted", "task.label_added", "task.label_removed",
  "comment.created", "comment.updated", "comment.deleted",
]

interface AuditFiltersProps {
  filters: Omit<AuditFilters, "limit" | "offset">
  onChange: (filters: Omit<AuditFilters, "limit" | "offset">) => void
}

export function AuditFiltersBar({ filters, onChange }: AuditFiltersProps) {
  const hasFilters = !!(filters.action || filters.resource_type || filters.actor_user_id || filters.since || filters.until)

  function set<K extends keyof typeof filters>(key: K, value: typeof filters[K]) {
    onChange({ ...filters, [key]: value || undefined })
  }

  function clearAll() {
    onChange({})
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      {/* Action filter */}
      <Select value={filters.action ?? "__all__"} onValueChange={(v) => set("action", v === "__all__" ? undefined : v)}>
        <SelectTrigger className="h-8 w-48 text-xs">
          <SelectValue placeholder="All actions" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">All actions</SelectItem>
          {ACTIONS.map((a) => (
            <SelectItem key={a} value={a}>{a}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Resource type filter */}
      <Select
        value={filters.resource_type ?? "__all__"}
        onValueChange={(v) => set("resource_type", v === "__all__" ? undefined : v)}
      >
        <SelectTrigger className="h-8 w-40 text-xs">
          <SelectValue placeholder="All types" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">All types</SelectItem>
          {RESOURCE_TYPES.map((rt) => (
            <SelectItem key={rt} value={rt}>{rt}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Actor user ID filter (free-text UUID) */}
      <Input
        className="h-8 w-64 text-xs"
        placeholder="Actor user ID…"
        value={filters.actor_user_id ?? ""}
        onChange={(e) => set("actor_user_id", e.target.value || undefined)}
      />

      {/* Date range */}
      <Input
        type="datetime-local"
        className="h-8 w-48 text-xs"
        title="Since"
        value={filters.since ? filters.since.slice(0, 16) : ""}
        onChange={(e) =>
          set("since", e.target.value ? new Date(e.target.value).toISOString() : undefined)
        }
      />
      <Input
        type="datetime-local"
        className="h-8 w-48 text-xs"
        title="Until"
        value={filters.until ? filters.until.slice(0, 16) : ""}
        onChange={(e) =>
          set("until", e.target.value ? new Date(e.target.value).toISOString() : undefined)
        }
      />

      {hasFilters && (
        <Button variant="ghost" size="sm" className="h-8 gap-1.5 text-xs" onClick={clearAll}>
          <X className="h-3.5 w-3.5" />
          Clear
        </Button>
      )}
    </div>
  )
}
