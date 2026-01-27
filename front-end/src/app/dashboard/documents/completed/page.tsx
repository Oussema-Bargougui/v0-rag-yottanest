"use client"

import { useState } from "react"
import {
  CheckCircle,
  FileText,
  Search,
  Filter,
  Download,
  Eye,
  Trash2,
  Calendar,
} from "lucide-react"
import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"

interface CompletedDocument {
  id: string
  name: string
  type: string
  entity?: string
  processedAt: string
  confidence: number
  extractedFields: number
  extractedEntities: number
  fileSize: string
}

const completedDocs: CompletedDocument[] = [
  {
    id: "DOC-001",
    name: "KYC_Acme_Corp_2024.pdf",
    type: "KYC",
    entity: "Acme Corporation Ltd",
    processedAt: "2024-01-15T08:30:00Z",
    confidence: 94,
    extractedFields: 28,
    extractedEntities: 5,
    fileSize: "2.4 MB",
  },
  {
    id: "DOC-002",
    name: "Contract_TechSolutions.docx",
    type: "Contract",
    entity: "Tech Solutions Corp",
    processedAt: "2024-01-14T16:25:00Z",
    confidence: 87,
    extractedFields: 45,
    extractedEntities: 8,
    fileSize: "1.8 MB",
  },
  {
    id: "DOC-003",
    name: "Invoice_GlobalTrading_Dec.pdf",
    type: "Invoice",
    entity: "Global Trading Inc",
    processedAt: "2024-01-14T14:00:00Z",
    confidence: 92,
    extractedFields: 18,
    extractedEntities: 3,
    fileSize: "0.8 MB",
  },
  {
    id: "DOC-004",
    name: "Bank_Statement_Nov.pdf",
    type: "Financial",
    entity: "Pacific Ventures LLC",
    processedAt: "2024-01-13T11:00:00Z",
    confidence: 89,
    extractedFields: 52,
    extractedEntities: 12,
    fileSize: "3.2 MB",
  },
  {
    id: "DOC-005",
    name: "ID_Passport_Scan.jpg",
    type: "KYC",
    entity: "Northern Industries Co",
    processedAt: "2024-01-12T09:30:00Z",
    confidence: 96,
    extractedFields: 12,
    extractedEntities: 1,
    fileSize: "1.1 MB",
  },
  {
    id: "DOC-006",
    name: "Incorporation_Certificate.pdf",
    type: "Certificate",
    entity: "Metro Holdings Inc",
    processedAt: "2024-01-11T15:00:00Z",
    confidence: 98,
    extractedFields: 8,
    extractedEntities: 2,
    fileSize: "0.5 MB",
  },
]

const typeConfig: Record<string, { className: string }> = {
  KYC: { className: "bg-blue-100 text-blue-700" },
  Contract: { className: "bg-purple-100 text-purple-700" },
  Invoice: { className: "bg-green-100 text-green-700" },
  Financial: { className: "bg-orange-100 text-orange-700" },
  Certificate: { className: "bg-teal-100 text-teal-700" },
}

export default function CompletedDocumentsPage() {
  const [searchQuery, setSearchQuery] = useState("")

  const filteredDocs = completedDocs.filter((doc) => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        doc.name.toLowerCase().includes(query) ||
        doc.id.toLowerCase().includes(query) ||
        (doc.entity && doc.entity.toLowerCase().includes(query))
      )
    }
    return true
  })

  return (
    <div className="space-y-6">
      <PageHeader
        title="Completed Documents"
        description="Documents that have been successfully processed"
        actions={
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export All
          </Button>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-100">
              <CheckCircle className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{completedDocs.length}</p>
              <p className="text-sm text-neutral-500">Total Processed</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-100">
              <FileText className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">92%</p>
              <p className="text-sm text-neutral-500">Avg. Confidence</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-100">
              <FileText className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">163</p>
              <p className="text-sm text-neutral-500">Fields Extracted</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-orange-100">
              <FileText className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">31</p>
              <p className="text-sm text-neutral-500">Entities Found</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Search */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400" />
          <Input
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button variant="outline">
          <Filter className="mr-2 h-4 w-4" />
          Filters
        </Button>
      </div>

      {/* Document List */}
      <div className="space-y-4">
        {filteredDocs.map((doc) => {
          const typeStyle = typeConfig[doc.type] || { className: "bg-neutral-100 text-neutral-700" }

          return (
            <Card key={doc.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  <div className="flex items-start gap-4">
                    <div className="p-3 rounded-lg bg-green-100">
                      <CheckCircle className="h-6 w-6 text-green-600" />
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${typeStyle.className}`}>
                          {doc.type}
                        </span>
                        <span className="text-xs text-neutral-500">{doc.id}</span>
                      </div>
                      <h3 className="font-medium text-neutral-900">{doc.name}</h3>
                      {doc.entity && (
                        <p className="text-sm text-neutral-600">{doc.entity}</p>
                      )}
                      <div className="flex flex-wrap items-center gap-4 text-sm text-neutral-500 mt-2">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3.5 w-3.5" />
                          {new Date(doc.processedAt).toLocaleString()}
                        </span>
                        <span>{doc.fileSize}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="text-center">
                      <Badge
                        variant={doc.confidence >= 90 ? "success" : doc.confidence >= 80 ? "warning" : "secondary"}
                      >
                        {doc.confidence}%
                      </Badge>
                      <p className="text-xs text-neutral-500 mt-1">Confidence</p>
                    </div>
                    <div className="text-center">
                      <p className="font-bold text-neutral-900">{doc.extractedFields}</p>
                      <p className="text-xs text-neutral-500">Fields</p>
                    </div>
                    <div className="text-center">
                      <p className="font-bold text-neutral-900">{doc.extractedEntities}</p>
                      <p className="text-xs text-neutral-500">Entities</p>
                    </div>
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
              </CardContent>
            </Card>
          )
        })}
      </div>

      {filteredDocs.length === 0 && (
        <div className="text-center py-12">
          <FileText className="h-12 w-12 text-neutral-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-neutral-900 mb-2">
            No documents found
          </h3>
          <p className="text-neutral-500">
            No completed documents match your search.
          </p>
        </div>
      )}
    </div>
  )
}
