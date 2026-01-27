"use client"

import { useState } from "react"
import {
  FileText,
  Search,
  Filter,
  Plus,
  Download,
  Eye,
  MoreHorizontal,
  Calendar,
  CheckCircle,
  Clock,
  AlertCircle,
} from "lucide-react"
import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

interface Report {
  id: string
  title: string
  type: "sar" | "risk_memo" | "audit" | "periodic"
  entity?: string
  status: "draft" | "pending_review" | "approved" | "submitted"
  createdBy: string
  createdAt: string
  submittedAt?: string
}

const mockReports: Report[] = [
  {
    id: "RPT-001",
    title: "Suspicious Activity Report - Acme Corp",
    type: "sar",
    entity: "Acme Corporation Ltd",
    status: "pending_review",
    createdBy: "John Smith",
    createdAt: "2024-01-15T10:00:00Z",
  },
  {
    id: "RPT-002",
    title: "Monthly Risk Assessment - December 2023",
    type: "periodic",
    status: "approved",
    createdBy: "Sarah Johnson",
    createdAt: "2024-01-02T14:00:00Z",
    submittedAt: "2024-01-05T09:00:00Z",
  },
  {
    id: "RPT-003",
    title: "Risk Memo - Global Trading PEP Exposure",
    type: "risk_memo",
    entity: "Global Trading Inc",
    status: "draft",
    createdBy: "Mike Brown",
    createdAt: "2024-01-14T11:00:00Z",
  },
  {
    id: "RPT-004",
    title: "Q4 2023 Compliance Audit Report",
    type: "audit",
    status: "submitted",
    createdBy: "Sarah Johnson",
    createdAt: "2024-01-08T09:00:00Z",
    submittedAt: "2024-01-12T16:00:00Z",
  },
  {
    id: "RPT-005",
    title: "SAR - Oceanic Exports Transaction Pattern",
    type: "sar",
    entity: "Oceanic Exports LLC",
    status: "pending_review",
    createdBy: "John Smith",
    createdAt: "2024-01-13T15:00:00Z",
  },
]

const typeConfig = {
  sar: { label: "SAR", className: "bg-red-100 text-red-700" },
  risk_memo: { label: "Risk Memo", className: "bg-orange-100 text-orange-700" },
  audit: { label: "Audit", className: "bg-purple-100 text-purple-700" },
  periodic: { label: "Periodic", className: "bg-blue-100 text-blue-700" },
}

const statusConfig = {
  draft: { label: "Draft", icon: FileText, className: "bg-neutral-100 text-neutral-700" },
  pending_review: { label: "Pending Review", icon: Clock, className: "bg-yellow-100 text-yellow-700" },
  approved: { label: "Approved", icon: CheckCircle, className: "bg-green-100 text-green-700" },
  submitted: { label: "Submitted", icon: CheckCircle, className: "bg-teal-100 text-teal-700" },
}

export default function ReportsPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [filter, setFilter] = useState<string>("all")

  const filteredReports = mockReports.filter((report) => {
    if (filter !== "all" && report.type !== filter) return false
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        report.title.toLowerCase().includes(query) ||
        report.id.toLowerCase().includes(query) ||
        (report.entity && report.entity.toLowerCase().includes(query))
      )
    }
    return true
  })

  return (
    <div className="space-y-6">
      <PageHeader
        title="Report Management"
        description="Create and manage compliance reports"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Report
          </Button>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-2xl font-bold text-neutral-900">{mockReports.length}</div>
          <div className="text-sm text-neutral-500">Total Reports</div>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-yellow-600">
            {mockReports.filter((r) => r.status === "pending_review").length}
          </div>
          <div className="text-sm text-neutral-500">Pending Review</div>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-red-600">
            {mockReports.filter((r) => r.type === "sar").length}
          </div>
          <div className="text-sm text-neutral-500">SARs</div>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-teal-600">
            {mockReports.filter((r) => r.status === "submitted").length}
          </div>
          <div className="text-sm text-neutral-500">Submitted</div>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        {[
          { key: "all", label: "All Reports" },
          { key: "sar", label: "SARs" },
          { key: "risk_memo", label: "Risk Memos" },
          { key: "audit", label: "Audits" },
          { key: "periodic", label: "Periodic" },
        ].map((tab) => (
          <Button
            key={tab.key}
            variant={filter === tab.key ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(tab.key)}
          >
            {tab.label}
          </Button>
        ))}
      </div>

      {/* Search */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400" />
          <Input
            placeholder="Search reports..."
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

      {/* Report List */}
      <div className="space-y-4">
        {filteredReports.map((report) => {
          const type = typeConfig[report.type]
          const status = statusConfig[report.status]
          const StatusIcon = status.icon

          return (
            <Card key={report.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  <div className="flex items-start gap-4">
                    <div className="p-3 rounded-lg bg-neutral-100">
                      <FileText className="h-6 w-6 text-neutral-600" />
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${type.className}`}>
                          {type.label}
                        </span>
                        <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${status.className}`}>
                          <StatusIcon className="h-3 w-3" />
                          {status.label}
                        </span>
                        <span className="text-xs text-neutral-500">{report.id}</span>
                      </div>
                      <h3 className="font-semibold text-neutral-900 mb-1">
                        {report.title}
                      </h3>
                      {report.entity && (
                        <p className="text-sm text-neutral-600 mb-1">
                          Entity: {report.entity}
                        </p>
                      )}
                      <div className="flex flex-wrap items-center gap-4 text-sm text-neutral-500">
                        <span>Created by: {report.createdBy}</span>
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3.5 w-3.5" />
                          {new Date(report.createdAt).toLocaleDateString()}
                        </span>
                        {report.submittedAt && (
                          <span className="text-teal-600">
                            Submitted: {new Date(report.submittedAt).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm">
                      <Eye className="mr-1 h-4 w-4" />
                      View
                    </Button>
                    <Button variant="outline" size="sm">
                      <Download className="mr-1 h-4 w-4" />
                      Download
                    </Button>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="outline" size="icon-sm">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>Edit Report</DropdownMenuItem>
                        <DropdownMenuItem>Duplicate</DropdownMenuItem>
                        <DropdownMenuItem>Submit for Review</DropdownMenuItem>
                        <DropdownMenuItem className="text-red-600">Delete</DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {filteredReports.length === 0 && (
        <div className="text-center py-12">
          <FileText className="h-12 w-12 text-neutral-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-neutral-900 mb-2">No reports found</h3>
          <p className="text-neutral-500">
            No reports match your current filters.
          </p>
        </div>
      )}
    </div>
  )
}
