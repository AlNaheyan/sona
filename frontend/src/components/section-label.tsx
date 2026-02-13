interface SectionLabelProps {
  children: React.ReactNode;
  className?: string;
}

export function SectionLabel({ children, className = "" }: SectionLabelProps) {
  return (
    <p
      className={`font-mono text-[10px] tracking-[0.2em] uppercase text-silver-dark ${className}`}
    >
      {children}
    </p>
  );
}
