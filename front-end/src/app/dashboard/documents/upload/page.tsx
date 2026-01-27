"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { UploadCloud, FileIcon, ImageIcon, ExternalLink, X, FileText, Loader2, Play, MessageSquare } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { cn } from "@/lib/utils"
import { ProcessingAnimation } from "@/components/documents/processing-animation"
import {
  uploadDocuments,
  processDocuments,
  getProcessingStatus,
  type ProcessingStage,
  type RAGProcessingStatus,
} from "@/lib/api/rag-documents"

// --- Components ---

interface PdfPreviewProps {
  file: File
  showAllPages?: boolean
}

function PdfPreview({ file, showAllPages = false }: PdfPreviewProps) {
  const [pdfUrl, setPdfUrl] = React.useState<string | null>(null)

  React.useEffect(() => {
    const url = URL.createObjectURL(file)
    setPdfUrl(url)
    return () => {
      URL.revokeObjectURL(url)
    }
  }, [file])

  if (!pdfUrl) {
    return (
      <div className="flex h-40 flex-col items-center justify-center gap-2">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
        <p className="text-xs text-slate-500">Loading PDF...</p>
      </div>
    )
  }

  if (!showAllPages) {
    return (
      <div className="relative flex flex-col items-center justify-center h-40 pt-4 bg-gradient-to-br from-red-50 to-red-100 rounded-lg border border-red-200">
        <FileText className="h-12 w-12 text-red-500 mb-2" />
        <p className="text-xs font-medium text-red-700">PDF Document</p>
        <p className="text-[10px] text-red-500 mt-1">Click to preview</p>
      </div>
    )
  }

  return (
    <div className="w-full h-full min-h-[500px] pt-4">
      <iframe
        src={`${pdfUrl}#toolbar=0&navpanes=0`}
        className="w-full h-full min-h-[500px] rounded-lg border-0"
        title={file.name}
      />
    </div>
  )
}

// --- Main Page ---

type PageState = "upload" | "uploading" | "processing" | "ready" | "error"

