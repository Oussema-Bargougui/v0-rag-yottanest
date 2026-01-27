"use client"

import { useState, useMemo } from "react"
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  flexRender,
  ColumnDef,
  SortingState,
  ColumnFiltersState,
} from "@tanstack/react-table"
import {
  ArrowUpDown,
  Search,
  Filter,
  Download,
  ChevronLeft,
  ChevronRight,
  Eye,
} from "lucide-react"
import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { formatCurrency, formatDateTime, getRiskLabel } from "@/lib/utils"

interface Transaction {
  id: string
  date: string
  entity: string
  entityId: string
  type: "incoming" | "outgoing" | "internal"
  amount: number
  currency: string
  counterparty: string
  country: string
  riskScore: number
  status: "pending" | "cleared" | "flagged" | "blocked"
}

const mockTransactions: Transaction[] = [
  {
    id: "TXN-001",
    date: "2024-01-15T14:30:00Z",
    entity: "Acme Corporation Ltd",
    entityId: "ENT-4521",
    type: "outgoing",
    amount: 250000,
    currency: "USD",
    counterparty: "Offshore Holdings SA",
    country: "Cayman Islands",
    riskScore: 92,
    status: "flagged",
  },
  {
    id: "TXN-002",
    date: "2024-01-15T12:15:00Z",
    entity: "Global Trading Inc",
    entityId: "ENT-3892",
    type: "incoming",
    amount: 89500,
    currency: "EUR",
    counterparty: "European Imports GmbH",
    country: "Germany",
    riskScore: 28,
    status: "cleared",
  },
  {
    id: "TXN-003",
    date: "2024-01-15T10:45:00Z",
    entity: "Tech Solutions Corp",
    entityId: "ENT-1983",
    type: "outgoing",
    amount: 175000,
    currency: "USD",
    counterparty: "Asian Tech Partners",
    country: "Hong Kong",
    riskScore: 65,
    status: "pending",
  },
  {
    id: "TXN-004",
    date: "2024-01-15T09:30:00Z",
    entity: "Northern Industries Co",
    entityId: "ENT-6721",
    type: "internal",
    amount: 50000,
    currency: "USD",
    counterparty: "Northern Subsidiary LLC",
    country: "United States",
    riskScore: 12,
    status: "cleared",
  },
  {
    id: "TXN-005",
    date: "2024-01-14T16:20:00Z",
    entity: "Eastern Commerce Ltd",
    entityId: "ENT-5123",
    type: "outgoing",
    amount: 320000,
    currency: "USD",
    counterparty: "Dubai Trading FZE",
    country: "UAE",
    riskScore: 78,
    status: "flagged",
  },
  {
    id: "TXN-006",
    date: "2024-01-14T14:00:00Z",
    entity: "Pacific Ventures LLC",
    entityId: "ENT-7892",
    type: "incoming",
    amount: 145000,
    currency: "GBP",
    counterparty: "British Finance Ltd",
    country: "United Kingdom",
    riskScore: 35,
    status: "cleared",
  },
  {
    id: "TXN-007",
    date: "2024-01-14T11:30:00Z",
    entity: "Oceanic Exports LLC",
    entityId: "ENT-2741",
    type: "outgoing",
    amount: 420000,
    currency: "USD",
    counterparty: "Anonymous Shell Corp",
    country: "Panama",
    riskScore: 95,
    status: "blocked",
  },
  {
    id: "TXN-008",
    date: "2024-01-14T09:15:00Z",
    entity: "Metro Holdings Inc",
    entityId: "ENT-8234",
    type: "incoming",
    amount: 78000,
    currency: "CAD",
    counterparty: "Canadian Resources Inc",
    country: "Canada",
    riskScore: 18,
    status: "cleared",
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
  pending: { label: "Pending", className: "bg-yellow-100 text-yellow-700" },
  cleared: { label: "Cleared", className: "bg-green-100 text-green-700" },
  flagged: { label: "Flagged", className: "bg-red-100 text-red-700" },
  blocked: { label: "Blocked", className: "bg-neutral-100 text-neutral-700" },
}

const typeConfig = {
  incoming: { label: "Incoming", className: "text-green-600" },
  outgoing: { label: "Outgoing", className: "text-red-600" },
  internal: { label: "Internal", className: "text-blue-600" },
}

export default function TransactionsPage() {
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [globalFilter, setGlobalFilter] = useState("")

  const columns: ColumnDef<Transaction>[] = useMemo(
    () => [
      {
        accessorKey: "id",
        header: "Transaction ID",
        cell: ({ row }) => (
          <span className="font-mono text-sm">{row.getValue("id")}</span>
        ),
      },
      {
        accessorKey: "date",
        header: ({ column }) => (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="-ml-4"
          >
            Date
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        ),
        cell: ({ row }) => formatDateTime(row.getValue("date")),
      },
      {
        accessorKey: "entity",
        header: "Entity",
        cell: ({ row }) => (
          <div>
            <div className="font-medium">{row.getValue("entity")}</div>
            <div className="text-xs text-neutral-500">{row.original.entityId}</div>
          </div>
        ),
      },
      {
        accessorKey: "type",
        header: "Type",
        cell: ({ row }) => {
          const type = row.getValue("type") as keyof typeof typeConfig
          return (
            <span className={`font-medium ${typeConfig[type].className}`}>
              {typeConfig[type].label}
            </span>
          )
        },
      },
      {
        accessorKey: "amount",
        header: ({ column }) => (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="-ml-4"
          >
            Amount
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        ),
        cell: ({ row }) => {
          const amount = row.getValue("amount") as number
          const currency = row.original.currency
          return (
            <span className="font-medium">{formatCurrency(amount, currency)}</span>
          )
        },
      },
      {
        accessorKey: "counterparty",
        header: "Counterparty",
        cell: ({ row }) => (
          <div>
            <div>{row.getValue("counterparty")}</div>
            <div className="text-xs text-neutral-500">{row.original.country}</div>
          </div>
        ),
      },
      {
        accessorKey: "riskScore",
        header: ({ column }) => (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="-ml-4"
          >
            Risk Score
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        ),
        cell: ({ row }) => {
          const score = row.getValue("riskScore") as number
          return (
            <div className="flex items-center gap-2">
              <Badge variant={getRiskBadgeVariant(score)}>{score}</Badge>
              <span className="text-xs text-neutral-500">{getRiskLabel(score)}</span>
            </div>
          )
        },
      },
      {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => {
          const status = row.getValue("status") as keyof typeof statusConfig
          return (
            <span
              className={`px-2 py-1 rounded-full text-xs font-medium ${statusConfig[status].className}`}
            >
              {statusConfig[status].label}
            </span>
          )
        },
      },
      {
        id: "actions",
        header: "",
        cell: () => (
          <Button variant="ghost" size="icon-sm">
            <Eye className="h-4 w-4" />
          </Button>
        ),
      },
    ],
    []
  )

  const table = useReactTable({
    data: mockTransactions,
    columns,
    state: {
      sorting,
      columnFilters,
      globalFilter,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: { pageSize: 10 },
    },
  })

  return (
    <div className="space-y-6">
      <PageHeader
        title="Transaction Monitoring"
        description="Review and analyze transaction activity across all monitored entities"
        actions={
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        }
      />

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400" />
          <Input
            placeholder="Search transactions..."
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button variant="outline">
          <Filter className="mr-2 h-4 w-4" />
          Filters
        </Button>
      </div>

      {/* Table */}
      <Card>
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  No transactions found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>

        {/* Pagination */}
        <div className="flex items-center justify-between px-4 py-4 border-t">
          <div className="text-sm text-neutral-500">
            Showing {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1} to{" "}
            {Math.min(
              (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
              table.getFilteredRowModel().rows.length
            )}{" "}
            of {table.getFilteredRowModel().rows.length} transactions
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}
