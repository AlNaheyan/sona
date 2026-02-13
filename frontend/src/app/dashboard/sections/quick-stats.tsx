"use client";

import { motion } from "framer-motion";
import { fadeUp } from "@/components/motion";

interface RankingStats {
  ranked_albums: number;
  numeric_ratings: number;
  pairwise_comparisons: number;
  average_elo: number;
  elo_range: { min: number; max: number };
}

interface QuickStatsProps {
  stats: RankingStats | null;
  isLoading: boolean;
}

function SkeletonCard() {
  return (
    <div className="border border-silver-light/40 rounded-xl p-5 animate-pulse">
      <div className="h-2.5 w-16 bg-silver-light/30 rounded mb-3" />
      <div className="h-7 w-12 bg-silver-light/30 rounded" />
    </div>
  );
}

export function QuickStats({ stats, isLoading }: QuickStatsProps) {
  if (isLoading) {
    return (
      <motion.div variants={fadeUp} className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </motion.div>
    );
  }

  const albums = stats?.ranked_albums ?? 0;
  const comparisons = stats?.pairwise_comparisons ?? 0;
  const avgElo = stats && albums > 0 ? Math.round(stats.average_elo) : "--";
  const eloRange =
    stats && albums > 0
      ? `${Math.round(stats.elo_range.min)}–${Math.round(stats.elo_range.max)}`
      : "--";

  const cards = [
    { label: "Albums Ranked", value: albums || "--" },
    { label: "Comparisons", value: comparisons || "--" },
    { label: "Avg Elo", value: avgElo },
    { label: "Elo Range", value: eloRange },
  ];

  return (
    <motion.div variants={fadeUp} className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
      {cards.map((card) => (
        <div
          key={card.label}
          className="border border-silver-light/40 rounded-xl p-5"
        >
          <p className="font-mono text-[10px] tracking-[0.2em] uppercase text-silver-dark mb-1">
            {card.label}
          </p>
          <p className="font-serif text-2xl tracking-tight">{card.value}</p>
        </div>
      ))}
    </motion.div>
  );
}
