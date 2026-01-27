"use client"

import { useState, useCallback } from "react"
import {
  Upload,
  FileText,
  CheckCircle,
  Clock,
  AlertCircle,
  X,
  Eye,
  Download,
  Trash2,
  Filter,
  Search,
} from "lucide-react"
import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface Document {
  id: string
  name: string
  type: "kyc" | "invoice" | "contract" | "report" | "other"
  entity: string
  entityId: string
  status: "processing" | "completed" | "failed" | "pending"
  uploadedAt: string
  processedAt?: string
  confidence?: number
  extractedData?: {
    fields: number
    entities: number
  }
}

const mockDocuments: Document[] = [
  {
    id: "DOC-001",
    name: "KYC_Acme_Corp_2024.pdf",
    type: "kyc",
    entity: "Acme Corporation Ltd",
    entityId: "ENT-4521",
    status: "completed",
    uploadedAt: "2024-01-15T10:30:00Z",
    processedAt: "2024-01-15T10:32:15Z",
    confidence: 94,
    extractedData: { fields: 28, entities: 5 },
  },
  {
    id: "DOC-002",
    name: "Invoice_GlobalTrading_Q4.pdf",
    type: "invoice",
    entity: "Global Trading Inc",
    entityId: "ENT-3892",
    status: "processing",
    uploadedAt: "2024-01-15T09:45:00Z",
  },
  {
    id: "DOC-003",
    name: "Contract_TechSolutions.docx",
    type: "contract",
    entity: "Tech Solutions Corp",
    entityId: "ENT-1983",
    status: "completed",
    uploadedAt: "2024-01-14T16:20:00Z",
    processedAt: "2024-01-14T16:25:30Z",
    confidence: 87,
    extractedData: { fields: 45, entities: 8 },
  },
  {
    id: "DOC-004",
    name: "Due_Diligence_Pacific.pdf",
    type: "report",
    entity: "Pacific Ventures LLC",
    entityId: "ENT-7892",
    status: "failed",
    uploadedAt: "2024-01-14T14:00:00Z",
  },
  {
    id: "DOC-005",
    name: "ID_Verification_Scan.jpg",
    type: "kyc",
    entity: "Eastern Commerce Ltd",
    entityId: "ENT-5123",
    status: "pending",
    uploadedAt: "2024-01-14T11:30:00Z",
  },
]

const typeConfig = {
  kyc: { label: "KYC", className: "bg-blue-100 text-blue-700" },
  invoice: { label: "Invoice", className: "bg-green-100 text-green-700" },
  contract: { label: "Contract", className: "bg-purple-100 text-purple-700" },
  report: { label: "Report", className: "bg-orange-100 text-orange-700" },
  other: { label: "Other", className: "bg-neutral-100 text-neutral-700" },
}

const statusConfig = {
  processing: {
    label: "Processing",
    icon: Clock,
    className: "bg-yellow-100 text-yellow-700",
  },
  completed: {
    label: "Completed",
    icon: CheckCircle,
    className: "bg-green-100 text-green-700",
  },
  failed: {
    label: "Failed",
    icon: AlertCircle,
    className: "bg-red-100 text-red-700",
  },
  pending: {
    label: "Pending",
    icon: Clock,
    className: "bg-neutral-100 text-neutral-700",
  },
}

