"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { useAuth } from "@/contexts/auth";
import { apiFetch } from "@/lib/api";
import { stagger } from "@/components/motion";
import { DashboardHeader } from "./sections/dashboard-header";
import { QuickStats } from "./sections/quick-stats";
import { FeaturedLists } from "./sections/featured-lists";
import { Recommendations } from "./sections/recommendations";
import { Trending } from "./sections/trending";

/* ─── Types ─── */
interface RankingStats {
  ranked_albums: number;
  numeric_ratings: number;
  pairwise_comparisons: number;
  average_elo: number;
  elo_range: { min: number; max: number };
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<RankingStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);

  const fetchStats = useCallback(async () => {
    setStatsLoading(true);
    try {
      const data = await apiFetch<RankingStats>("/api/v1/rankings/stats");
      setStats(data);
    } catch {
      setStats(null);
    } finally {
      setStatsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user) {
      fetchStats();
    }
  }, [user, fetchStats]);

  return (
    <div className="max-w-4xl mx-auto px-8 py-16">
      <motion.div variants={stagger} initial="hidden" animate="show">
        <DashboardHeader
          username={user?.username || "music lover"}
          stats={stats}
        />
        <QuickStats stats={stats} isLoading={statsLoading} />
        <FeaturedLists />
        <Recommendations />
        <Trending />
      </motion.div>
    </div>
  );
}
