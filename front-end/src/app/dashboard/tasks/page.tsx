"use client"

import { useState } from "react"
import {
  CheckSquare,
  Search,
  Filter,
  Plus,
  Clock,
  User,
  Calendar,
  CheckCircle,
  Circle,
  MoreHorizontal,
} from "lucide-react"
import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

interface Task {
  id: string
  title: string
  description: string
  priority: "high" | "medium" | "low"
  status: "todo" | "in_progress" | "completed"
  assignedTo: string
  dueDate: string
  relatedCase?: string
  relatedEntity?: string
}

const mockTasks: Task[] = [
  {
    id: "TASK-001",
    title: "Review suspicious transaction report",
    description: "Analyze and document findings for transaction pattern ALT-001",
    priority: "high",
    status: "in_progress",
    assignedTo: "John Smith",
    dueDate: "2024-01-16",
    relatedCase: "CASE-001",
    relatedEntity: "Acme Corporation Ltd",
  },
  {
    id: "TASK-002",
    title: "Complete PEP due diligence",
    description: "Verify PEP status and document beneficial ownership structure",
    priority: "high",
    status: "todo",
    assignedTo: "Sarah Johnson",
    dueDate: "2024-01-17",
    relatedCase: "CASE-002",
    relatedEntity: "Global Trading Inc",
  },
  {
    id: "TASK-003",
    title: "Request additional KYC documents",
    description: "Contact entity for updated proof of address and ID verification",
    priority: "medium",
    status: "todo",
    assignedTo: "Mike Brown",
    dueDate: "2024-01-18",
    relatedEntity: "Oceanic Exports LLC",
  },
  {
    id: "TASK-004",
    title: "Prepare SAR filing",
    description: "Draft Suspicious Activity Report for regulatory submission",
    priority: "high",
    status: "in_progress",
    assignedTo: "John Smith",
    dueDate: "2024-01-15",
    relatedCase: "CASE-001",
  },
  {
    id: "TASK-005",
    title: "Schedule compliance review meeting",
    description: "Coordinate with senior management for quarterly compliance review",
    priority: "medium",
    status: "completed",
    assignedTo: "Sarah Johnson",
    dueDate: "2024-01-14",
  },
  {
    id: "TASK-006",
    title: "Update risk scoring model",
    description: "Incorporate new risk factors from recent regulatory guidance",
    priority: "low",
    status: "todo",
    assignedTo: "Mike Brown",
    dueDate: "2024-01-20",
  },
  {
    id: "TASK-007",
    title: "Review document processing results",
    description: "Verify OCR accuracy for batch DOC-001 through DOC-010",
    priority: "medium",
    status: "in_progress",
    assignedTo: "John Smith",
    dueDate: "2024-01-16",
  },
  {
    id: "TASK-008",
    title: "Escalate geographic risk findings",
    description: "Prepare escalation report for transactions with high-risk jurisdictions",
    priority: "high",
    status: "todo",
    assignedTo: "Sarah Johnson",
    dueDate: "2024-01-16",
    relatedCase: "CASE-003",
  },
]

const priorityConfig = {
  high: { label: "High", className: "bg-red-100 text-red-700" },
  medium: { label: "Medium", className: "bg-yellow-100 text-yellow-700" },
  low: { label: "Low", className: "bg-green-100 text-green-700" },
}

const statusConfig = {
  todo: { label: "To Do", icon: Circle },
  in_progress: { label: "In Progress", icon: Clock },
  completed: { label: "Completed", icon: CheckCircle },
}

