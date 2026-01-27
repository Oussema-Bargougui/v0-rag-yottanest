"use client"

import { useState } from "react"
import Link from "next/link"
import {
  Building2,
  Search,
  Filter,
  Plus,
  Eye,
  MoreHorizontal,
  MapPin,
  Calendar,
  TrendingUp,
  AlertTriangle,
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
import { getRiskLabel } from "@/lib/utils"

interface Entity {
  id: string
  name: string
  type: "corporation" | "llc" | "partnership" | "individual"
  country: string
  industry: string
  riskScore: number
  status: "active" | "under_review" | "suspended" | "cleared"
  lastReview: string
  alertCount: number
  transactionVolume: number
}

const mockEntities: Entity[] = [
  {
    id: "ENT-4521",
    name: "Acme Corporation Ltd",
    type: "corporation",
    country: "United States",
    industry: "Financial Services",
    riskScore: 94,
    status: "under_review",
    lastReview: "2024-01-10",
    alertCount: 5,
    transactionVolume: 2450000,
  },
  {
    id: "ENT-3892",
    name: "Global Trading Inc",
    type: "corporation",
    country: "United Kingdom",
    industry: "Import/Export",
    riskScore: 78,
    status: "under_review",
    lastReview: "2024-01-08",
    alertCount: 3,
    transactionVolume: 1890000,
  },
  {
    id: "ENT-2741",
    name: "Oceanic Exports LLC",
    type: "llc",
    country: "Panama",
    industry: "Shipping",
    riskScore: 85,
    status: "suspended",
    lastReview: "2024-01-05",
    alertCount: 8,
    transactionVolume: 4200000,
  },
  {
    id: "ENT-1983",
    name: "Tech Solutions Corp",
    type: "corporation",
    country: "Germany",
    industry: "Technology",
    riskScore: 45,
    status: "active",
    lastReview: "2024-01-12",
    alertCount: 1,
    transactionVolume: 980000,
  },
  {
    id: "ENT-5123",
    name: "Eastern Commerce Ltd",
    type: "corporation",
    country: "Singapore",
    industry: "E-Commerce",
    riskScore: 52,
    status: "active",
    lastReview: "2024-01-11",
    alertCount: 2,
    transactionVolume: 1250000,
  },
  {
    id: "ENT-6721",
    name: "Northern Industries Co",
    type: "corporation",
    country: "Canada",
    industry: "Manufacturing",
    riskScore: 18,
    status: "cleared",
    lastReview: "2024-01-14",
    alertCount: 0,
    transactionVolume: 750000,
  },
  {
    id: "ENT-7892",
    name: "Pacific Ventures LLC",
    type: "llc",
    country: "Australia",
    industry: "Investment",
    riskScore: 35,
    status: "active",
    lastReview: "2024-01-09",
    alertCount: 1,
    transactionVolume: 3100000,
  },
  {
    id: "ENT-8234",
    name: "Metro Holdings Inc",
    type: "corporation",
    country: "United States",
    industry: "Real Estate",
    riskScore: 22,
    status: "cleared",
    lastReview: "2024-01-13",
    alertCount: 0,
    transactionVolume: 5600000,
  },
]

const getRiskBadgeVariant = (score: number) => {
  if (score >= 90) return "critical"
  if (score >= 70) return "high"
  if (score >= 40) return "medium"
  if (score >= 20) return "low"
  return "clear"
}

const statusConfig = {
  active: { label: "Active", className: "bg-green-100 text-green-700" },
  under_review: { label: "Under Review", className: "bg-yellow-100 text-yellow-700" },
  suspended: { label: "Suspended", className: "bg-red-100 text-red-700" },
  cleared: { label: "Cleared", className: "bg-teal-100 text-teal-700" },
}

const formatCurrency = (amount: number) => {
  if (amount >= 1000000) return `$${(amount / 1000000).toFixed(1)}M`
  if (amount >= 1000) return `$${(amount / 1000).toFixed(0)}K`
  return `$${amount}`
}

export default function EntitiesPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [filter, setFilter] = useState<string>("all")

  const filteredEntities = mockEntities.filter((entity) => {
    // Filter by risk level
    if (filter !== "all") {
      const riskLabel = getRiskLabel(entity.riskScore).toLowerCase()
      if (filter !== riskLabel) return false
    }
    // Filter by search
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        entity.name.toLowerCase().includes(query) ||
        entity.id.toLowerCase().includes(query) ||
        entity.country.toLowerCase().includes(query)
      )
    }
    return true
  })

  return (
    <div className="space-y-6">
      <PageHeader
        title="Entity Management"
        description="Monitor and manage all registered entities in the compliance system"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Entity
          </Button>
        }
      />

      {/* Stats Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-2xl font-bold text-neutral-900">{mockEntities.length}</div>
          <div className="text-sm text-neutral-500">Total Entities</div>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-red-600">
            {mockEntities.filter((e) => e.riskScore >= 70).length}
          </div>
          <div className="text-sm text-neutral-500">High Risk</div>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-yellow-600">
            {mockEntities.filter((e) => e.status === "under_review").length}
          </div>
          <div className="text-sm text-neutral-500">Under Review</div>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-teal-600">
            {mockEntities.filter((e) => e.status === "cleared").length}
          </div>
          <div className="text-sm text-neutral-500">Cleared</div>
        </Card>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2">
        {["all", "critical", "high", "medium", "low", "clear"].map((level) => (
          <Button
            key={level}
            variant={filter === level ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(level)}
            className="capitalize"
          >
            {level === "all" ? "All Entities" : level}
          </Button>
        ))}
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400" />
          <Input
            placeholder="Search entities..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button variant="outline">
          <Filter className="mr-2 h-4 w-4" />
          More Filters
        </Button>
      </div>

      {/* Entity Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filteredEntities.map((entity) => {
          const status = statusConfig[entity.status]
          return (
            <Card key={entity.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-lg bg-primary-100 flex items-center justify-center">
                      <Building2 className="h-6 w-6 text-primary-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-neutral-900">{entity.name}</h3>
                      <p className="text-sm text-neutral-500">{entity.id}</p>
                    </div>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon-sm">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem>
                        <Eye className="mr-2 h-4 w-4" />
                        View Details
                      </DropdownMenuItem>
                      <DropdownMenuItem>Edit Entity</DropdownMenuItem>
                      <DropdownMenuItem>Generate Report</DropdownMenuItem>
                      <DropdownMenuItem className="text-red-600">Suspend</DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>

                <div className="flex flex-wrap items-center gap-2 mb-4">
                  <Badge variant={getRiskBadgeVariant(entity.riskScore)}>
                    Risk: {entity.riskScore}
                  </Badge>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${status.className}`}>
                    {status.label}
                  </span>
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2 text-neutral-600">
                    <MapPin className="h-4 w-4 text-neutral-400" />
                    <span>{entity.country}</span>
                    <span className="text-neutral-300">|</span>
                    <span>{entity.industry}</span>
                  </div>
                  <div className="flex items-center gap-2 text-neutral-600">
                    <Calendar className="h-4 w-4 text-neutral-400" />
                    <span>Last Review: {new Date(entity.lastReview).toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center gap-2 text-neutral-600">
                    <TrendingUp className="h-4 w-4 text-neutral-400" />
                    <span>Volume: {formatCurrency(entity.transactionVolume)}</span>
                  </div>
                  {entity.alertCount > 0 && (
                    <div className="flex items-center gap-2 text-red-600">
                      <AlertTriangle className="h-4 w-4" />
                      <span>{entity.alertCount} Active Alert{entity.alertCount > 1 ? "s" : ""}</span>
                    </div>
                  )}
                </div>

                <div className="mt-4 pt-4 border-t">
                  <Link href={`/dashboard/entities/${entity.id}`}>
                    <Button variant="outline" className="w-full">
                      <Eye className="mr-2 h-4 w-4" />
                      View Details
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {filteredEntities.length === 0 && (
        <div className="text-center py-12">
          <Building2 className="h-12 w-12 text-neutral-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-neutral-900 mb-2">No entities found</h3>
          <p className="text-neutral-500">
            No entities match your current filters. Try adjusting your search criteria.
          </p>
        </div>
      )}
    </div>
  )
}
