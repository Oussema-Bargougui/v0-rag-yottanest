"use client"

import * as React from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import {
  Send,
  FileText,
  Bot,
  User,
  Loader2,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  ArrowLeft,
  Upload,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import {
  queryDocuments,
  getSessionInfo,
  type RAGQueryResponse,
  type RAGSourceInfo,
  type RAGSessionInfo,
} from "@/lib/api/rag-documents"

// --- Types ---

interface ChatMessage {
  id: string
  type: "user" | "assistant"
  content: string
  sources?: RAGSourceInfo[]
  timestamp: Date
  error?: string
}

// --- Components ---

function ChatMessageBubble({ message }: { message: ChatMessage }) {
  const [showSources, setShowSources] = React.useState(false)
  const isUser = message.type === "user"

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("flex gap-3 mb-4", isUser ? "flex-row-reverse" : "flex-row")}
    >
      {/* Avatar */}
      <div
        className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
          isUser ? "bg-primary-500 text-white" : "bg-secondary-100 text-secondary-600"
        )}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Message */}
      <div className={cn("flex flex-col max-w-[75%]", isUser ? "items-end" : "items-start")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-3",
            isUser
              ? "bg-primary-500 text-white rounded-br-md"
              : "bg-white border border-neutral-200 text-neutral-800 rounded-bl-md shadow-sm"
          )}
        >
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* Sources */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-2 w-full">
            <button
              onClick={() => setShowSources(!showSources)}
              className="flex items-center gap-1 text-xs text-neutral-500 hover:text-neutral-700 transition-colors"
            >
              <FileText className="w-3 h-3" />
              {message.sources.length} source{message.sources.length > 1 ? "s" : ""}
              {showSources ? (
                <ChevronUp className="w-3 h-3" />
              ) : (
                <ChevronDown className="w-3 h-3" />
              )}
            </button>

            <AnimatePresence>
              {showSources && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-2 space-y-2"
                >
                  {message.sources.map((source, i) => (
                    <div
                      key={i}
                      className="bg-neutral-50 border border-neutral-200 rounded-lg p-3 text-xs"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-neutral-700">{source.filename}</span>
                        <span className="text-neutral-400">
                          {(source.similarity_score * 100).toFixed(0)}% match
                        </span>
                      </div>
                      <p className="text-neutral-500 line-clamp-2">{source.text_preview}</p>
                    </div>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* Error */}
        {message.error && (
          <div className="mt-2 flex items-center gap-1 text-xs text-amber-600">
            <AlertCircle className="w-3 h-3" />
            {message.error}
          </div>
        )}

        {/* Timestamp */}
        <span className="text-[10px] text-neutral-400 mt-1">
          {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>
    </motion.div>
  )
}

function TypingIndicator() {
  return (
    <div className="flex gap-3 mb-4">
      <div className="w-8 h-8 rounded-full bg-secondary-100 text-secondary-600 flex items-center justify-center">
        <Bot className="w-4 h-4" />
      </div>
      <div className="bg-white border border-neutral-200 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
        <div className="flex gap-1">
          <motion.div
            className="w-2 h-2 bg-neutral-400 rounded-full"
            animate={{ y: [0, -5, 0] }}
            transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
          />
          <motion.div
            className="w-2 h-2 bg-neutral-400 rounded-full"
            animate={{ y: [0, -5, 0] }}
            transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }}
          />
          <motion.div
            className="w-2 h-2 bg-neutral-400 rounded-full"
            animate={{ y: [0, -5, 0] }}
            transition={{ duration: 0.6, repeat: Infinity, delay: 0.4 }}
          />
        </div>
      </div>
    </div>
  )
}

// --- Main Page ---

