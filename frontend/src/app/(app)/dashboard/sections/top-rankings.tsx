"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Trophy } from "lucide-react";
import Link from "next/link";
import { fadeUp } from "@/components/motion";
import { AlbumCover } from "@/components/album-cover";
import { SectionLabel } from "@/components/section-label";
import { EmptyState } from "@/components/empty-state";
import { apiFetch } from "@/lib/api";

/* ─── Types ─── */
interface RankedAlbum {
  rank: number;
  album_id: string;
  album_title: string;
  album_artist: string | null;
  album_cover_url: string | null;
  elo: number;
  elo_normalized: number;
  rating_count: number;
  comparison_count: number;
}

interface RankingsResponse {
  rankings: RankedAlbum[];
  count: number;
}

interface TopRankingsProps {
  refreshKey: number;
}

export function TopRankings({ refreshKey }: TopRankingsProps) {
  const [albums, setAlbums] = useState<RankedAlbum[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(true);
    apiFetch<RankingsResponse>("/api/v1/rankings?limit=5")
      .then((data) => setAlbums(data.rankings))
      .catch(() => setAlbums([]))
      .finally(() => setIsLoading(false));
  }, [refreshKey]);

  if (isLoading) {
    return (
      <motion.div variants={fadeUp} className="mb-10">
        <SectionLabel className="mb-3">Your Top Rankings</SectionLabel>
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="flex items-center gap-3 p-3 rounded-xl border border-silver-light/30 animate-pulse"
            >
              <div className="w-5 h-3 bg-silver-light/30 rounded shrink-0" />
              <div className="w-12 h-12 bg-silver-light/30 rounded-lg shrink-0" />
              <div className="flex-1 space-y-2">
                <div className="h-3 w-24 bg-silver-light/30 rounded" />
                <div className="h-2 w-16 bg-silver-light/30 rounded" />
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div variants={fadeUp} className="mb-10">
      <div className="flex items-center justify-between mb-3">
        <SectionLabel>Your Top Rankings</SectionLabel>
        {albums.length > 0 && (
          <Link
            href="/rankings"
            className="font-mono text-[10px] tracking-[0.15em] uppercase text-silver-dark hover:text-foreground transition-colors duration-200"
          >
            View all
          </Link>
        )}
      </div>

      {albums.length > 0 ? (
        <div className="space-y-2">
          {albums.map((album) => (
            <div
              key={album.album_id}
              className="flex items-center gap-3 p-3 rounded-xl border border-silver-light/30 hover:border-silver-light/60 transition-colors duration-200"
            >
              <span className="font-mono text-[10px] text-silver-dark w-5 text-right shrink-0">
                {album.rank}
              </span>
              <AlbumCover
                title={album.album_title}
                coverUrl={album.album_cover_url}
              />
              <div className="min-w-0 flex-1">
                <p className="font-serif text-sm tracking-tight truncate">
                  {album.album_title}
                </p>
                <p className="font-mono text-[10px] text-silver-dark truncate">
                  {album.album_artist || "Unknown Artist"}
                </p>
              </div>
              <span className="font-mono text-[10px] text-silver shrink-0">
                {Math.round(album.elo_normalized)}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={Trophy}
          heading="No rankings yet."
          description="Rate and compare albums to build your personal ranking."
          actionLabel="Start Ranking"
          actionHref="/onboarding"
        />
      )}
    </motion.div>
  );
}
