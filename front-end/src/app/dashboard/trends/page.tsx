"use client"

import dynamic from "next/dynamic"
import { TrendingUp, Calendar } from "lucide-react"
import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

// Dynamic imports for recharts
const ResponsiveContainer = dynamic(() => import("recharts").then((mod) => mod.ResponsiveContainer), { ssr: false })
const LineChart = dynamic(() => import("recharts").then((mod) => mod.LineChart), { ssr: false })
const Line = dynamic(() => import("recharts").then((mod) => mod.Line), { ssr: false })
const BarChart = dynamic(() => import("recharts").then((mod) => mod.BarChart), { ssr: false })
const Bar = dynamic(() => import("recharts").then((mod) => mod.Bar), { ssr: false })
const XAxis = dynamic(() => import("recharts").then((mod) => mod.XAxis), { ssr: false })
const YAxis = dynamic(() => import("recharts").then((mod) => mod.YAxis), { ssr: false })
const CartesianGrid = dynamic(() => import("recharts").then((mod) => mod.CartesianGrid), { ssr: false })
const Tooltip = dynamic(() => import("recharts").then((mod) => mod.Tooltip), { ssr: false })
const Legend = dynamic(() => import("recharts").then((mod) => mod.Legend), { ssr: false })

const alertTrendData = [
  { week: "W1", alerts: 45, resolved: 38, escalated: 7 },
  { week: "W2", alerts: 52, resolved: 45, escalated: 5 },
  { week: "W3", alerts: 38, resolved: 35, escalated: 8 },
  { week: "W4", alerts: 65, resolved: 55, escalated: 10 },
  { week: "W5", alerts: 48, resolved: 42, escalated: 6 },
  { week: "W6", alerts: 55, resolved: 50, escalated: 5 },
  { week: "W7", alerts: 42, resolved: 38, escalated: 4 },
  { week: "W8", alerts: 58, resolved: 52, escalated: 6 },
]

const transactionVolumeData = [
  { month: "Aug", volume: 2.4, count: 1250 },
  { month: "Sep", volume: 2.8, count: 1420 },
  { month: "Oct", volume: 3.2, count: 1580 },
  { month: "Nov", volume: 2.9, count: 1350 },
  { month: "Dec", volume: 3.5, count: 1680 },
  { month: "Jan", volume: 3.1, count: 1520 },
]

const documentProcessingData = [
  { day: "Mon", processed: 45, pending: 12 },
  { day: "Tue", processed: 52, pending: 8 },
  { day: "Wed", processed: 38, pending: 15 },
  { day: "Thu", processed: 65, pending: 5 },
  { day: "Fri", processed: 48, pending: 10 },
  { day: "Sat", processed: 22, pending: 3 },
  { day: "Sun", processed: 15, pending: 2 },
]

const caseResolutionData = [
  { month: "Aug", avgDays: 12 },
  { month: "Sep", avgDays: 10 },
  { month: "Oct", avgDays: 8 },
  { month: "Nov", avgDays: 9 },
  { month: "Dec", avgDays: 7 },
  { month: "Jan", avgDays: 6 },
]

export default function TrendsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Trends & Analytics"
        description="Historical trends and performance metrics"
        actions={
          <Button variant="outline">
            <Calendar className="mr-2 h-4 w-4" />
            Last 30 Days
          </Button>
        }
      />

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-100">
              <TrendingUp className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">342</p>
              <p className="text-sm text-neutral-500">Alerts This Month</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-100">
              <TrendingUp className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">94%</p>
              <p className="text-sm text-neutral-500">Resolution Rate</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-100">
              <TrendingUp className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">6.2</p>
              <p className="text-sm text-neutral-500">Avg. Days to Resolve</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-orange-100">
              <TrendingUp className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">$3.1M</p>
              <p className="text-sm text-neutral-500">Transaction Volume</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Alert Trends */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Alert Trends (8 Weeks)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={alertTrendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis dataKey="week" tick={{ fontSize: 12, fill: "#6B7280" }} />
                  <YAxis tick={{ fontSize: 12, fill: "#6B7280" }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "white",
                      border: "1px solid #E5E7EB",
                      borderRadius: "8px",
                    }}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="alerts" stroke="#DC2626" strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="resolved" stroke="#16A34A" strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="escalated" stroke="#EA580C" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Transaction Volume */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Transaction Volume (6 Months)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={transactionVolumeData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis dataKey="month" tick={{ fontSize: 12, fill: "#6B7280" }} />
                  <YAxis
                    tick={{ fontSize: 12, fill: "#6B7280" }}
                    tickFormatter={(value) => `$${value}M`}
                  />
                  <Tooltip
                    formatter={(value) => [`$${value}M`, "Volume"]}
                    contentStyle={{
                      backgroundColor: "white",
                      border: "1px solid #E5E7EB",
                      borderRadius: "8px",
                    }}
                  />
                  <Bar dataKey="volume" fill="#2C5282" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Document Processing */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Document Processing (This Week)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={documentProcessingData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis dataKey="day" tick={{ fontSize: 12, fill: "#6B7280" }} />
                  <YAxis tick={{ fontSize: 12, fill: "#6B7280" }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "white",
                      border: "1px solid #E5E7EB",
                      borderRadius: "8px",
                    }}
                  />
                  <Legend />
                  <Bar dataKey="processed" fill="#16A34A" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="pending" fill="#CA8A04" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Case Resolution Time */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Avg. Case Resolution Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={caseResolutionData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis dataKey="month" tick={{ fontSize: 12, fill: "#6B7280" }} />
                  <YAxis
                    tick={{ fontSize: 12, fill: "#6B7280" }}
                    tickFormatter={(value) => `${value}d`}
                  />
                  <Tooltip
                    formatter={(value) => [`${value} days`, "Avg. Resolution"]}
                    contentStyle={{
                      backgroundColor: "white",
                      border: "1px solid #E5E7EB",
                      borderRadius: "8px",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="avgDays"
                    stroke="#8B5CF6"
                    strokeWidth={3}
                    dot={{ r: 6, fill: "#8B5CF6" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
