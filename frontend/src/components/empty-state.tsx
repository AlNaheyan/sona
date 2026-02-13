import type { LucideIcon } from "lucide-react";
import Link from "next/link";

interface EmptyStateProps {
  icon?: LucideIcon;
  heading: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
}

export function EmptyState({
  icon: Icon,
  heading,
  description,
  actionLabel,
  actionHref,
  onAction,
}: EmptyStateProps) {
  return (
    <div className="border border-dashed border-silver-light/40 rounded-2xl p-8 text-center">
      {Icon && <Icon className="w-5 h-5 text-silver-light mx-auto mb-2" />}
      <p className="font-serif text-base tracking-tight mb-1">{heading}</p>
      <p className="font-mono text-[10px] text-silver-dark mb-4">
        {description}
      </p>
      {actionLabel && actionHref && (
        <Link
          href={actionHref}
          className="inline-block font-mono text-xs tracking-widest uppercase py-2.5 px-8 bg-foreground text-cream rounded-full hover:shadow-[0_8px_30px_rgba(0,0,0,0.12)] transition-shadow duration-300"
        >
          {actionLabel}
        </Link>
      )}
      {actionLabel && onAction && !actionHref && (
        <button
          onClick={onAction}
          className="font-mono text-xs tracking-widest uppercase py-2.5 px-8 bg-foreground text-cream rounded-full hover:shadow-[0_8px_30px_rgba(0,0,0,0.12)] transition-shadow duration-300"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
