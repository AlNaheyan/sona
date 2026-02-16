"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
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
const PAGE_SIZE = 5;
const SKELETON_COUNT = PAGE_SIZE;

type ModalAlbum = NonNullable<AlbumDetailModalProps["album"]>;

export default function RecommendationsPage() {
  const [meta, setMeta] = useState<Omit<RecommendationsResponse, "recommendations"> | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedAlbum, setSelectedAlbum] = useState<ModalAlbum | null>(null);
  const [visible, setVisible] = useState<RecommendedAlbum[]>([]);

  // Buffer holds the full payload; pageIndex tracks current window
  const bufferRef = useRef<RecommendedAlbum[]>([]);
  const pageIndexRef = useRef(0);

  const fetchRecs = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await apiFetch<RecommendationsResponse>(
        "/api/v1/recommendations?limit=20&include_reasons=true"
      );
      const { recommendations, ...rest } = res;
      bufferRef.current = recommendations;
      pageIndexRef.current = 0;
      setMeta(rest);
      setVisible(recommendations.slice(0, PAGE_SIZE));
    } catch {
      bufferRef.current = [];
      pageIndexRef.current = 0;
      setMeta(null);
      setVisible([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRecs();
  }, [fetchRecs]);

  const handleRefresh = async () => {
    const buffer = bufferRef.current;
    const nextStart = (pageIndexRef.current + 1) * PAGE_SIZE;

    if (nextStart < buffer.length) {
      // Still have unseen albums in the buffer — show next page
      pageIndexRef.current += 1;
      const end = Math.min(nextStart + PAGE_SIZE, buffer.length);
      setVisible(buffer.slice(nextStart, end));
    } else {
      // Buffer exhausted — fetch new recommendations
      await fetchRecs();
    }
  };

  const hasData = meta && visible.length > 0;

  return (
    <div className="max-w-4xl mx-auto px-8 py-16">
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-serif text-3xl tracking-tight">Discover</h1>
        {hasData && (
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
      {hasData && (
        <p className="font-mono text-[10px] text-silver-dark/60 mb-6">
          {meta.user_ranked_albums} albums ranked
          {meta.similar_users_found > 0 &&
            ` \u00b7 ${meta.similar_users_found} similar users found`}
          {meta.exploration_count > 0 &&
            ` \u00b7 ${meta.exploration_count} exploration picks`}
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
      {!isLoading && !hasData && (
        <EmptyState
          icon={Compass}
          heading="Not enough data yet."
          description="Rate at least 5 albums to get personalized recommendations."
          actionLabel="Start Rating"
          actionHref="/search"
        />
      )}

      {/* Recommendations list */}
      {!isLoading && hasData && (
        <AnimatePresence mode="wait">
          <motion.div
            key={pageIndexRef.current}
            className="space-y-2"
            variants={stagger}
            initial="hidden"
            animate="show"
            exit="hidden"
          >
            {visible.map((rec) => (
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
        </AnimatePresence>
      )}

      <AlbumDetailModal
        album={selectedAlbum}
        onClose={() => setSelectedAlbum(null)}
      />
    </div>
  );
}