export default function TasksPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [filter, setFilter] = useState<string>("all")

  const filteredTasks = mockTasks.filter((task) => {
    if (filter !== "all" && task.status !== filter) return false
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        task.title.toLowerCase().includes(query) ||
        task.description.toLowerCase().includes(query) ||
        task.id.toLowerCase().includes(query)
      )
    }
    return true
  })

  const stats = {
    total: mockTasks.length,
    todo: mockTasks.filter((t) => t.status === "todo").length,
    inProgress: mockTasks.filter((t) => t.status === "in_progress").length,
    completed: mockTasks.filter((t) => t.status === "completed").length,
  }

  const isOverdue = (dueDate: string) => {
    return new Date(dueDate) < new Date()
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Task Management"
        description="Track and manage compliance-related tasks"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Task
          </Button>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-2xl font-bold text-neutral-900">{stats.total}</div>
          <div className="text-sm text-neutral-500">Total Tasks</div>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-blue-600">{stats.todo}</div>
          <div className="text-sm text-neutral-500">To Do</div>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-yellow-600">{stats.inProgress}</div>
          <div className="text-sm text-neutral-500">In Progress</div>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-green-600">{stats.completed}</div>
          <div className="text-sm text-neutral-500">Completed</div>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        {[
          { key: "all", label: "All Tasks" },
          { key: "todo", label: "To Do" },
          { key: "in_progress", label: "In Progress" },
          { key: "completed", label: "Completed" },
        ].map((tab) => (
          <Button
            key={tab.key}
            variant={filter === tab.key ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(tab.key)}
          >
            {tab.label}
          </Button>
        ))}
      </div>

      {/* Search */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400" />
          <Input
            placeholder="Search tasks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button variant="outline">
          <Filter className="mr-2 h-4 w-4" />
          Filters
        </Button>
      </div>

      {/* Task Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {(["todo", "in_progress", "completed"] as const).map((status) => {
          const StatusIcon = statusConfig[status].icon
          const tasksInColumn = filteredTasks.filter((t) => t.status === status)

          return (
            <Card key={status}>
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-medium flex items-center gap-2">
                  <StatusIcon className="h-4 w-4" />
                  {statusConfig[status].label}
                  <Badge variant="secondary" className="ml-auto">
                    {tasksInColumn.length}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {tasksInColumn.map((task) => {
                  const priority = priorityConfig[task.priority]
                  const overdue = isOverdue(task.dueDate) && task.status !== "completed"

                  return (
                    <div
                      key={task.id}
                      className={`p-4 rounded-lg border bg-white hover:shadow-sm transition-shadow ${
                        overdue ? "border-red-200" : ""
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${priority.className}`}>
                          {priority.label}
                        </span>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon-sm" className="-mr-2 -mt-1">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>Edit Task</DropdownMenuItem>
                            <DropdownMenuItem>Move to In Progress</DropdownMenuItem>
                            <DropdownMenuItem>
                              <CheckCircle className="mr-2 h-4 w-4" />
                              Mark Complete
                            </DropdownMenuItem>
                            <DropdownMenuItem className="text-red-600">Delete</DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                      <h4 className="font-medium text-neutral-900 text-sm mb-1">
                        {task.title}
                      </h4>
                      <p className="text-xs text-neutral-500 mb-3 line-clamp-2">
                        {task.description}
                      </p>
                      <div className="flex items-center justify-between text-xs text-neutral-500">
                        <span className="flex items-center gap-1">
                          <User className="h-3 w-3" />
                          {task.assignedTo.split(" ")[0]}
                        </span>
                        <span className={`flex items-center gap-1 ${overdue ? "text-red-600 font-medium" : ""}`}>
                          <Calendar className="h-3 w-3" />
                          {new Date(task.dueDate).toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric",
                          })}
                        </span>
                      </div>
                      {(task.relatedCase || task.relatedEntity) && (
                        <div className="mt-2 pt-2 border-t text-xs text-neutral-400">
                          {task.relatedCase && <span>{task.relatedCase}</span>}
                          {task.relatedCase && task.relatedEntity && <span> • </span>}
                          {task.relatedEntity && <span>{task.relatedEntity}</span>}
                        </div>
                      )}
                    </div>
                  )
                })}

                {tasksInColumn.length === 0 && (
                  <div className="text-center py-8 text-neutral-400 text-sm">
                    No tasks
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
