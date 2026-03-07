export const queryKeys = {
  user: () => ["user"] as const,
  orgs: () => ["orgs"] as const,
  org: (orgId: string) => ["org", orgId] as const,
  members: (orgId: string) => ["org", orgId, "members"] as const,
  invites: (orgId: string) => ["org", orgId, "invites"] as const,
  projects: (orgId: string) => ["org", orgId, "projects"] as const,
  project: (orgId: string, projectId: string) =>
    ["org", orgId, "project", projectId] as const,
  tasks: (orgId: string, projectId: string, filters?: Record<string, unknown>) =>
    ["org", orgId, "project", projectId, "tasks", filters] as const,
  task: (orgId: string, taskId: string) =>
    ["org", orgId, "task", taskId] as const,
  comments: (orgId: string, taskId: string) =>
    ["org", orgId, "task", taskId, "comments"] as const,
  auditLogs: (orgId: string, filters?: Record<string, unknown>) =>
    ["org", orgId, "audit-logs", filters] as const,
}
