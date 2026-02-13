interface StatCardProps {
  label: string;
  value: string | number;
  className?: string;
}

export function StatCard({ label, value, className = "" }: StatCardProps) {
  return (
    <div
      className={`border border-silver-light/40 rounded-xl p-5 ${className}`}
    >
      <p className="font-mono text-[10px] tracking-[0.2em] uppercase text-silver-dark mb-1">
        {label}
      </p>
      <p className="font-serif text-2xl tracking-tight">{value}</p>
    </div>
  );
}
