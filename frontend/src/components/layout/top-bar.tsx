import { Moon, Sun } from "lucide-react"
import { Button } from "@/components/ui/button"
import { UserMenu } from "@/components/layout/user-menu"
import { useTheme } from "@/providers/theme-provider"

export function TopBar() {
  const { theme, toggleTheme } = useTheme()

  return (
    <header className="h-12 border-b border-border bg-background/95 backdrop-blur-sm flex items-center px-4 gap-2 sticky top-0 z-40">
      <span className="font-semibold text-sm text-foreground mr-auto">Tenantrix</span>

      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8"
        onClick={toggleTheme}
        aria-label="Toggle theme"
      >
        {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      </Button>

      <UserMenu />
    </header>
  )
}