export default function UploadPage() {
  const router = useRouter()
  const [files, setFiles] = React.useState<File[]>([])
  const [entityId, setEntityId] = React.useState("")
  const [isDragging, setIsDragging] = React.useState(false)
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  // Processing state
  const [pageState, setPageState] = React.useState<PageState>("upload")
  const [sessionId, setSessionId] = React.useState<string | null>(null)
  const [processingStatus, setProcessingStatus] = React.useState<RAGProcessingStatus | null>(null)
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null)
  const [uploadProgress, setUploadProgress] = React.useState({ current: 0, total: 0, filename: "" })

  const onFilesAdded = (newFiles: File[]) => {
    // Filter to only supported file types
    const supportedFiles = newFiles.filter(file => {
      const ext = file.name.toLowerCase()
      return ext.endsWith('.pdf') || ext.endsWith('.txt') || ext.endsWith('.md')
    })
    setFiles((prev) => [...prev, ...supportedFiles])
  }

  const handleRemoveFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const isImage = (file: File) => file.type.startsWith("image/")
  const isPdf = (file: File) => file.type === "application/pdf" || file.name.endsWith(".pdf")

  // Upload and process documents
  const handleProcessDocuments = async () => {
    if (files.length === 0) return

    setPageState("uploading")
    setErrorMessage(null)

    try {
      // Step 1: Upload all files
      const { sessionId: newSessionId, uploads } = await uploadDocuments(
        files,
        undefined,
        (current, total, filename) => {
          setUploadProgress({ current, total, filename })
        }
      )

      setSessionId(newSessionId)
      setPageState("processing")

      // Step 2: Start processing
      await processDocuments(newSessionId)

      // Step 3: Poll for status updates
      const pollStatus = async () => {
        try {
          const status = await getProcessingStatus(newSessionId)
          setProcessingStatus(status)

          if (status.stage === "ready") {
            setPageState("ready")
          } else if (status.stage === "error") {
            setPageState("error")
            setErrorMessage(status.error || "Processing failed")
          } else {
            // Continue polling
            setTimeout(pollStatus, 1000)
          }
        } catch (error) {
          setPageState("error")
          setErrorMessage(error instanceof Error ? error.message : "Failed to get processing status")
        }
      }

      pollStatus()
    } catch (error) {
      setPageState("error")
      setErrorMessage(error instanceof Error ? error.message : "An unexpected error occurred")
    }
  }

  // Navigate to chat
  const handleGoToChat = () => {
    if (sessionId) {
      router.push(`/dashboard/documents/chat?session=${sessionId}`)
    }
  }

  // Reset to start over
  const handleReset = () => {
    setFiles([])
    setPageState("upload")
    setSessionId(null)
    setProcessingStatus(null)
    setErrorMessage(null)
  }

  // Show processing view
  if (pageState === "uploading" || pageState === "processing" || pageState === "ready") {
    return (
      <div className="container mx-auto max-w-4xl p-6">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            {pageState === "uploading" ? "Uploading Documents" :
             pageState === "processing" ? "Processing Documents" :
             "Documents Ready!"}
          </h1>
          <p className="text-slate-500 mt-2">
            {pageState === "uploading"
              ? `Uploading ${uploadProgress.current} of ${uploadProgress.total}: ${uploadProgress.filename}`
              : pageState === "processing"
                ? "Your documents are being analyzed and indexed"
                : "Your documents have been processed and are ready for questions"}
          </p>
        </div>

        <Card>
          <CardContent className="pt-6">
            {pageState === "uploading" ? (
              <div className="flex flex-col items-center py-12">
                <Loader2 className="h-12 w-12 animate-spin text-primary-500 mb-4" />
                <p className="text-lg font-medium text-slate-700">Uploading files...</p>
                <p className="text-sm text-slate-500 mt-2">
                  {uploadProgress.current} of {uploadProgress.total} files uploaded
                </p>
                <div className="w-full max-w-md mt-4">
                  <div className="h-2 bg-neutral-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-500 rounded-full transition-all duration-300"
                      style={{ width: `${(uploadProgress.current / uploadProgress.total) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            ) : (
              <ProcessingAnimation
                currentStage={processingStatus?.stage as ProcessingStage || "extracting"}
                progress={processingStatus?.progress || 0}
                message={processingStatus?.message}
                error={processingStatus?.error}
              />
            )}

            {pageState === "ready" && (
              <div className="flex justify-center gap-4 mt-8 pb-4">
                <Button variant="outline" onClick={handleReset}>
                  Upload More Documents
                </Button>
                <Button onClick={handleGoToChat} className="gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Start Chatting with Documents
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Files processed summary */}
        {(pageState === "processing" || pageState === "ready") && (
          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="text-base">Uploaded Files ({files.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {files.map((file, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-full text-sm text-slate-600"
                  >
                    <FileText className="h-3.5 w-3.5" />
                    <span className="truncate max-w-[200px]">{file.name}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    )
  }

  // Error view
  if (pageState === "error") {
    return (
      <div className="container mx-auto max-w-4xl p-6">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Processing Error</h1>
          <p className="text-slate-500 mt-2">Something went wrong while processing your documents</p>
        </div>

        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col items-center py-8">
              <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mb-4">
                <X className="h-8 w-8 text-red-500" />
              </div>
              <p className="text-lg font-medium text-red-700 mb-2">Processing Failed</p>
              <p className="text-sm text-slate-500 text-center max-w-md">
                {errorMessage || "An unexpected error occurred. Please try again."}
              </p>
              <Button onClick={handleReset} className="mt-6">
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Default upload view
  return (
    <div className="container mx-auto max-w-7xl p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Upload Documents</h1>
        <p className="text-slate-500">Upload documents for Smart Docs processing and AI-powered Q&A</p>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Left Column: Form & Upload */}
        <div className="lg:col-span-2 flex flex-col gap-8">
          <Card>
            <CardHeader>
              <CardTitle>Link to Entity (Optional)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2">
                <Input
                  placeholder="Enter Entity ID (e.g., ENT-4521)"
                  value={entityId}
                  onChange={(e) => setEntityId(e.target.value)}
                />
                <p className="text-xs text-slate-400">Link documents to a specific entity for automatic association</p>
              </div>
            </CardContent>
          </Card>

          <Card className="flex-1">
            <CardHeader>
              <CardTitle>Upload Files</CardTitle>
            </CardHeader>
            <CardContent>
              <div
                onDragOver={(e) => {
                  e.preventDefault()
                  setIsDragging(true)
                }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={(e) => {
                  e.preventDefault()
                  setIsDragging(false)
                  onFilesAdded(Array.from(e.dataTransfer.files))
                }}
                onClick={() => fileInputRef.current?.click()}
                className={cn(
                  "group relative flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-200 bg-slate-50 py-16 transition-all hover:bg-slate-100/50",
                  isDragging && "border-primary bg-slate-100",
                )}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={(e) => e.target.files && onFilesAdded(Array.from(e.target.files))}
                  className="hidden"
                  multiple
                  accept=".pdf,.txt,.md"
                />
                <div className="mb-4 rounded-full bg-white p-4 shadow-sm">
                  <UploadCloud className="h-8 w-8 text-slate-400 group-hover:text-primary" />
                </div>
                <p className="mb-2 text-lg font-medium text-slate-700">Drag and drop files</p>
                <p className="mb-4 text-sm text-slate-500">or click to browse</p>
                <p className="text-xs text-slate-400">Supported: PDF, TXT, MD (Max 25MB each)</p>
              </div>

              {files.length > 0 && (
                <div className="mt-8">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-medium text-slate-900">Selected Files ({files.length})</h3>
                    <Button
                      onClick={handleProcessDocuments}
                      className="gap-2"
                    >
                      <Play className="h-4 w-4" />
                      Process {files.length} Document{files.length > 1 ? 's' : ''}
                    </Button>
                  </div>
                  <div className="space-y-2">
                    {files.map((file, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between rounded-md border border-slate-200 bg-white p-3"
                      >
                        <div className="flex items-center gap-3">
                          <div className={cn(
                            "w-8 h-8 rounded flex items-center justify-center",
                            isPdf(file) ? "bg-red-100" : "bg-blue-100"
                          )}>
                            <FileText className={cn(
                              "h-4 w-4",
                              isPdf(file) ? "text-red-500" : "text-blue-500"
                            )} />
                          </div>
                          <div>
                            <span className="text-sm text-slate-600 truncate block max-w-[300px]">{file.name}</span>
                            <span className="text-xs text-slate-400">{(file.size / 1024).toFixed(1)} KB</span>
                          </div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleRemoveFile(i)
                          }}
                          className="text-slate-400 hover:text-red-500 transition-colors"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Preview */}
        <div className="lg:col-span-1">
          <Card className="h-full">
            <CardHeader>
              <CardTitle>File Preview</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              {files.length === 0 ? (
                <div className="flex h-40 flex-col items-center justify-center rounded-lg border border-dashed border-slate-200 text-slate-400">
                  <p className="text-sm">No files uploaded yet</p>
                </div>
              ) : (
                files.map((file, index) => (
                  <Dialog key={index}>
                    <DialogTrigger asChild>
                      <div className="cursor-pointer overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm hover:border-primary/50 transition-all">
                        <div className="border-b border-slate-100 bg-slate-50/50 px-4 py-2 flex items-center justify-between">
                          <p className="truncate text-xs font-medium text-slate-700">{file.name}</p>
                          <ExternalLink className="h-3 w-3 text-slate-300" />
                        </div>
                        <div className="p-3">
                          {isPdf(file) ? (
                            <PdfPreview file={file} showAllPages={false} />
                          ) : isImage(file) ? (
                            <div className="relative aspect-[4/3] overflow-hidden rounded border border-slate-100 bg-slate-50">
                              <img
                                src={URL.createObjectURL(file) || "/placeholder.svg"}
                                alt={file.name}
                                className="h-full w-full object-contain"
                              />
                            </div>
                          ) : (
                            <div className="flex h-20 items-center justify-center rounded bg-slate-50 text-xs text-slate-400 italic gap-2">
                              <FileIcon className="h-4 w-4" /> Text file
                            </div>
                          )}
                        </div>
                      </div>
                    </DialogTrigger>
                    <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col p-0 overflow-hidden">
                      <DialogHeader className="p-6 border-b">
                        <DialogTitle className="flex items-center gap-2">
                          {isPdf(file) ? (
                            <FileIcon className="h-5 w-5 text-red-500" />
                          ) : (
                            <ImageIcon className="h-5 w-5 text-blue-500" />
                          )}
                          {file.name}
                        </DialogTitle>
                      </DialogHeader>
                      <div className="flex-1 overflow-y-auto bg-slate-100/50 p-6">
                        {isPdf(file) ? (
                          <PdfPreview file={file} showAllPages={true} />
                        ) : isImage(file) ? (
                          <div className="flex justify-center">
                            <img
                              src={URL.createObjectURL(file) || "/placeholder.svg"}
                              alt={file.name}
                              className="h-auto max-w-full rounded-lg shadow-lg"
                            />
                          </div>
                        ) : (
                          <div className="flex flex-col items-center justify-center py-20 text-slate-500">
                            <FileIcon className="h-16 w-16 mb-4 text-slate-200" />
                            <p className="font-medium text-lg">Full preview not available</p>
                            <p className="text-sm">Type: {file.type || "Text file"}</p>
                          </div>
                        )}
                      </div>
                    </DialogContent>
                  </Dialog>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
