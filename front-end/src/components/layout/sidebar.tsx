"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard,
  Search,
  ArrowRightLeft,
  Building2,
  FolderOpen,
  CheckSquare,
  FileText,
  Upload,
  Loader2,
  CheckCircle,
  TrendingUp,
  BarChart3,
  Map,
  Settings,
  HelpCircle,
  ChevronDown,
  MessageSquare,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useSidebarStore } from "@/store/sidebar-store"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface NavItem {
  title: string
  href: string
  icon: React.ElementType
  badge?: number
}

interface NavSection {
  title: string
  items: NavItem[]
}

const navSections: NavSection[] = [
  {
    title: "MAIN",
    items: [
      { title: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
      { title: "Company Search", href: "/dashboard/alerts", icon: Search },
      { title: "Transactions", href: "/dashboard/transactions", icon: ArrowRightLeft },
      { title: "Entities", href: "/dashboard/entities", icon: Building2 },
    ],
  },
  {
    title: "INVESTIGATION",
    items: [
      { title: "Cases", href: "/dashboard/cases", icon: FolderOpen, badge: 3 },
      { title: "Tasks", href: "/dashboard/tasks", icon: CheckSquare, badge: 8 },
      { title: "Reports", href: "/dashboard/reports", icon: FileText },
    ],
  },
  {
    title: "DOCUMENTS",
    items: [
      { title: "Upload", href: "/dashboard/documents/upload", icon: Upload },
      { title: "Chat with Docs", href: "/dashboard/documents/chat", icon: MessageSquare },
      { title: "Processing", href: "/dashboard/documents/processing", icon: Loader2, badge: 5 },
      { title: "Completed", href: "/dashboard/documents/completed", icon: CheckCircle },
    ],
  },
  {
    title: "ANALYTICS",
    items: [
      { title: "Risk Overview", href: "/dashboard/risk-overview", icon: TrendingUp },
      { title: "Trends", href: "/dashboard/trends", icon: BarChart3 },
      { title: "Geographic", href: "/dashboard/geographic", icon: Map },
    ],
  },
]

const bottomNavItems: NavItem[] = [
  { title: "Settings", href: "/settings", icon: Settings },
  { title: "Help & Support", href: "/help", icon: HelpCircle },
]

function NavItemComponent({
  item,
  isCollapsed,
  isActive,
}: {
  item: NavItem
  isCollapsed: boolean
  isActive: boolean
}) {
  const Icon = item.icon

  const content = (
    <Link
      href={item.href}
      className={cn(
        "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-150",
        "text-white/70 hover:text-white/90 hover:bg-white/10",
        isActive && "bg-white/15 text-white border-l-[3px] border-secondary-400 ml-0 pl-[9px]",
        isCollapsed && "justify-center px-0"
      )}
    >
      <Icon className="h-5 w-5 shrink-0" strokeWidth={1.5} />
      {!isCollapsed && (
        <>
          <span className="text-sm font-medium flex-1">{item.title}</span>
          {item.badge && (
            <span className="min-w-5 h-5 flex items-center justify-center px-1.5 rounded-full bg-red-500 text-white text-xs font-semibold">
              {item.badge}
            </span>
          )}
        </>
      )}
    </Link>
  )

  if (isCollapsed) {
    return (
      <Tooltip delayDuration={0}>
        <TooltipTrigger asChild>{content}</TooltipTrigger>
        <TooltipContent side="right" className="flex items-center gap-2">
          {item.title}
          {item.badge && (
            <span className="min-w-5 h-5 flex items-center justify-center px-1.5 rounded-full bg-red-500 text-white text-xs font-semibold">
              {item.badge}
            </span>
          )}
        </TooltipContent>
      </Tooltip>
    )
  }

  return content
}

export function Sidebar() {
  const pathname = usePathname()
  const { isCollapsed } = useSidebarStore()

  return (
    <TooltipProvider>
      <aside
        className={cn(
          "fixed left-0 top-16 h-[calc(100vh-64px)] bg-primary-500 transition-all duration-300 z-fixed",
          isCollapsed ? "w-[72px]" : "w-[280px]"
        )}
      >
        <ScrollArea className="h-full sidebar-scroll">
          <div className="flex flex-col h-full p-3">
            {/* Navigation Sections */}
            <nav className="flex-1 space-y-6">
              {navSections.map((section, idx) => (
                <div key={section.title}>
                  {!isCollapsed && (
                    <h3 className="px-3 mb-2 text-[11px] font-semibold uppercase tracking-wider text-white/50">
                      {section.title}
                    </h3>
                  )}
                  {isCollapsed && idx > 0 && (
                    <div className="mx-3 my-2 border-t border-white/10" />
                  )}
                  <div className="space-y-1">
                    {section.items.map((item) => (
                      <NavItemComponent
                        key={item.href}
                        item={item}
                        isCollapsed={isCollapsed}
                        isActive={pathname === item.href || pathname.startsWith(item.href + "/")}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </nav>

            {/* Bottom Section */}
            <div className="mt-auto pt-4 border-t border-white/10">
              <div className="space-y-1">
                {bottomNavItems.map((item) => (
                  <NavItemComponent
                    key={item.href}
                    item={item}
                    isCollapsed={isCollapsed}
                    isActive={pathname === item.href}
                  />
                ))}
              </div>

              {/* User Profile */}
              <div
                className={cn(
                  "mt-4 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors cursor-pointer",
                  isCollapsed && "p-2 flex justify-center"
                )}
              >
                {isCollapsed ? (
                  <Tooltip delayDuration={0}>
                    <TooltipTrigger asChild>
                      <Avatar className="h-8 w-8">
                        <AvatarImage src="/avatar.svg" alt="User" />
                        <AvatarFallback className="bg-secondary-400 text-white text-xs">
                          JS
                        </AvatarFallback>
                      </Avatar>
                    </TooltipTrigger>
                    <TooltipContent side="right">
                      <div>
                        <p className="font-medium">John Smith</p>
                        <p className="text-xs text-neutral-500">Compliance Analyst</p>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                ) : (
                  <div className="flex items-center gap-3">
                    <Avatar className="h-9 w-9">
                      <AvatarImage src="/avatar.svg" alt="User" />
                      <AvatarFallback className="bg-secondary-400 text-white text-sm">
                        JS
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">
                        John Smith
                      </p>
                      <p className="text-xs text-white/60 truncate">
                        Compliance Analyst
                      </p>
                    </div>
                    <ChevronDown className="h-4 w-4 text-white/40" />
                  </div>
                )}
              </div>
            </div>
          </div>
        </ScrollArea>
      </aside>
    </TooltipProvider>
  )
}
