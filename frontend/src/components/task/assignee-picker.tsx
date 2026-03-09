import { useState } from "react"
import { Check, ChevronsUpDown, UserX } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"
import { useMembers } from "@/hooks/use-members"

interface AssigneePickerProps {
  orgId: string
  value: string | null
  onChange: (userId: string | null) => void
  disabled?: boolean
  compact?: boolean  // slim trigger for properties panel
}

function initials(name: string) {
  return name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)
}

export function AssigneePicker({ orgId, value, onChange, disabled, compact }: AssigneePickerProps) {
  const [open, setOpen] = useState(false)
  const { data: members = [] } = useMembers(orgId)

  const selectedMember = members.find((m) => m.user_id === value)

  function displayName(m: { full_name?: string | null; email?: string; user_id: string }) {
    return m.full_name ?? m.email ?? m.user_id
  }

  const trigger = compact ? (
    <button
      disabled={disabled}
      className="flex items-center gap-1.5 rounded px-1 py-0.5 text-xs hover:bg-accent transition-colors w-full text-left disabled:opacity-50"
    >
      {selectedMember ? (
        <>
          <Avatar className="h-5 w-5">
            <AvatarFallback className="text-[10px]">{initials(displayName(selectedMember))}</AvatarFallback>
          </Avatar>
          <span className="truncate">{displayName(selectedMember)}</span>
        </>
      ) : (
        <span className="text-muted-foreground">None</span>
      )}
    </button>
  ) : (
    <Button
      variant="outline"
      role="combobox"
      disabled={disabled}
      className="w-full justify-between font-normal"
    >
      {selectedMember ? (
        <span className="flex items-center gap-2">
          <Avatar className="h-5 w-5">
            <AvatarFallback className="text-[10px]">
              {initials(displayName(selectedMember))}
            </AvatarFallback>
          </Avatar>
          <span className="truncate">{displayName(selectedMember)}</span>
        </span>
      ) : (
        <span className="text-muted-foreground">Unassigned</span>
      )}
      <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
    </Button>
  )

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>{trigger}</PopoverTrigger>
      <PopoverContent className="w-64 p-1">
        <div className="flex flex-col gap-0.5">
          <button
            className="flex items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-accent"
            onClick={() => { onChange(null); setOpen(false) }}
          >
            <UserX className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Unassigned</span>
            {value === null && <Check className="ml-auto h-4 w-4" />}
          </button>
          {members.map((m) => (
            <button
              key={m.user_id}
              className={cn(
                "flex items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-accent",
              )}
              onClick={() => { onChange(m.user_id); setOpen(false) }}
            >
              <Avatar className="h-5 w-5">
                <AvatarFallback className="text-[10px]">
                  {initials(displayName(m))}
                </AvatarFallback>
              </Avatar>
              <span className="truncate">{displayName(m)}</span>
              {value === m.user_id && <Check className="ml-auto h-4 w-4" />}
            </button>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  )
}
