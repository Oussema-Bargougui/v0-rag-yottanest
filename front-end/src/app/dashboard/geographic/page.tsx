"use client"

import dynamic from "next/dynamic"
import { Map, Globe, AlertTriangle, Building2 } from "lucide-react"
import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

// Dynamic imports for recharts
const ResponsiveContainer = dynamic(() => import("recharts").then((mod) => mod.ResponsiveContainer), { ssr: false })
const BarChart = dynamic(() => import("recharts").then((mod) => mod.BarChart), { ssr: false })
const Bar = dynamic(() => import("recharts").then((mod) => mod.Bar), { ssr: false })
const XAxis = dynamic(() => import("recharts").then((mod) => mod.XAxis), { ssr: false })
const YAxis = dynamic(() => import("recharts").then((mod) => mod.YAxis), { ssr: false })
const CartesianGrid = dynamic(() => import("recharts").then((mod) => mod.CartesianGrid), { ssr: false })
const Tooltip = dynamic(() => import("recharts").then((mod) => mod.Tooltip), { ssr: false })
const Treemap = dynamic(() => import("recharts").then((mod) => mod.Treemap), { ssr: false })

const countryRiskData = [
  { country: "Cayman Islands", riskLevel: "High", entities: 8, transactions: 45, avgRiskScore: 82 },
  { country: "Panama", riskLevel: "High", entities: 5, transactions: 32, avgRiskScore: 78 },
  { country: "UAE", riskLevel: "Medium", entities: 12, transactions: 89, avgRiskScore: 58 },
  { country: "Hong Kong", riskLevel: "Medium", entities: 15, transactions: 124, avgRiskScore: 52 },
  { country: "Singapore", riskLevel: "Low", entities: 22, transactions: 187, avgRiskScore: 35 },
  { country: "United Kingdom", riskLevel: "Low", entities: 45, transactions: 312, avgRiskScore: 28 },
  { country: "Germany", riskLevel: "Low", entities: 38, transactions: 245, avgRiskScore: 25 },
  { country: "United States", riskLevel: "Low", entities: 89, transactions: 567, avgRiskScore: 22 },
  { country: "Canada", riskLevel: "Low", entities: 28, transactions: 178, avgRiskScore: 20 },
  { country: "Australia", riskLevel: "Low", entities: 19, transactions: 134, avgRiskScore: 18 },
]

const transactionsByRegion = [
  { region: "North America", value: 745 },
  { region: "Europe", value: 557 },
  { region: "Asia Pacific", value: 445 },
  { region: "Middle East", value: 121 },
  { region: "Caribbean", value: 77 },
  { region: "Central America", value: 32 },
]

const highRiskJurisdictions = [
  { name: "Cayman Islands", fatfStatus: "Grey List", entities: 8, alerts: 12 },
  { name: "Panama", fatfStatus: "Grey List", entities: 5, alerts: 8 },
  { name: "Myanmar", fatfStatus: "Black List", entities: 1, alerts: 3 },
  { name: "North Korea", fatfStatus: "Black List", entities: 0, alerts: 0 },
  { name: "Iran", fatfStatus: "Black List", entities: 0, alerts: 0 },
]

const getRiskLevelColor = (level: string) => {
  switch (level) {
    case "High": return "text-red-600 bg-red-100"
    case "Medium": return "text-yellow-600 bg-yellow-100"
    case "Low": return "text-green-600 bg-green-100"
    default: return "text-neutral-600 bg-neutral-100"
  }
}

export default function GeographicPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Geographic Risk Analysis"
        description="Monitor geographic distribution and jurisdiction-based risks"
        actions={
          <Button variant="outline">
            <Globe className="mr-2 h-4 w-4" />
            Update FATF List
          </Button>
        }
      />

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-100">
              <Globe className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">42</p>
              <p className="text-sm text-neutral-500">Countries Active</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-red-100">
              <AlertTriangle className="h-5 w-5 text-red-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">5</p>
              <p className="text-sm text-neutral-500">High-Risk Jurisdictions</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-yellow-100">
              <Map className="h-5 w-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">13</p>
              <p className="text-sm text-neutral-500">FATF Watchlist</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-100">
              <Building2 className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">281</p>
              <p className="text-sm text-neutral-500">Total Entities</p>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Transactions by Region */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Transactions by Region</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={transactionsByRegion} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis type="number" tick={{ fontSize: 12, fill: "#6B7280" }} />
                  <YAxis type="category" dataKey="region" tick={{ fontSize: 12, fill: "#6B7280" }} width={120} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "white",
                      border: "1px solid #E5E7EB",
                      borderRadius: "8px",
                    }}
                  />
                  <Bar dataKey="value" fill="#2C5282" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* High-Risk Jurisdictions */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">FATF Watchlist Countries</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {highRiskJurisdictions.map((jurisdiction) => (
                <div
                  key={jurisdiction.name}
                  className="flex items-center justify-between p-3 rounded-lg bg-neutral-50"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${
                      jurisdiction.fatfStatus === "Black List" ? "bg-red-500" : "bg-yellow-500"
                    }`} />
                    <div>
                      <p className="font-medium text-neutral-900">{jurisdiction.name}</p>
                      <p className="text-sm text-neutral-500">{jurisdiction.fatfStatus}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    <span className="text-neutral-500">{jurisdiction.entities} entities</span>
                    {jurisdiction.alerts > 0 && (
                      <Badge variant="destructive">{jurisdiction.alerts} alerts</Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Country Risk Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Country Risk Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-medium text-neutral-500">Country</th>
                  <th className="text-left py-3 px-4 font-medium text-neutral-500">Risk Level</th>
                  <th className="text-center py-3 px-4 font-medium text-neutral-500">Entities</th>
                  <th className="text-center py-3 px-4 font-medium text-neutral-500">Transactions</th>
                  <th className="text-center py-3 px-4 font-medium text-neutral-500">Avg. Risk Score</th>
                </tr>
              </thead>
              <tbody>
                {countryRiskData.map((country) => (
                  <tr key={country.country} className="border-b hover:bg-neutral-50">
                    <td className="py-3 px-4 font-medium">{country.country}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskLevelColor(country.riskLevel)}`}>
                        {country.riskLevel}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">{country.entities}</td>
                    <td className="py-3 px-4 text-center">{country.transactions}</td>
                    <td className="py-3 px-4 text-center">
                      <Badge
                        variant={
                          country.avgRiskScore >= 70 ? "high" :
                          country.avgRiskScore >= 40 ? "medium" : "low"
                        }
                      >
                        {country.avgRiskScore}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
