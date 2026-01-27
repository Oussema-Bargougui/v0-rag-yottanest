import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary-500 text-white",
        secondary:
          "border-transparent bg-neutral-100 text-neutral-900",
        outline: "text-neutral-700 border-neutral-300",
        success:
          "border-transparent bg-green-100 text-green-700",
        warning:
          "border-transparent bg-amber-100 text-amber-700",
        destructive:
          "border-transparent bg-red-100 text-red-700",
        // Risk level badges
        critical:
          "border-red-200 bg-red-100 text-red-700",
        high:
          "border-orange-200 bg-orange-100 text-orange-700",
        medium:
          "border-yellow-200 bg-yellow-100 text-yellow-700",
        low:
          "border-green-200 bg-green-100 text-green-700",
        clear:
          "border-teal-200 bg-teal-100 text-teal-700",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
