"use client"

import { ReactNode } from "react"
import { TopNavbar } from "./top-navbar"
import { Sidebar } from "./sidebar"
import { useSidebarStore } from "@/store/sidebar-store"
import { cn } from "@/lib/utils"

interface DashboardLayoutProps {
  children: ReactNode
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const { isCollapsed } = useSidebarStore()

  return (
    <div className="min-h-screen bg-neutral-50">
      <TopNavbar />
      <Sidebar />
      <main
        className={cn(
          "pt-16 min-h-screen transition-all duration-300",
          isCollapsed ? "ml-[72px]" : "ml-[280px]"
        )}
      >
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  )
}
