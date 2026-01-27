"use client"

import { useParams } from "next/navigation"
import Link from "next/link"
import dynamic from "next/dynamic"
import {
  Building2,
  ArrowLeft,
  MapPin,
  Calendar,
  AlertTriangle,
  FileText,
  TrendingUp,
  Clock,
  User,
  ExternalLink,
  Download,
} from "lucide-react"
import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

// Dynamic imports for recharts to avoid SSR issues
const ResponsiveContainer = dynamic(() => import("recharts").then((mod) => mod.ResponsiveContainer), { ssr: false })
const BarChart = dynamic(() => import("recharts").then((mod) => mod.BarChart), { ssr: false })
const Bar = dynamic(() => import("recharts").then((mod) => mod.Bar), { ssr: false })
const XAxis = dynamic(() => import("recharts").then((mod) => mod.XAxis), { ssr: false })
const YAxis = dynamic(() => import("recharts").then((mod) => mod.YAxis), { ssr: false })
const CartesianGrid = dynamic(() => import("recharts").then((mod) => mod.CartesianGrid), { ssr: false })
const Tooltip = dynamic(() => import("recharts").then((mod) => mod.Tooltip), { ssr: false })

// Mock entity data
const entityData = {
  id: "ENT-4521",
  name: "Acme Corporation Ltd",
  type: "Corporation",
  country: "United States",
  industry: "Financial Services",
  riskScore: 94,
  status: "under_review",
  registrationNumber: "US-12345678",
  incorporationDate: "2015-03-15",
  lastReview: "2024-01-10",
  nextReview: "2024-04-10",
  beneficialOwners: [
    { name: "John Doe", ownership: 45, isPEP: false },
    { name: "Jane Smith", ownership: 30, isPEP: true },
    { name: "Bob Johnson", ownership: 25, isPEP: false },
  ],
  riskFactors: [
    { factor: "Geographic Risk", score: 85, details: "Operations in high-risk jurisdictions" },
    { factor: "Transaction Pattern", score: 92, details: "Unusual transaction frequency detected" },
    { factor: "PEP Exposure", score: 78, details: "Beneficial owner is a PEP" },
    { factor: "Industry Risk", score: 65, details: "Financial services sector" },
  ],
  recentAlerts: [
    { id: "ALT-001", title: "Suspicious Transaction Pattern", severity: "critical", date: "2024-01-15" },
    { id: "ALT-008", title: "PEP Association Detected", severity: "high", date: "2024-01-12" },
    { id: "ALT-015", title: "Threshold Breach", severity: "medium", date: "2024-01-10" },
  ],
  transactionsByMonth: [
    { month: "Aug", amount: 180000 },
    { month: "Sep", amount: 220000 },
    { month: "Oct", amount: 195000 },
    { month: "Nov", amount: 350000 },
    { month: "Dec", amount: 420000 },
    { month: "Jan", amount: 285000 },
  ],
}

const riskColors = {
  critical: "#DC2626",
  high: "#EA580C",
  medium: "#CA8A04",
  low: "#16A34A",
}

