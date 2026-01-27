import { LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"
import { Card } from "@/components/ui/card"

interface StatCardProps {
  title: string
  value: string | number
  icon: LucideIcon
  trend?: {
    value: number
    label: string
  }
  variant?: "default" | "critical" | "high" | "medium" | "low" | "clear"
}

const variantStyles = {
  default: {
    icon: "bg-primary-100 text-primary-600",
    trend: "text-neutral-500",
  },
  critical: {
    icon: "bg-red-100 text-red-600",
    trend: "text-red-600",
  },
  high: {
    icon: "bg-orange-100 text-orange-600",
    trend: "text-orange-600",
  },
  medium: {
    icon: "bg-yellow-100 text-yellow-600",
    trend: "text-yellow-600",
  },
  low: {
    icon: "bg-green-100 text-green-600",
    trend: "text-green-600",
  },
  clear: {
    icon: "bg-teal-100 text-teal-600",
    trend: "text-teal-600",
  },
}

export function StatCard({
  title,
  value,
  icon: Icon,
  trend,
  variant = "default",
}: StatCardProps) {
  const styles = variantStyles[variant]

  return (
    <Card className="p-6">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-sm font-medium text-neutral-500">{title}</p>
          <p className="text-3xl font-bold text-neutral-900">{value}</p>
          {trend && (
            <p className={cn("text-sm", styles.trend)}>
              <span className={trend.value >= 0 ? "text-green-600" : "text-red-600"}>
                {trend.value >= 0 ? "+" : ""}
                {trend.value}%
              </span>{" "}
              <span className="text-neutral-500">{trend.label}</span>
            </p>
          )}
        </div>
        <div className={cn("p-3 rounded-lg", styles.icon)}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </Card>
  )
}