export default function DocumentsPage() {
  const [isDragOver, setIsDragOver] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [searchQuery, setSearchQuery] = useState("")

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)

    const files = Array.from(e.dataTransfer.files)
    setUploadedFiles((prev) => [...prev, ...files])
  }, [])

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files)
      setUploadedFiles((prev) => [...prev, ...files])
    }
  }, [])

  const removeFile = useCallback((index: number) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== index))
  }, [])

  const filteredDocuments = mockDocuments.filter((doc) => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        doc.name.toLowerCase().includes(query) ||
        doc.entity.toLowerCase().includes(query) ||
        doc.id.toLowerCase().includes(query)
      )
    }
    return true
  })

  const stats = {
    total: mockDocuments.length,
    completed: mockDocuments.filter((d) => d.status === "completed").length,
    processing: mockDocuments.filter((d) => d.status === "processing").length,
    failed: mockDocuments.filter((d) => d.status === "failed").length,
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Document Processing"
        description="Upload and analyze documents using Smart Docs OCR and NLP"
      />

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary-100">
              <FileText className="h-5 w-5 text-primary-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.total}</p>
              <p className="text-sm text-neutral-500">Total Documents</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-100">
              <CheckCircle className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.completed}</p>
              <p className="text-sm text-neutral-500">Completed</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-yellow-100">
              <Clock className="h-5 w-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.processing}</p>
              <p className="text-sm text-neutral-500">Processing</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-red-100">
              <AlertCircle className="h-5 w-5 text-red-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.failed}</p>
              <p className="text-sm text-neutral-500">Failed</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Upload Zone */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Upload Documents</CardTitle>
        </CardHeader>
        <CardContent>
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={cn(
              "border-2 border-dashed rounded-xl p-8 text-center transition-colors",
              isDragOver
                ? "border-primary-400 bg-primary-50"
                : "border-neutral-300 hover:border-neutral-400"
            )}
          >
            <div className="flex flex-col items-center gap-4">
              <div
                className={cn(
                  "p-4 rounded-full",
                  isDragOver ? "bg-primary-100" : "bg-neutral-100"
                )}
              >
                <Upload
                  className={cn(
                    "h-8 w-8",
                    isDragOver ? "text-primary-600" : "text-neutral-400"
                  )}
                />
              </div>
              <div>
                <p className="text-lg font-medium text-neutral-900">
                  {isDragOver ? "Drop files here" : "Drag and drop files here"}
                </p>
                <p className="text-sm text-neutral-500 mt-1">
                  or click to browse from your computer
                </p>
              </div>
              <label>
                <input
                  type="file"
                  multiple
                  className="hidden"
                  onChange={handleFileInput}
                  accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                />
                <Button variant="outline" asChild>
                  <span>Browse Files</span>
                </Button>
              </label>
              <p className="text-xs text-neutral-400">
                Supported formats: PDF, DOC, DOCX, JPG, PNG (Max 25MB)
              </p>
            </div>
          </div>

          {/* Uploaded Files Queue */}
          {uploadedFiles.length > 0 && (
            <div className="mt-6 space-y-3">
              <h4 className="font-medium text-neutral-900">Upload Queue</h4>
              {uploadedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 rounded-lg bg-neutral-50 border"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-neutral-400" />
                    <div>
                      <p className="font-medium text-sm">{file.name}</p>
                      <p className="text-xs text-neutral-500">
                        {(file.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => removeFile(index)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              <Button className="w-full">
                <Upload className="mr-2 h-4 w-4" />
                Process {uploadedFiles.length} Document{uploadedFiles.length > 1 ? "s" : ""}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Document List */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <CardTitle className="text-lg">Recent Documents</CardTitle>
            <div className="flex gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400" />
                <Input
                  placeholder="Search documents..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 w-64"
                />
              </div>
              <Button variant="outline" size="icon">
                <Filter className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {filteredDocuments.map((doc) => {
              const typeStyle = typeConfig[doc.type]
              const statusStyle = statusConfig[doc.status]
              const StatusIcon = statusStyle.icon

              return (
                <div
                  key={doc.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-lg border hover:bg-neutral-50 transition-colors gap-4"
                >
                  <div className="flex items-start gap-4">
                    <div className="p-2 rounded-lg bg-neutral-100">
                      <FileText className="h-6 w-6 text-neutral-600" />
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-medium ${typeStyle.className}`}
                        >
                          {typeStyle.label}
                        </span>
                        <span
                          className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${statusStyle.className}`}
                        >
                          <StatusIcon className="h-3 w-3" />
                          {statusStyle.label}
                        </span>
                      </div>
                      <p className="font-medium text-neutral-900">{doc.name}</p>
                      <p className="text-sm text-neutral-500">
                        {doc.entity} ({doc.entityId})
                      </p>
                      <p className="text-xs text-neutral-400 mt-1">
                        Uploaded: {new Date(doc.uploadedAt).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 sm:gap-6">
                    {doc.status === "completed" && doc.extractedData && (
                      <div className="text-right">
                        <p className="text-sm font-medium text-neutral-900">
                          {doc.confidence}% confidence
                        </p>
                        <p className="text-xs text-neutral-500">
                          {doc.extractedData.fields} fields, {doc.extractedData.entities} entities
                        </p>
                      </div>
                    )}

                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="icon-sm">
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="icon-sm">
                        <Download className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="icon-sm">
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {filteredDocuments.length === 0 && (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-neutral-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-neutral-900 mb-2">
                No documents found
              </h3>
              <p className="text-neutral-500">
                Upload documents to get started with Smart Docs processing.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
