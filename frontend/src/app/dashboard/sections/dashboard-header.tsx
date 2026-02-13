"use client";

import { motion } from "framer-motion";
import { fadeUp } from "@/components/motion";

interface DashboardHeaderProps {
  username: string;
  stats: { ranked_albums: number; pairwise_comparisons: number } | null;
}

export function DashboardHeader({ username, stats }: DashboardHeaderProps) {
  return (
    <motion.div variants={fadeUp} className="mb-10">
      <h1 className="font-serif text-4xl md:text-5xl tracking-tight mb-3">
        Welcome back,{" "}
        <span className="italic">{username}.</span>
      </h1>
      {stats && (
        <p className="font-mono text-sm text-silver-dark">
          {stats.ranked_albums} album{stats.ranked_albums !== 1 ? "s" : ""} ranked
          {stats.pairwise_comparisons > 0 && (
            <> &middot; {stats.pairwise_comparisons} comparison{stats.pairwise_comparisons !== 1 ? "s" : ""}</>
          )}
        </p>
      )}
    </motion.div>
  );
}
