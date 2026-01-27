"use client"

import { Clock, FileText, Loader2, RefreshCw, Eye, XCircle } from "lucide-react"
import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"

interface ProcessingDocument {
  id: string
  name: string
  type: string
  entity?: string
  status: "queued" | "processing" | "extracting" | "analyzing"
  progress: number
  startedAt: string
  estimatedCompletion?: string
}

const processingDocs: ProcessingDocument[] = [
  {
    id: "DOC-101",
    name: "KYC_GlobalTrading_2024.pdf",
    type: "KYC",
    entity: "Global Trading Inc",
    status: "analyzing",
    progress: 85,
    startedAt: "2024-01-15T10:30:00Z",
    estimatedCompletion: "2 min",
  },
  {
    id: "DOC-102",
    name: "Invoice_Batch_Q4.pdf",
    type: "Invoice",
    status: "extracting",
    progress: 60,
    startedAt: "2024-01-15T10:28:00Z",
    estimatedCompletion: "5 min",
  },
  {
    id: "DOC-103",
    name: "Contract_Amendment_2024.docx",
    type: "Contract",
    entity: "Tech Solutions Corp",
    status: "processing",
    progress: 35,
    startedAt: "2024-01-15T10:25:00Z",
    estimatedCompletion: "8 min",
  },
  {
    id: "DOC-104",
    name: "Bank_Statement_Dec.pdf",
    type: "Financial",
    status: "queued",
    progress: 0,
    startedAt: "2024-01-15T10:32:00Z",
  },
  {
    id: "DOC-105",
    name: "ID_Verification_Scan.jpg",
    type: "KYC",
    entity: "Eastern Commerce Ltd",
    status: "queued",
    progress: 0,
    startedAt: "2024-01-15T10:33:00Z",
  },
]

const statusConfig = {
  queued: { label: "Queued", color: "text-neutral-500", bgColor: "bg-neutral-100" },
  processing: { label: "Processing", color: "text-blue-600", bgColor: "bg-blue-100" },
  extracting: { label: "Extracting", color: "text-purple-600", bgColor: "bg-purple-100" },
  analyzing: { label: "Analyzing", color: "text-green-600", bgColor: "bg-green-100" },
}

export default function ProcessingPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Processing Queue"
        description="Documents currently being processed by Smart Docs"
        actions={
          <Button variant="outline">
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-100">
              <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
            </div>
            <div>
              <p className="text-2xl font-bold">{processingDocs.length}</p>
              <p className="text-sm text-neutral-500">In Queue</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-100">
              <Clock className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">3</p>
              <p className="text-sm text-neutral-500">Active</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-neutral-100">
              <FileText className="h-5 w-5 text-neutral-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">2</p>
              <p className="text-sm text-neutral-500">Waiting</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-100">
              <Clock className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">~15 min</p>
              <p className="text-sm text-neutral-500">Est. Total</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Processing Queue */}
      <div className="space-y-4">
        {processingDocs.map((doc) => {
          const status = statusConfig[doc.status]
          const isActive = doc.status !== "queued"

          return (
            <Card key={doc.id}>
              <CardContent className="p-6">
                <div className="flex flex-col lg:flex-row lg:items-center gap-4">
                  <div className="flex items-start gap-4 flex-1">
                    <div className={`p-3 rounded-lg ${status.bgColor}`}>
                      {isActive ? (
                        <Loader2 className={`h-6 w-6 ${status.color} animate-spin`} />
                      ) : (
                        <Clock className={`h-6 w-6 ${status.color}`} />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${status.bgColor} ${status.color}`}>
                          {status.label}
                        </span>
                        <span className="text-xs text-neutral-500">{doc.id}</span>
                      </div>
                      <h3 className="font-medium text-neutral-900 truncate">
                        {doc.name}
                      </h3>
                      <div className="flex items-center gap-4 text-sm text-neutral-500 mt-1">
                        <span>{doc.type}</span>
                        {doc.entity && (
                          <>
                            <span className="text-neutral-300">|</span>
                            <span>{doc.entity}</span>
                          </>
                        )}
                      </div>

                      {isActive && (
                        <div className="mt-3">
                          <div className="flex items-center justify-between text-sm mb-1">
                            <span className="text-neutral-500">Progress</span>
                            <span className="font-medium">{doc.progress}%</span>
                          </div>
                          <Progress value={doc.progress} className="h-2" />
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    {doc.estimatedCompletion && (
                      <div className="text-right">
                        <p className="text-sm font-medium text-neutral-900">
                          ~{doc.estimatedCompletion}
                        </p>
                        <p className="text-xs text-neutral-500">remaining</p>
                      </div>
                    )}
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="icon-sm" disabled={!isActive}>
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="icon-sm">
                        <XCircle className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {processingDocs.length === 0 && (
        <div className="text-center py-12">
          <FileText className="h-12 w-12 text-neutral-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-neutral-900 mb-2">
            No documents processing
          </h3>
          <p className="text-neutral-500">
            Upload documents to start processing.
          </p>
        </div>
      )}
    </div>
  )
}
