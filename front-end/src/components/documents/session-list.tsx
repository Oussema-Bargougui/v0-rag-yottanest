"use client"

import * as React from "react"
import {
  MessageSquare,
  Trash2,
  Edit2,
  Clock,
  FileText,
  Plus,
  Loader2,
  AlertCircle,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  listSessions,
  deleteSession,
  renameSession,
  type RAGSessionListItem,
} from "@/lib/api/rag-documents"

interface SessionListProps {
  selectedSessionId: string | null
  onSelectSession: (sessionId: string) => void
  onCreateSession: () => void
}

export function SessionList({
  selectedSessionId,
  onSelectSession,
  onCreateSession,
}: SessionListProps) {
  const [sessions, setSessions] = React.useState<RAGSessionListItem[]>([])
  const [isLoading, setIsLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)
  const [editingId, setEditingId] = React.useState<string | null>(null)
  const [editingName, setEditingName] = React.useState("")
  const [deletingId, setDeletingId] = React.useState<string | null>(null)

  // Load sessions
  const loadSessions = React.useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await listSessions()
      setSessions(data.sessions || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sessions")
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Initial load
  React.useEffect(() => {
    loadSessions()
  }, [loadSessions])

  // Handle delete session
  const handleDelete = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation()
    if (!confirm("Are you sure you want to delete this session? This cannot be undone.")) {
      return
    }

    setDeletingId(sessionId)
    try {
      await deleteSession(sessionId)
      await loadSessions()
      
      // If deleted session was selected, clear selection
      if (selectedSessionId === sessionId) {
        onSelectSession("")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete session")
    } finally {
      setDeletingId(null)
    }
  }

  // Handle start rename
  const handleStartRename = (e: React.MouseEvent, session: RAGSessionListItem) => {
    e.stopPropagation()
    setEditingId(session.session_id)
    setEditingName(session.session_id)
  }

  // Handle save rename
  const handleSaveRename = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!editingId || !editingName.trim()) return

    try {
      await renameSession(editingId, editingName)
      await loadSessions()
      setEditingId(null)
      setEditingName("")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to rename session")
    }
  }

  // Handle cancel rename
  const handleCancelRename = (e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingId(null)
    setEditingName("")
  }

  // Format date
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "Unknown"
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      })
    } catch {
      return "Unknown"
    }
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold">Sessions</CardTitle>
          <Button
            size="icon-sm"
            variant="ghost"
            onClick={onCreateSession}
            className="h-8 w-8"
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="flex-1 overflow-hidden p-0">
        <ScrollArea className="h-full">
          <div className="p-4 space-y-2">
            {error && (
              <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : sessions.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No sessions yet</p>
                <p className="text-xs mt-1">Upload documents to create a session</p>
              </div>
            ) : (
              sessions.map((session) => (
                <div
                  key={session.session_id}
                  onClick={() => onSelectSession(session.session_id)}
                  className={`
                    group relative p-3 rounded-lg border transition-all cursor-pointer
                    ${
                      selectedSessionId === session.session_id
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/50 hover:bg-muted/50"
                    }
                  `}
                >
                  {editingId === session.session_id ? (
                    <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                      <Input
                        value={editingName}
                        onChange={(e) => setEditingName(e.target.value)}
                        className="h-8 text-sm"
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            handleSaveRename(e as any)
                          } else if (e.key === "Escape") {
                            handleCancelRename(e as any)
                          }
                        }}
                        autoFocus
                      />
                      <Button
                        size="icon-sm"
                        variant="ghost"
                        onClick={handleSaveRename}
                        className="h-8 w-8"
                      >
                        ✓
                      </Button>
                      <Button
                        size="icon-sm"
                        variant="ghost"
                        onClick={handleCancelRename}
                        className="h-8 w-8"
                      >
                        ✕
                      </Button>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <MessageSquare className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                            <p className="text-sm font-medium truncate">
                              {session.session_id}
                            </p>
                          </div>
                          <div className="flex items-center gap-3 text-xs text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <FileText className="h-3 w-3" />
                              <span>{session.document_count} docs</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              <span>{formatDate(session.created_date)}</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Button
                            size="icon-sm"
                            variant="ghost"
                            onClick={(e) => handleStartRename(e, session)}
                            className="h-7 w-7"
                          >
                            <Edit2 className="h-3 w-3" />
                          </Button>
                          <Button
                            size="icon-sm"
                            variant="ghost"
                            onClick={(e) => handleDelete(e, session.session_id)}
                            disabled={deletingId === session.session_id}
                            className="h-7 w-7 text-destructive hover:text-destructive"
                          >
                            {deletingId === session.session_id ? (
                              <Loader2 className="h-3 w-3 animate-spin" />
                            ) : (
                              <Trash2 className="h-3 w-3" />
                            )}
                          </Button>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}