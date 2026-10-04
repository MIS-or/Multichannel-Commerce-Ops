import type React from "react"

/**
 * MetricCard — No icon variant.
 * Design principle: Numbers first, label second, context third.
 * Icon is removed entirely — color bar on the left communicates category.
 */
export interface MetricCardProps {
  /** Short label above the number */
  label: string
  /** Primary metric value (big number) */
  value: string | number
  /** One-line explanation of what this number means (context) */
  description?: string
  /** Optional sub-metric: a secondary value shown below description */
  subValue?: string
  /** Deprecated alias for description — kept for backward compatibility */
  hint?: string
  /** Accent color for left border: 'default' | 'success' | 'warning' | 'danger' | 'info' */
  accent?: 'default' | 'success' | 'warning' | 'danger' | 'info'
  /** Text color class for the primary value */
  valueClassName?: string
  className?: string
  /** Optional: render the card as a clickable element */
  onClick?: () => void
  /** @deprecated Use description instead */
  icon?: unknown
  /** @deprecated Use accent instead */
  iconClassName?: string
}

const ACCENT_CLASSES: Record<string, string> = {
  default: 'border-l-gray-300',
  success: 'border-l-emerald-500',
  warning: 'border-l-amber-500',
  danger:  'border-l-red-500',
  info:    'border-l-blue-500',
}

export function MetricCard({
  label,
  value,
  description,
  subValue,
  hint,
  accent = 'default',
  valueClassName = 'text-gray-900',
  className = '',
  onClick,
}: MetricCardProps) {
  const context = description || hint
  const borderClass = ACCENT_CLASSES[accent] ?? ACCENT_CLASSES.default

  const content = (
    <>
      {/* Label */}
      <p className="text-xs font-medium text-text-secondary uppercase tracking-wide mb-2.5">
        {label}
      </p>

      {/* Primary value */}
      <p className={`text-2xl font-bold tabular-nums leading-none mb-1.5 ${valueClassName}`}>
        {value}
      </p>

      {/* Context explanation */}
      {context && (
        <p className="text-[11px] text-text-muted leading-relaxed">{context}</p>
      )}

      {/* Optional sub-value */}
      {subValue && (
        <p className="text-xs text-text-secondary mt-1 font-mono tabular-nums">{subValue}</p>
      )}
    </>
  )

  const baseClass = `bg-white border border-border border-l-4 ${borderClass} rounded-xl px-5 py-4 shadow-xs transition-colors ${className}`

  if (onClick) {
    return (
      <button
        type="button"
        onClick={onClick}
        className={`${baseClass} text-left w-full hover:border-l-primary-400 hover:shadow-sm cursor-pointer`}
      >
        {content}
      </button>
    )
  }

  return <div className={baseClass}>{content}</div>
}
