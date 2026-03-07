import { LogOut } from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useAppStore } from "@/store/app-store"
import { useLogout } from "@/hooks/use-auth"
import { getInitials } from "@/lib/utils"

export function UserMenu() {
  const { user } = useAppStore()
  const logout = useLogout()

  if (!user) return null

  const initials = getInitials(user.full_name, user.email)

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="flex items-center gap-2 rounded-md px-2 py-1 hover:bg-accent transition-colors outline-none">
          <Avatar className="h-7 w-7">
            <AvatarFallback className="text-xs bg-primary text-primary-foreground">
              {initials}
            </AvatarFallback>
          </Avatar>
          <span className="text-sm text-foreground hidden sm:block max-w-32 truncate">
            {user.full_name ?? user.email}
          </span>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        <DropdownMenuLabel className="font-normal">
          <p className="text-sm font-medium">{user.full_name ?? "—"}</p>
          <p className="text-xs text-muted-foreground truncate">{user.email}</p>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          className="text-destructive focus:text-destructive cursor-pointer"
          onClick={() => logout.mutate()}
          disabled={logout.isPending}
        >
          <LogOut className="mr-2 h-4 w-4" />
          {logout.isPending ? "Signing out..." : "Sign out"}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
