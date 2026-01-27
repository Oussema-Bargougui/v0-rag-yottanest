"use client"

import {
  Building2,
  AlertTriangle,
  TrendingUp,
  ShieldCheck,
  FileText,
  Download,
} from "lucide-react"
import { PageHeader } from "@/components/layout/page-header"
import { StatCard } from "@/components/dashboard/stat-card"
import { RiskDonutChart } from "@/components/dashboard/risk-donut-chart"
import { TrendLineChart } from "@/components/dashboard/trend-line-chart"
import { RecentAlerts } from "@/components/dashboard/recent-alerts"
import { Button } from "@/components/ui/button"

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard Overview"
        description="Monitor real-time compliance metrics and risk indicators"
        lastUpdated="2 minutes ago"
        actions={
          <>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
            <Button>
              <FileText className="mr-2 h-4 w-4" />
              New Report
            </Button>
          </>
        }
      />

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Entities"
          value="408"
          icon={Building2}
          trend={{ value: 12, label: "from last month" }}
          variant="default"
        />
        <StatCard
          title="Critical Risk"
          value="12"
          icon={AlertTriangle}
          trend={{ value: -8, label: "from last month" }}
          variant="critical"
        />
        <StatCard
          title="High Risk"
          value="28"
          icon={TrendingUp}
          trend={{ value: 5, label: "from last month" }}
          variant="high"
        />
        <StatCard
          title="Cleared Entities"
          value="234"
          icon={ShieldCheck}
          trend={{ value: 18, label: "from last month" }}
          variant="clear"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <RiskDonutChart />
        </div>
        <div className="lg:col-span-2">
          <TrendLineChart />
        </div>
      </div>

      {/* Alerts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecentAlerts />

        {/* Quick Actions Card */}
        <div className="bg-white rounded-xl border border-neutral-200 shadow-sm p-6">
          <h3 className="text-lg font-semibold text-neutral-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 gap-4">
            <Button variant="outline" className="h-auto py-4 flex flex-col items-center gap-2">
              <FileText className="h-6 w-6" />
              <span>Generate SAR</span>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex flex-col items-center gap-2">
              <Building2 className="h-6 w-6" />
              <span>Add Entity</span>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex flex-col items-center gap-2">
              <TrendingUp className="h-6 w-6" />
              <span>Risk Report</span>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex flex-col items-center gap-2">
              <ShieldCheck className="h-6 w-6" />
              <span>Compliance Audit</span>
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
