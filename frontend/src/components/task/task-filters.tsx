import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { PriorityIcon } from "./priority-icon"
import { IssueTypeIcon } from "./issue-type-icon"
import type { TaskFilters, TaskPriority, IssueType } from "@/types/task"
import { TASK_PRIORITY_LABELS, ISSUE_TYPE_LABELS } from "@/types/task"
import { useMembers } from "@/hooks/use-members"
import { useProjectStates } from "@/hooks/use-project-states"

interface TaskFiltersBarProps {
  orgId: string
  projectId: string
  filters: TaskFilters
  onChange: (filters: TaskFilters) => void
}

const ALL = "__all__"

export function TaskFiltersBar({ orgId, projectId, filters, onChange }: TaskFiltersBarProps) {
  const { data: members = [] } = useMembers(orgId)
  const { data: states = [] } = useProjectStates(orgId, projectId)

  const hasFilters = !!(filters.state_id || filters.priority || filters.assignee_user_id || filters.issue_type)

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {/* State */}
      <Select
        value={filters.state_id ?? ALL}
        onValueChange={(v) => onChange({ ...filters, state_id: v === ALL ? undefined : v })}
      >
        <SelectTrigger className="h-8 w-36 text-xs">
          <SelectValue placeholder="State" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>All states</SelectItem>
          {states.map((s) => (
            <SelectItem key={s.id} value={s.id}>
              <span className="flex items-center gap-1.5">
                <span
                  className="inline-block h-2 w-2 rounded-full shrink-0"
                  style={{ backgroundColor: s.color }}
                />
                {s.name}
              </span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Priority */}
      <Select
        value={filters.priority ?? ALL}
        onValueChange={(v) => onChange({ ...filters, priority: v === ALL ? undefined : v as TaskPriority })}
      >
        <SelectTrigger className="h-8 w-36 text-xs">
          <SelectValue placeholder="Priority" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>All priorities</SelectItem>
          {(Object.keys(TASK_PRIORITY_LABELS) as TaskPriority[]).map((p) => (
            <SelectItem key={p} value={p}>
              <span className="flex items-center gap-1.5">
                <PriorityIcon priority={p} />
                {TASK_PRIORITY_LABELS[p]}
              </span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Assignee */}
      <Select
        value={filters.assignee_user_id ?? ALL}
        onValueChange={(v) => onChange({ ...filters, assignee_user_id: v === ALL ? undefined : v })}
      >
        <SelectTrigger className="h-8 w-40 text-xs">
          <SelectValue placeholder="Assignee" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>All assignees</SelectItem>
          {members.map((m) => (
            <SelectItem key={m.user_id} value={m.user_id}>
              {m.full_name ?? m.email ?? m.user_id}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Issue Type */}
      <Select
        value={filters.issue_type ?? ALL}
        onValueChange={(v) => onChange({ ...filters, issue_type: v === ALL ? undefined : v as IssueType })}
      >
        <SelectTrigger className="h-8 w-36 text-xs">
          <SelectValue placeholder="Type" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>All types</SelectItem>
          {(Object.entries(ISSUE_TYPE_LABELS) as [IssueType, string][]).map(([v, label]) => (
            <SelectItem key={v} value={v}>
              <span className="flex items-center gap-1.5">
                <IssueTypeIcon type={v} />
                {label}
              </span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {hasFilters && (
        <Button
          variant="ghost"
          size="sm"
          className="h-8 text-xs text-muted-foreground"
          onClick={() => onChange({})}
        >
          Clear filters
        </Button>
      )}
    </div>
  )
}
