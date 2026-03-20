import { useCallback, useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { Search, FileText, FolderKanban } from "lucide-react"
import { useQuery } from "@tanstack/react-query"
import {
  Dialog, DialogContent,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { apiClient } from "@/lib/api-client"
import { useAppStore } from "@/store/app-store"
import { cn } from "@/lib/utils"

interface SearchResult {
  id: string
  type: "task" | "project"
  title: string
  status?: string
  project_id?: string
  project_name?: string
  identifier?: string | null
  sequence_id?: number | null
  state_name?: string | null
  state_color?: string | null
  description?: string | null
}

export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState("")
  const [selectedIndex, setSelectedIndex] = useState(0)
  const navigate = useNavigate()
  const activeOrg = useAppStore((s) => s.activeOrg)
  const openTaskPanel = useAppStore((s) => s.openTaskPanel)
  const orgId = activeOrg?.id ?? ""

  // Keyboard shortcut
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault()
        setOpen(true)
      }
      if (e.key === "/" && !["INPUT", "TEXTAREA", "SELECT"].includes((e.target as HTMLElement)?.tagName)) {
        e.preventDefault()
        setOpen(true)
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [])

  const { data } = useQuery({
    queryKey: ["search", orgId, query],
    queryFn: () =>
      apiClient
        .get(`organizations/${orgId}/search`, { searchParams: { q: query } })
        .json<{ results: SearchResult[] }>(),
    enabled: !!orgId && query.length >= 1 && open,
    staleTime: 1000 * 5,
  })

  const results = data?.results ?? []

  const handleSelect = useCallback((result: SearchResult) => {
    setOpen(false)
    setQuery("")
    if (result.type === "task" && result.project_id) {
      navigate(`/orgs/${orgId}/projects/${result.project_id}/board`)
      setTimeout(() => openTaskPanel(result.id), 100)
    } else if (result.type === "project") {
      navigate(`/orgs/${orgId}/projects/${result.id}/board`)
    }
  }, [navigate, orgId, openTaskPanel])

  useEffect(() => {
    setSelectedIndex(0)
  }, [query])

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault()
      setSelectedIndex((i) => Math.min(i + 1, results.length - 1))
    } else if (e.key === "ArrowUp") {
      e.preventDefault()
      setSelectedIndex((i) => Math.max(i - 1, 0))
    } else if (e.key === "Enter" && results[selectedIndex]) {
      handleSelect(results[selectedIndex])
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { setOpen(v); if (!v) setQuery("") }}>
      <DialogContent className="sm:max-w-lg p-0 gap-0 overflow-hidden" aria-label="Search tasks and projects">
        <div className="flex items-center border-b border-border/60 px-3">
          <Search className="h-4 w-4 text-primary/60 shrink-0" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search tasks, projects..."
            className="border-0 shadow-none focus-visible:ring-0 focus-visible:shadow-none h-11"
            autoFocus
          />
        </div>
        <div className="max-h-72 overflow-y-auto py-1">
          {query.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-6">
              Type to search across your organization
            </p>
          )}
          {query.length > 0 && results.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-6">No results found.</p>
          )}
          {results.map((result, idx) => (
            <button
              key={`${result.type}-${result.id}`}
              className={cn(
                "w-full flex items-center gap-3 px-4 py-2 text-sm text-left transition-colors",
                idx === selectedIndex
                  ? "bg-primary/10 dark:bg-primary/15 text-foreground"
                  : "hover:bg-accent",
              )}
              onClick={() => handleSelect(result)}
              onMouseEnter={() => setSelectedIndex(idx)}
            >
              {result.type === "task" ? (
                <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
              ) : (
                <FolderKanban className="h-4 w-4 text-muted-foreground shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <p className="truncate">{result.title}</p>
                <div className="flex items-center gap-1.5 mt-0.5">
                  {result.type === "task" && result.identifier && result.sequence_id != null && (
                    <span className="text-[10px] text-muted-foreground font-mono">
                      {result.identifier}-{result.sequence_id}
                    </span>
                  )}
                  {result.state_color && result.state_name && (
                    <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
                      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: result.state_color }} />
                      {result.state_name}
                    </span>
                  )}
                  {result.project_name && result.type === "task" && (
                    <span className="text-[10px] text-muted-foreground truncate">{result.project_name}</span>
                  )}
                  {result.type === "project" && (
                    <span className="text-[10px] text-muted-foreground">Project</span>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
        <div className="border-t border-border/60 px-3 py-2 text-[11px] text-muted-foreground flex items-center gap-3">
          <span><kbd className="px-1 rounded bg-muted dark:bg-primary/10 text-[10px]">↑↓</kbd> navigate</span>
          <span><kbd className="px-1 rounded bg-muted dark:bg-primary/10 text-[10px]">↵</kbd> select</span>
          <span><kbd className="px-1 rounded bg-muted dark:bg-primary/10 text-[10px]">esc</kbd> close</span>
        </div>
      </DialogContent>
    </Dialog>
  )
}