export default function EntityDetailPage() {
  const params = useParams()
  const entityId = params.id

  return (
    <div className="space-y-6">
      {/* Back button */}
      <Link href="/dashboard/entities">
        <Button variant="ghost" className="gap-2 -ml-2">
          <ArrowLeft className="h-4 w-4" />
          Back to Entities
        </Button>
      </Link>

      <PageHeader
        title={entityData.name}
        description={`Entity ID: ${entityId}`}
        actions={
          <>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export Report
            </Button>
            <Button>
              <FileText className="mr-2 h-4 w-4" />
              Generate SAR
            </Button>
          </>
        }
      />

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-red-50 to-white border-red-100">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-neutral-500">Risk Score</p>
                <p className="text-3xl font-bold text-red-600">{entityData.riskScore}</p>
                <p className="text-sm text-red-600">Critical Risk</p>
              </div>
              <AlertTriangle className="h-10 w-10 text-red-200" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-neutral-500">Status</p>
                <p className="text-lg font-semibold text-yellow-600">Under Review</p>
                <p className="text-sm text-neutral-500">Since Jan 10, 2024</p>
              </div>
              <Clock className="h-10 w-10 text-neutral-200" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-neutral-500">Active Alerts</p>
                <p className="text-3xl font-bold text-neutral-900">5</p>
                <p className="text-sm text-red-600">2 Critical</p>
              </div>
              <AlertTriangle className="h-10 w-10 text-neutral-200" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-neutral-500">Next Review</p>
                <p className="text-lg font-semibold text-neutral-900">Apr 10, 2024</p>
                <p className="text-sm text-neutral-500">In 85 days</p>
              </div>
              <Calendar className="h-10 w-10 text-neutral-200" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Entity Details */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Entity Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3">
              <Building2 className="h-5 w-5 text-neutral-400" />
              <div>
                <p className="text-sm text-neutral-500">Entity Type</p>
                <p className="font-medium">{entityData.type}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <MapPin className="h-5 w-5 text-neutral-400" />
              <div>
                <p className="text-sm text-neutral-500">Country</p>
                <p className="font-medium">{entityData.country}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <TrendingUp className="h-5 w-5 text-neutral-400" />
              <div>
                <p className="text-sm text-neutral-500">Industry</p>
                <p className="font-medium">{entityData.industry}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <FileText className="h-5 w-5 text-neutral-400" />
              <div>
                <p className="text-sm text-neutral-500">Registration Number</p>
                <p className="font-medium">{entityData.registrationNumber}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Calendar className="h-5 w-5 text-neutral-400" />
              <div>
                <p className="text-sm text-neutral-500">Incorporation Date</p>
                <p className="font-medium">{new Date(entityData.incorporationDate).toLocaleDateString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Risk Factors */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Risk Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {entityData.riskFactors.map((factor, idx) => (
                <div key={idx}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">{factor.factor}</span>
                    <span className="text-sm font-bold">{factor.score}</span>
                  </div>
                  <div className="w-full h-2 bg-neutral-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${factor.score}%`,
                        backgroundColor:
                          factor.score >= 90
                            ? riskColors.critical
                            : factor.score >= 70
                            ? riskColors.high
                            : factor.score >= 40
                            ? riskColors.medium
                            : riskColors.low,
                      }}
                    />
                  </div>
                  <p className="text-xs text-neutral-500 mt-1">{factor.details}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Beneficial Owners */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Beneficial Owners</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {entityData.beneficialOwners.map((owner, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 rounded-lg bg-neutral-50"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
                      <User className="h-5 w-5 text-primary-600" />
                    </div>
                    <div>
                      <p className="font-medium">{owner.name}</p>
                      <p className="text-sm text-neutral-500">{owner.ownership}% ownership</p>
                    </div>
                  </div>
                  {owner.isPEP && (
                    <Badge variant="warning">PEP</Badge>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Transaction Volume Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Transaction Volume (6 Months)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={entityData.transactionsByMonth}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis dataKey="month" tick={{ fontSize: 12, fill: "#6B7280" }} />
                  <YAxis
                    tick={{ fontSize: 12, fill: "#6B7280" }}
                    tickFormatter={(value) => `$${value / 1000}K`}
                  />
                  <Tooltip
                    formatter={(value) => [`$${Number(value).toLocaleString()}`, "Amount"]}
                    contentStyle={{
                      backgroundColor: "white",
                      border: "1px solid #E5E7EB",
                      borderRadius: "8px",
                    }}
                  />
                  <Bar dataKey="amount" fill="#2C5282" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Recent Alerts */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {entityData.recentAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`p-4 rounded-lg border ${
                    alert.severity === "critical"
                      ? "bg-red-50 border-red-100"
                      : alert.severity === "high"
                      ? "bg-orange-50 border-orange-100"
                      : "bg-yellow-50 border-yellow-100"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <Badge
                          variant={
                            alert.severity === "critical"
                              ? "critical"
                              : alert.severity === "high"
                              ? "high"
                              : "medium"
                          }
                        >
                          {alert.severity}
                        </Badge>
                        <span className="text-xs text-neutral-500">{alert.id}</span>
                      </div>
                      <p className="font-medium">{alert.title}</p>
                      <p className="text-sm text-neutral-500">{alert.date}</p>
                    </div>
                    <Button variant="ghost" size="icon-sm">
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
            <Link href="/dashboard/alerts">
              <Button variant="outline" className="w-full mt-4">
                View All Alerts
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
