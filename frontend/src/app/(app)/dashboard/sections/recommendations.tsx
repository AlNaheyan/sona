"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { fadeUp } from "@/components/motion";
import { AlbumCover } from "@/components/album-cover";
import { SectionLabel } from "@/components/section-label";
import { EmptyState } from "@/components/empty-state";
import { apiFetch } from "@/lib/api";

/* ─── Types ─── */
interface RecommendedAlbum {
  album_id: string;
  title: string;
  artist_name: string | null;
  cover_url: string | null;
  release_year: number | null;
  final_score: number;
  is_exploration: boolean;
  reasons: string[];
}

interface RecommendationsResponse {
  recommendations: RecommendedAlbum[];
  count: number;
  user_ranked_albums: number;
}

export function Recommendations() {
  const [recs, setRecs] = useState<RecommendedAlbum[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [tooFew, setTooFew] = useState(false);

  useEffect(() => {
    apiFetch<RecommendationsResponse>(
      "/api/v1/recommendations?limit=5&include_reasons=true"
    )
      .then((data) => {
        setRecs(data.recommendations);
        if (data.recommendations.length === 0 && data.user_ranked_albums < 10) {
          setTooFew(true);
        }
      })
      .catch(() => setRecs([]))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return (
      <motion.div variants={fadeUp} className="mb-10">
        <SectionLabel className="mb-3">Recommended for You</SectionLabel>
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="flex items-center gap-3 p-3 rounded-xl border border-silver-light/30 animate-pulse"
            >
              <div className="w-12 h-12 bg-silver-light/30 rounded-lg shrink-0" />
              <div className="flex-1 space-y-2">
                <div className="h-3 w-28 bg-silver-light/30 rounded" />
                <div className="h-2 w-20 bg-silver-light/30 rounded" />
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div variants={fadeUp} className="mb-10">
      <SectionLabel className="mb-3">Recommended for You</SectionLabel>

      {recs.length > 0 ? (
        <div className="space-y-2">
          {recs.map((rec) => {
            const matchPct = Math.round(rec.final_score * 100);
            return (
              <div
                key={rec.album_id}
                className="flex items-center gap-3 p-3 rounded-xl border border-silver-light/30 hover:border-silver-light/60 transition-colors duration-200"
              >
                <AlbumCover
                  title={rec.title}
                  coverUrl={rec.cover_url}
                />
                <div className="min-w-0 flex-1">
                  <p className="font-serif text-sm tracking-tight truncate">
                    {rec.title}
                  </p>
                  <p className="font-mono text-[10px] text-silver-dark truncate">
                    {rec.artist_name || "Unknown Artist"}
                    {rec.release_year ? ` · ${rec.release_year}` : ""}
                  </p>
                  {rec.reasons.length > 0 && (
                    <p className="font-mono text-[10px] text-silver truncate mt-0.5">
                      {rec.reasons[0]}
                    </p>
                  )}
                </div>
                <div className="flex flex-col items-end gap-1 shrink-0">
                  <span className="font-mono text-[10px] text-silver-dark">
                    {matchPct}%
                  </span>
                  {rec.is_exploration && (
                    <span className="font-mono text-[8px] tracking-wider uppercase py-0.5 px-2 rounded-full bg-silver-light/20 text-silver-dark">
                      Explore
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <EmptyState
          icon={Sparkles}
          heading={tooFew ? "Almost there." : "No recommendations yet."}
          description={
            tooFew
              ? "Rate at least 10 albums to unlock personalized recommendations."
              : "Start rating albums to get recommendations."
          }
          actionLabel="Rate Albums"
          actionHref="/onboarding"
        />
      )}
    </motion.div>
  );
}
