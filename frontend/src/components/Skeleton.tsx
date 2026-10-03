import type React from "react"

export interface SkeletonProps {
  className?: string
  style?: React.CSSProperties
}

export function Skeleton({ className = "", style }: SkeletonProps) {
  return (
    <div className={`animate-pulse bg-gray-200 rounded ${className}`} style={style} />
  )
}

export function MetricCardSkeleton() {
  return (
    <div className="bg-white border border-border border-l-4 border-l-gray-200 rounded-xl px-5 py-4 shadow-xs">
      <Skeleton className="w-24 h-3 rounded mb-3" />
      <Skeleton className="w-36 h-7 rounded mb-2" />
      <Skeleton className="w-28 h-2.5 rounded" />
    </div>
  )
}

export function TableRowSkeleton({ cols = 6 }: { cols?: number }) {
  return (
    <tr>
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <Skeleton className="h-3.5 rounded" style={{ width: i === 0 ? "80px" : i === cols - 1 ? "60px" : "120px" }} />
        </td>
      ))}
    </tr>
  )
}

export function ChartSkeleton({ height = 220 }: { height?: number }) {
  return (
    <div className="flex items-end gap-3 px-2" style={{ height }}>
      {[60, 80, 50, 75, 45].map((h, i) => (
        <div key={i} className="flex-1 flex items-end">
          <Skeleton className="w-full rounded-sm" style={{ height: `${h}%` }} />
        </div>
      ))}
    </div>
  )
}
