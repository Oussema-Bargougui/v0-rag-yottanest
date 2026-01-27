"use client"

import dynamic from "next/dynamic"
import { TrendingUp, TrendingDown, AlertTriangle, Shield, Building2, ArrowRight } from "lucide-react"
import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

// Dynamic imports for recharts
const ResponsiveContainer = dynamic(() => import("recharts").then((mod) => mod.ResponsiveContainer), { ssr: false })
const AreaChart = dynamic(() => import("recharts").then((mod) => mod.AreaChart), { ssr: false })
const Area = dynamic(() => import("recharts").then((mod) => mod.Area), { ssr: false })
const XAxis = dynamic(() => import("recharts").then((mod) => mod.XAxis), { ssr: false })
const YAxis = dynamic(() => import("recharts").then((mod) => mod.YAxis), { ssr: false })
const CartesianGrid = dynamic(() => import("recharts").then((mod) => mod.CartesianGrid), { ssr: false })
const Tooltip = dynamic(() => import("recharts").then((mod) => mod.Tooltip), { ssr: false })
const BarChart = dynamic(() => import("recharts").then((mod) => mod.BarChart), { ssr: false })
const Bar = dynamic(() => import("recharts").then((mod) => mod.Bar), { ssr: false })

const riskTrendData = [
  { month: "Jul", critical: 15, high: 32, medium: 48, low: 85 },
  { month: "Aug", critical: 18, high: 35, medium: 52, low: 82 },
  { month: "Sep", critical: 14, high: 30, medium: 55, low: 88 },
  { month: "Oct", critical: 12, high: 28, medium: 50, low: 92 },
  { month: "Nov", critical: 16, high: 33, medium: 47, low: 89 },
  { month: "Dec", critical: 11, high: 26, medium: 44, low: 95 },
  { month: "Jan", critical: 12, high: 28, medium: 45, low: 89 },
]

const riskByIndustryData = [
  { industry: "Financial Services", score: 78 },
  { industry: "Import/Export", score: 72 },
  { industry: "Real Estate", score: 65 },
  { industry: "Technology", score: 42 },
  { industry: "Manufacturing", score: 35 },
  { industry: "Retail", score: 28 },
]

const topRiskEntities = [
  { name: "Acme Corporation Ltd", id: "ENT-4521", score: 94, change: 8 },
  { name: "Oceanic Exports LLC", id: "ENT-2741", score: 85, change: -3 },
  { name: "Global Trading Inc", id: "ENT-3892", score: 78, change: 5 },
  { name: "Eastern Commerce Ltd", id: "ENT-5123", score: 72, change: 12 },
  { name: "Pacific Ventures LLC", id: "ENT-7892", score: 68, change: -2 },
]

export default function RiskOverviewPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Risk Overview"
        description="Comprehensive view of risk metrics across all monitored entities"
        actions={
          <Button variant="outline">
            Export Report
          </Button>
        }
      />

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-red-50 to-white border-red-100">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-neutral-500">Critical Risk</p>
                <p className="text-3xl font-bold text-red-600">12</p>
                <p className="text-sm text-red-600 flex items-center gap-1">
                  <TrendingDown className="h-4 w-4" />
                  -8% from last month
                </p>
              </div>
              <AlertTriangle className="h-10 w-10 text-red-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-white border-orange-100">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-neutral-500">High Risk</p>
                <p className="text-3xl font-bold text-orange-600">28</p>
                <p className="text-sm text-orange-600 flex items-center gap-1">
                  <TrendingUp className="h-4 w-4" />
                  +5% from last month
                </p>
              </div>
              <TrendingUp className="h-10 w-10 text-orange-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-yellow-50 to-white border-yellow-100">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-neutral-500">Medium Risk</p>
                <p className="text-3xl font-bold text-yellow-600">45</p>
                <p className="text-sm text-green-600 flex items-center gap-1">
                  <TrendingDown className="h-4 w-4" />
                  -12% from last month
                </p>
              </div>
              <Building2 className="h-10 w-10 text-yellow-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-white border-green-100">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-neutral-500">Low/Clear</p>
                <p className="text-3xl font-bold text-green-600">323</p>
                <p className="text-sm text-green-600 flex items-center gap-1">
                  <TrendingUp className="h-4 w-4" />
                  +18% from last month
                </p>
              </div>
              <Shield className="h-10 w-10 text-green-200" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Risk Distribution Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={riskTrendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis dataKey="month" tick={{ fontSize: 12, fill: "#6B7280" }} />
                  <YAxis tick={{ fontSize: 12, fill: "#6B7280" }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "white",
                      border: "1px solid #E5E7EB",
                      borderRadius: "8px",
                    }}
                  />
                  <Area type="monotone" dataKey="low" stackId="1" stroke="#16A34A" fill="#DCFCE7" />
                  <Area type="monotone" dataKey="medium" stackId="1" stroke="#CA8A04" fill="#FEF9C3" />
                  <Area type="monotone" dataKey="high" stackId="1" stroke="#EA580C" fill="#FFEDD5" />
                  <Area type="monotone" dataKey="critical" stackId="1" stroke="#DC2626" fill="#FEE2E2" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Risk by Industry</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={riskByIndustryData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis type="number" tick={{ fontSize: 12, fill: "#6B7280" }} domain={[0, 100]} />
                  <YAxis type="category" dataKey="industry" tick={{ fontSize: 12, fill: "#6B7280" }} width={120} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "white",
                      border: "1px solid #E5E7EB",
                      borderRadius: "8px",
                    }}
                  />
                  <Bar
                    dataKey="score"
                    radius={[0, 4, 4, 0]}
                    fill="#2C5282"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Top Risk Entities */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg">Top Risk Entities</CardTitle>
          <Button variant="ghost" size="sm">
            View All
            <ArrowRight className="ml-1 h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {topRiskEntities.map((entity, index) => (
              <div
                key={entity.id}
                className="flex items-center justify-between p-4 rounded-lg bg-neutral-50 hover:bg-neutral-100 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="w-8 h-8 rounded-full bg-neutral-200 flex items-center justify-center font-bold text-neutral-600">
                    {index + 1}
                  </div>
                  <div>
                    <p className="font-medium text-neutral-900">{entity.name}</p>
                    <p className="text-sm text-neutral-500">{entity.id}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className={`flex items-center gap-1 text-sm ${entity.change > 0 ? "text-red-600" : "text-green-600"}`}>
                    {entity.change > 0 ? (
                      <TrendingUp className="h-4 w-4" />
                    ) : (
                      <TrendingDown className="h-4 w-4" />
                    )}
                    {entity.change > 0 ? "+" : ""}{entity.change}
                  </div>
                  <Badge
                    variant={
                      entity.score >= 90 ? "critical" :
                      entity.score >= 70 ? "high" :
                      entity.score >= 40 ? "medium" : "low"
                    }
                    className="min-w-[60px] justify-center"
                  >
                    {entity.score}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
