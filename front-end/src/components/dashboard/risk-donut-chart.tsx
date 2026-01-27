"use client"

import dynamic from "next/dynamic"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const PieChart = dynamic(() => import("recharts").then((mod) => mod.PieChart), { ssr: false })
const Pie = dynamic(() => import("recharts").then((mod) => mod.Pie), { ssr: false })
const Cell = dynamic(() => import("recharts").then((mod) => mod.Cell), { ssr: false })
const ResponsiveContainer = dynamic(() => import("recharts").then((mod) => mod.ResponsiveContainer), { ssr: false })
const Legend = dynamic(() => import("recharts").then((mod) => mod.Legend), { ssr: false })
const Tooltip = dynamic(() => import("recharts").then((mod) => mod.Tooltip), { ssr: false })

const RISK_COLORS = {
  Critical: "#DC2626",
  High: "#EA580C",
  Medium: "#CA8A04",
  Low: "#16A34A",
  Clear: "#0D9488",
}

interface RiskData {
  name: string
  value: number
  color: string
  [key: string]: string | number
}

interface RiskDonutChartProps {
  data?: RiskData[]
}

const defaultData: RiskData[] = [
  { name: "Critical", value: 12, color: RISK_COLORS.Critical },
  { name: "High", value: 28, color: RISK_COLORS.High },
  { name: "Medium", value: 45, color: RISK_COLORS.Medium },
  { name: "Low", value: 89, color: RISK_COLORS.Low },
  { name: "Clear", value: 234, color: RISK_COLORS.Clear },
]

export function RiskDonutChart({ data = defaultData }: RiskDonutChartProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0)

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-lg font-semibold">Risk Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value, name) => [
                  `${value} (${((Number(value) / total) * 100).toFixed(1)}%)`,
                  name,
                ]}
                contentStyle={{
                  backgroundColor: "white",
                  border: "1px solid #E5E7EB",
                  borderRadius: "8px",
                  boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                }}
              />
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(value) => (
                  <span className="text-sm text-neutral-600">{value}</span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-4 text-center">
          <p className="text-2xl font-bold text-neutral-900">{total}</p>
          <p className="text-sm text-neutral-500">Total Entities</p>
        </div>
      </CardContent>
    </Card>
  )
}