export default function ChatPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const sessionId = searchParams.get("session")

  const [messages, setMessages] = React.useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = React.useState("")
  const [isLoading, setIsLoading] = React.useState(false)
  const [sessionInfo, setSessionInfo] = React.useState<RAGSessionInfo | null>(null)
  const [error, setError] = React.useState<string | null>(null)

  const messagesEndRef = React.useRef<HTMLDivElement>(null)
  const inputRef = React.useRef<HTMLInputElement>(null)

  // Scroll to bottom when messages change
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Load session info on mount
  React.useEffect(() => {
    if (sessionId) {
      getSessionInfo(sessionId)
        .then(setSessionInfo)
        .catch((err) => setError(err.message))
    }
  }, [sessionId])

  // Add welcome message
  React.useEffect(() => {
    if (sessionInfo && messages.length === 0) {
      const filesCount = sessionInfo.files?.length || 0
      setMessages([
        {
          id: "welcome",
          type: "assistant",
          content: `Hello! I've analyzed ${filesCount} document${filesCount > 1 ? "s" : ""} for you. Ask me anything about the content and I'll help you find the information you need.\n\nFor compliance and KYC analysis, try asking questions like:\n• "What are the key findings in these documents?"\n• "Are there any risk indicators mentioned?"\n• "Summarize the main points"`,
          timestamp: new Date(),
        },
      ])
    }
  }, [sessionInfo, messages.length])

  // Handle sending a message
  const handleSendMessage = async () => {
    if (!inputValue.trim() || !sessionId || isLoading) return

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      type: "user",
      content: inputValue.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue("")
    setIsLoading(true)

    try {
      const response = await queryDocuments(sessionId, userMessage.content)

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        type: "assistant",
        content: response.answer,
        sources: response.sources,
        timestamp: new Date(),
        error: response.error || undefined,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        type: "assistant",
        content: "I encountered an error while processing your question. Please try again.",
        timestamp: new Date(),
        error: err instanceof Error ? err.message : "Unknown error",
      }

      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // No session ID provided
  if (!sessionId) {
    return (
      <div className="container mx-auto max-w-4xl p-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col items-center py-12 text-center">
              <div className="w-16 h-16 rounded-full bg-neutral-100 flex items-center justify-center mb-4">
                <FileText className="w-8 h-8 text-neutral-400" />
              </div>
              <h2 className="text-xl font-semibold text-neutral-800 mb-2">No Documents Loaded</h2>
              <p className="text-neutral-500 mb-6 max-w-md">
                You need to upload and process documents before you can chat with them.
              </p>
              <Button onClick={() => router.push("/dashboard/documents/upload")} className="gap-2">
                <Upload className="w-4 h-4" />
                Upload Documents
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Error loading session
  if (error) {
    return (
      <div className="container mx-auto max-w-4xl p-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col items-center py-12 text-center">
              <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mb-4">
                <AlertCircle className="w-8 h-8 text-red-500" />
              </div>
              <h2 className="text-xl font-semibold text-neutral-800 mb-2">Session Not Found</h2>
              <p className="text-neutral-500 mb-6 max-w-md">{error}</p>
              <Button onClick={() => router.push("/dashboard/documents/upload")} className="gap-2">
                <Upload className="w-4 h-4" />
                Upload New Documents
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto max-w-6xl p-6 h-[calc(100vh-120px)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => router.push("/dashboard/documents/upload")}
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-neutral-900">Chat with Documents</h1>
            <p className="text-sm text-neutral-500">
              {sessionInfo?.files?.length || 0} document{(sessionInfo?.files?.length || 0) > 1 ? "s" : ""} loaded
            </p>
          </div>
        </div>
      </div>

      <div className="flex gap-6 flex-1 min-h-0">
        {/* Chat Area */}
        <Card className="flex-1 flex flex-col min-h-0">
          <ScrollArea className="flex-1 p-4">
            <div className="space-y-1">
              {messages.map((message) => (
                <ChatMessageBubble key={message.id} message={message} />
              ))}
              {isLoading && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Input Area */}
          <div className="border-t border-neutral-200 p-4">
            <div className="flex gap-2">
              <Input
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Ask a question about your documents..."
                disabled={isLoading}
                className="flex-1"
              />
              <Button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isLoading}
                className="gap-2"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
                Send
              </Button>
            </div>
            <p className="text-xs text-neutral-400 mt-2">
              Powered by Llama 3.1 running locally via Ollama
            </p>
          </div>
        </Card>

        {/* Sidebar - Document Info */}
        <Card className="w-80 hidden lg:block">
          <CardHeader>
            <CardTitle className="text-base">Loaded Documents</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px]">
              <div className="space-y-2">
                {sessionInfo?.files?.map((file, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-2 p-2 bg-neutral-50 rounded-lg"
                  >
                    <div className="w-8 h-8 rounded bg-red-100 flex items-center justify-center">
                      <FileText className="w-4 h-4 text-red-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-neutral-700 truncate">
                        {file.filename}
                      </p>
                      <p className="text-xs text-neutral-400">
                        {(file.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>

            <div className="mt-4 pt-4 border-t border-neutral-200">
              <Button
                variant="outline"
                className="w-full gap-2"
                onClick={() => router.push("/dashboard/documents/upload")}
              >
                <Upload className="w-4 h-4" />
                Upload More Documents
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
