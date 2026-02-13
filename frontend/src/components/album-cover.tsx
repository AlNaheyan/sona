"use client";

import { useState } from "react";

const sizes = {
  xs: { dim: "w-9 h-9", text: "text-[8px]" },
  sm: { dim: "w-12 h-12", text: "text-[10px]" },
  md: { dim: "w-16 h-16", text: "text-xs" },
  lg: { dim: "w-20 h-20", text: "text-sm" },
  xl: { dim: "w-28 h-28", text: "text-base" },
  "2xl": { dim: "w-36 h-36", text: "text-lg" },
  "3xl": { dim: "w-44 h-44", text: "text-xl" },
} as const;

type Size = keyof typeof sizes;

interface AlbumCoverProps {
  title: string;
  coverUrl: string | null | undefined;
  size?: Size;
  className?: string;
}

function getInitials(title: string): string {
  const words = title.split(/\s+/).filter((w) => w.length > 0);
  if (words.length === 0) return "?";
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

export function AlbumCover({
  title,
  coverUrl,
  size = "sm",
  className = "",
}: AlbumCoverProps) {
  const [imgFailed, setImgFailed] = useState(false);
  const { dim, text } = sizes[size];
  const initials = getInitials(title);

  if (coverUrl && !imgFailed) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={coverUrl}
        alt={title}
        className={`${dim} rounded-lg object-cover shrink-0 ${className}`}
        onError={() => setImgFailed(true)}
      />
    );
  }

  return (
    <div
      className={`${dim} rounded-lg bg-linear-to-br from-zinc-700 to-zinc-900 flex items-center justify-center shrink-0 ${className}`}
    >
      <span
        className={`font-serif ${text} text-white/40 italic select-none`}
      >
        {initials}
      </span>
    </div>
  );
}
