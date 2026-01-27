import { ReactNode } from "react"

interface PageHeaderProps {
  title: string
  description?: string
  lastUpdated?: string
  actions?: ReactNode
}

export function PageHeader({
  title,
  description,
  lastUpdated,
  actions,
}: PageHeaderProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
      <div>
        <h1 className="text-2xl font-bold text-neutral-900">{title}</h1>
        {description && (
          <p className="mt-1 text-sm text-neutral-500">{description}</p>
        )}
        {lastUpdated && (
          <p className="mt-2 text-xs text-neutral-400">
            Last updated: {lastUpdated}
          </p>
        )}
      </div>
      {actions && <div className="flex items-center gap-3">{actions}</div>}
    </div>
  )
}
