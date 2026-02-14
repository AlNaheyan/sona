"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { Compass, Sparkles, RefreshCw } from "lucide-react";
import { stagger, fadeUp } from "@/components/motion";
import { AlbumCover } from "@/components/album-cover";
import { AlbumDetailModal, type AlbumDetailModalProps } from "@/components/album-detail-modal";
import { EmptyState } from "@/components/empty-state";
import { apiFetch } from "@/lib/api";

/* ─── Types ─── */
interface RecommendedAlbum {
  album_id: string;
  mbid: string | null;
  title: string;
  artist_name: string | null;
  cover_url: string | null;
  release_year: number | null;
  genres: string | null;
  final_score: number;
  is_exploration: boolean;
  reasons: string[];
  community_rating_count: number;
  community_bayesian_score: number | null;
}

interface RecommendationsResponse {
  recommendations: RecommendedAlbum[];
  count: number;
  user_ranked_albums: number;
  recommendation_type: string;
  similar_users_found: number;
  exploration_count: number;
}

/* ─── Constants ─── */
const SKELETON_COUNT = 8;

type ModalAlbum = NonNullable<AlbumDetailModalProps["album"]>;

export default function RecommendationsPage() {
  const [data, setData] = useState<RecommendationsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedAlbum, setSelectedAlbum] = useState<ModalAlbum | null>(null);

  const fetchRecs = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await apiFetch<RecommendationsResponse>(
        "/api/v1/recommendations?limit=20&include_reasons=true"
      );
      setData(res);
    } catch {
      setData(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRecs();
  }, [fetchRecs]);

  const handleRefresh = () => {
    fetchRecs();
  };

  return (
    <div className="max-w-4xl mx-auto px-8 py-16">
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-serif text-3xl tracking-tight">Discover</h1>
        {data && data.count > 0 && (
          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="flex items-center gap-1.5 font-mono text-[10px] tracking-widest uppercase text-silver-dark hover:text-foreground transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3 h-3 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        )}
      </div>

      {/* Meta info */}
      {data && data.count > 0 && (
        <p className="font-mono text-[10px] text-silver-dark/60 mb-6">
          {data.user_ranked_albums} albums ranked
          {data.similar_users_found > 0 &&
            ` \u00b7 ${data.similar_users_found} similar users found`}
          {data.exploration_count > 0 &&
            ` \u00b7 ${data.exploration_count} exploration picks`}
        </p>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="space-y-2">
          {Array.from({ length: SKELETON_COUNT }).map((_, i) => (
            <div
              key={i}
              className="flex items-center gap-3 p-3 rounded-xl border border-silver-light/30 animate-pulse"
            >
              <div className="w-12 h-12 bg-silver-light/30 rounded-lg shrink-0" />
              <div className="flex-1 space-y-2">
                <div className="h-3 w-32 bg-silver-light/30 rounded" />
                <div className="h-2 w-20 bg-silver-light/30 rounded" />
              </div>
              <div className="h-2 w-8 bg-silver-light/30 rounded shrink-0" />
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && (!data || data.count === 0) && (
        <EmptyState
          icon={Compass}
          heading="Not enough data yet."
          description="Rate at least 5 albums to get personalized recommendations."
          actionLabel="Start Rating"
          actionHref="/search"
        />
      )}

      {/* Recommendations list */}
      {!isLoading && data && data.count > 0 && (
        <motion.div
          className="space-y-2"
          variants={stagger}
          initial="hidden"
          animate="show"
        >
          {data.recommendations.map((rec) => (
            <motion.div
              key={rec.album_id}
              variants={fadeUp}
              onClick={() => {
                if (!rec.mbid) return;
                setSelectedAlbum({
                  mbid: rec.mbid,
                  title: rec.title,
                  artist_name: rec.artist_name || "Unknown Artist",
                  release_year: rec.release_year,
                  cover_url: rec.cover_url,
                });
              }}
              className="flex items-center gap-3 p-3 rounded-xl border border-silver-light/30 hover:border-silver-light/60 transition-colors duration-200 cursor-pointer"
            >
              <AlbumCover
                title={rec.title}
                coverUrl={rec.cover_url}
              />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <p className="font-serif text-sm tracking-tight truncate">
                    {rec.title}
                  </p>
                  {rec.is_exploration && (
                    <Sparkles className="w-3 h-3 text-amber-500 shrink-0" />
                  )}
                </div>
                <p className="font-mono text-[10px] text-silver-dark truncate">
                  {rec.artist_name || "Unknown Artist"}
                </p>
                {rec.reasons.length > 0 && (
                  <p className="font-mono text-[9px] text-silver-dark/50 truncate mt-0.5">
                    {rec.reasons[0]}
                  </p>
                )}
              </div>
              <div className="flex flex-col items-end gap-0.5 shrink-0 mr-1">
                {rec.release_year && (
                  <span className="font-mono text-[10px] text-silver-dark">
                    {rec.release_year}
                  </span>
                )}
                {rec.community_bayesian_score != null && (
                  <span className="font-mono text-[10px] text-silver-dark/50">
                    {rec.community_bayesian_score.toFixed(1)}
                  </span>
                )}
              </div>
            </motion.div>
          ))}
        </motion.div>
      )}

      <AlbumDetailModal
        album={selectedAlbum}
        onClose={() => setSelectedAlbum(null)}
      />
    </div>
  );
}
