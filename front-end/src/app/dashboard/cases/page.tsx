"use client"

import { useState } from "react"
import {
  FolderOpen,
  Search,
  Filter,
  Plus,
  Clock,
  User,
  AlertTriangle,
  CheckCircle,
  MoreHorizontal,
  Eye,
  ArrowRight,
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

interface Case {
  id: string
  title: string
  entity: string
  entityId: string
  priority: "critical" | "high" | "medium" | "low"
  status: "open" | "in_progress" | "pending_review" | "closed"
  assignedTo: string
  createdAt: string
  updatedAt: string
  alertCount: number
}

const mockCases: Case[] = [
  {
    id: "CASE-001",
    title: "Suspicious Transaction Pattern Investigation",
    entity: "Acme Corporation Ltd",
    entityId: "ENT-4521",
    priority: "critical",
    status: "in_progress",
    assignedTo: "John Smith",
    createdAt: "2024-01-10T08:00:00Z",
    updatedAt: "2024-01-15T14:30:00Z",
    alertCount: 5,
  },
  {
    id: "CASE-002",
    title: "PEP Exposure Assessment",
    entity: "Global Trading Inc",
    entityId: "ENT-3892",
    priority: "high",
    status: "pending_review",
    assignedTo: "Sarah Johnson",
    createdAt: "2024-01-08T10:00:00Z",
    updatedAt: "2024-01-14T16:00:00Z",
    alertCount: 3,
  },
  {
    id: "CASE-003",
    title: "Geographic Risk Review",
    entity: "Oceanic Exports LLC",
    entityId: "ENT-2741",
    priority: "high",
    status: "open",
    assignedTo: "Mike Brown",
    createdAt: "2024-01-12T09:00:00Z",
    updatedAt: "2024-01-12T09:00:00Z",
    alertCount: 8,
  },
  {
    id: "CASE-004",
    title: "Document Verification Follow-up",
    entity: "Tech Solutions Corp",
    entityId: "ENT-1983",
    priority: "medium",
    status: "in_progress",
    assignedTo: "John Smith",
    createdAt: "2024-01-05T11:00:00Z",
    updatedAt: "2024-01-13T10:00:00Z",
    alertCount: 2,
  },
  {
    id: "CASE-005",
    title: "Threshold Breach Analysis",
    entity: "Eastern Commerce Ltd",
    entityId: "ENT-5123",
    priority: "low",
    status: "closed",
    assignedTo: "Sarah Johnson",
    createdAt: "2024-01-02T14:00:00Z",
    updatedAt: "2024-01-10T12:00:00Z",
    alertCount: 1,
  },
]

const priorityConfig = {
  critical: { label: "Critical", variant: "critical" as const, color: "bg-red-500" },
  high: { label: "High", variant: "high" as const, color: "bg-orange-500" },
  medium: { label: "Medium", variant: "medium" as const, color: "bg-yellow-500" },
  low: { label: "Low", variant: "low" as const, color: "bg-green-500" },
}

const statusConfig = {
  open: { label: "Open", className: "bg-blue-100 text-blue-700" },
  in_progress: { label: "In Progress", className: "bg-yellow-100 text-yellow-700" },
  pending_review: { label: "Pending Review", className: "bg-purple-100 text-purple-700" },
  closed: { label: "Closed", className: "bg-green-100 text-green-700" },
}

export default function CasesPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [filter, setFilter] = useState<string>("all")

  const filteredCases = mockCases.filter((c) => {
    if (filter !== "all" && c.status !== filter) return false
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        c.title.toLowerCase().includes(query) ||
        c.entity.toLowerCase().includes(query) ||
        c.id.toLowerCase().includes(query)
      )
    }
    return true
  })

  const stats = {
    total: mockCases.length,
    open: mockCases.filter((c) => c.status === "open").length,
    inProgress: mockCases.filter((c) => c.status === "in_progress").length,
    pendingReview: mockCases.filter((c) => c.status === "pending_review").length,
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Case Management"
        description="Manage and track compliance investigation cases"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Case
          </Button>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-2xl font-bold text-neutral-900">{stats.total}</div>
          <div className="text-sm text-neutral-500">Total Cases</div>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-blue-600">{stats.open}</div>
          <div className="text-sm text-neutral-500">Open</div>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-yellow-600">{stats.inProgress}</div>
          <div className="text-sm text-neutral-500">In Progress</div>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-purple-600">{stats.pendingReview}</div>
          <div className="text-sm text-neutral-500">Pending Review</div>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        {[
          { key: "all", label: "All Cases" },
          { key: "open", label: "Open" },
          { key: "in_progress", label: "In Progress" },
          { key: "pending_review", label: "Pending Review" },
          { key: "closed", label: "Closed" },
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
            placeholder="Search cases..."
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

      {/* Case List */}
      <div className="space-y-4">
        {filteredCases.map((caseItem) => {
          const priority = priorityConfig[caseItem.priority]
          const status = statusConfig[caseItem.status]

          return (
            <Card key={caseItem.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  <div className="flex items-start gap-4">
                    <div className={`w-1 h-16 rounded-full ${priority.color}`} />
                    <div>
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <Badge variant={priority.variant}>{priority.label}</Badge>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${status.className}`}>
                          {status.label}
                        </span>
                        <span className="text-xs text-neutral-500">{caseItem.id}</span>
                      </div>
                      <h3 className="font-semibold text-neutral-900 mb-1">
                        {caseItem.title}
                      </h3>
                      <p className="text-sm text-neutral-600">
                        {caseItem.entity} ({caseItem.entityId})
                      </p>
                      <div className="flex flex-wrap items-center gap-4 mt-2 text-sm text-neutral-500">
                        <span className="flex items-center gap-1">
                          <User className="h-3.5 w-3.5" />
                          {caseItem.assignedTo}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5" />
                          Updated {new Date(caseItem.updatedAt).toLocaleDateString()}
                        </span>
                        <span className="flex items-center gap-1">
                          <AlertTriangle className="h-3.5 w-3.5" />
                          {caseItem.alertCount} alerts
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm">
                      <Eye className="mr-1 h-4 w-4" />
                      View
                    </Button>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="outline" size="icon-sm">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>Edit Case</DropdownMenuItem>
                        <DropdownMenuItem>Assign to...</DropdownMenuItem>
                        <DropdownMenuItem>
                          <CheckCircle className="mr-2 h-4 w-4" />
                          Mark as Resolved
                        </DropdownMenuItem>
                        <DropdownMenuItem className="text-red-600">Close Case</DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {filteredCases.length === 0 && (
        <div className="text-center py-12">
          <FolderOpen className="h-12 w-12 text-neutral-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-neutral-900 mb-2">No cases found</h3>
          <p className="text-neutral-500">
            No cases match your current filters.
          </p>
        </div>
      )}
    </div>
  )
}
