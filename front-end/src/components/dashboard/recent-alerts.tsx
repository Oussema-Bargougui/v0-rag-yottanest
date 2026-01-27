"use client"

import { AlertTriangle, Clock, ArrowRight } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import Link from "next/link"

interface Alert {
  id: string
  title: string
  entity: string
  severity: "critical" | "high" | "medium" | "low"
  timestamp: string
  riskScore: number
}

interface RecentAlertsProps {
  alerts?: Alert[]
}

const defaultAlerts: Alert[] = [
  {
    id: "ALT-001",
    title: "Suspicious Transaction Pattern",
    entity: "Acme Corporation Ltd",
    severity: "critical",
    timestamp: "2 minutes ago",
    riskScore: 94,
  },
  {
    id: "ALT-002",
    title: "PEP Match Detected",
    entity: "Global Trading Inc",
    severity: "high",
    timestamp: "15 minutes ago",
    riskScore: 78,
  },
  {
    id: "ALT-003",
    title: "Unusual Geographic Activity",
    entity: "Oceanic Exports LLC",
    severity: "high",
    timestamp: "32 minutes ago",
    riskScore: 72,
  },
  {
    id: "ALT-004",
    title: "Document Verification Failed",
    entity: "Tech Solutions Corp",
    severity: "medium",
    timestamp: "1 hour ago",
    riskScore: 56,
  },
  {
    id: "ALT-005",
    title: "Threshold Breach Alert",
    entity: "Eastern Commerce Ltd",
    severity: "medium",
    timestamp: "2 hours ago",
    riskScore: 48,
  },
]

const severityConfig = {
  critical: {
    variant: "critical" as const,
    bg: "bg-red-50",
    border: "border-red-100",
  },
  high: {
    variant: "high" as const,
    bg: "bg-orange-50",
    border: "border-orange-100",
  },
  medium: {
    variant: "medium" as const,
    bg: "bg-yellow-50",
    border: "border-yellow-100",
  },
  low: {
    variant: "low" as const,
    bg: "bg-green-50",
    border: "border-green-100",
  },
}

export function RecentAlerts({ alerts = defaultAlerts }: RecentAlertsProps) {
  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg font-semibold flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          Recent Alerts
        </CardTitle>
        <Link href="/dashboard/alerts">
          <Button variant="ghost" size="sm" className="text-primary-500">
            View All
            <ArrowRight className="ml-1 h-4 w-4" />
          </Button>
        </Link>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {alerts.map((alert) => {
            const config = severityConfig[alert.severity]
            return (
              <div
                key={alert.id}
                className={`p-4 rounded-lg border ${config.bg} ${config.border} hover:shadow-sm transition-shadow cursor-pointer`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant={config.variant} className="capitalize">
                        {alert.severity}
                      </Badge>
                      <span className="text-xs text-neutral-500">{alert.id}</span>
                    </div>
                    <h4 className="font-medium text-neutral-900 truncate">
                      {alert.title}
                    </h4>
                    <p className="text-sm text-neutral-600 truncate">
                      {alert.entity}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-lg font-bold text-neutral-900">
                      {alert.riskScore}
                    </div>
                    <div className="flex items-center gap-1 text-xs text-neutral-500">
                      <Clock className="h-3 w-3" />
                      {alert.timestamp}
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
