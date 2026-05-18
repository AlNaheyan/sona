"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { Trophy, TrendingUp } from "lucide-react";
import { stagger, fadeUp } from "@/components/motion";
import { AlbumCover } from "@/components/album-cover";
import { EmptyState } from "@/components/empty-state";
import { apiFetch } from "@/lib/api";

/* ─── Types ─── */
interface CommunityAlbum {
  rank: number;
  id: string;
  mbid: string | null;
  title: string;
  artist_name: string | null;
  cover_url: string | null;
  release_year: number | null;
  rating_count: number;
  average_rating: number;
  bayesian_score: number;
}

interface CommunityRankingsResponse {
  rankings: CommunityAlbum[];
  total: number;
  limit: number;
  offset: number;
}

interface TrendingAlbum {
  id: string;
  mbid: string | null;
  title: string;
  artist_name: string | null;
  cover_url: string | null;
  rating_count: number;
  average_rating: number;
}

interface TrendingResponse {
  trending: TrendingAlbum[];
  count: number;
}

interface CommunityStats {
  total_ratings: number;
  rated_albums: number;
  global_mean_rating: number;
  top_album: { title: string; artist: string | null; bayesian_score: number | null } | null;
}

const PAGE_SIZE = 25;
const SKELETON_COUNT = 10;

type Tab = "rankings" | "trending";

export default function CommunityPage() {
  const [tab, setTab] = useState<Tab>("rankings");
  const [rankings, setRankings] = useState<CommunityAlbum[]>([]);
  const [trending, setTrending] = useState<TrendingAlbum[]>([]);
  const [stats, setStats] = useState<CommunityStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);

  const fetchRankings = useCallback(async (offset = 0, append = false) => {
    if (offset === 0) setIsLoading(true);
    else setIsLoadingMore(true);
    try {
      const data = await apiFetch<CommunityRankingsResponse>(
        `/api/v1/community/rankings?limit=${PAGE_SIZE}&offset=${offset}`
      );
      if (append) {
        setRankings((prev) => [...prev, ...data.rankings]);
      } else {
        setRankings(data.rankings);
      }
      setHasMore(data.rankings.length === PAGE_SIZE);
    } catch {
      if (!append) setRankings([]);
    } finally {
      setIsLoading(false);
      setIsLoadingMore(false);
    }
  }, []);

  const fetchTrending = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await apiFetch<TrendingResponse>("/api/v1/community/trending?limit=20");
      setTrending(data.trending);
    } catch {
      setTrending([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    apiFetch<CommunityStats>("/api/v1/community/stats")
      .then(setStats)
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (tab === "rankings") fetchRankings(0);
    else fetchTrending();
  }, [tab, fetchRankings, fetchTrending]);

  const loadMore = useCallback(() => {
    fetchRankings(rankings.length, true);
  }, [rankings.length, fetchRankings]);

  return (
    <div className="max-w-4xl mx-auto px-8 py-16">
      <motion.div variants={stagger} initial="hidden" animate="show">
        {/* Header */}
        <motion.div variants={fadeUp} className="mb-10">
          <h1 className="font-serif text-3xl tracking-tight mb-1">Community</h1>
          <p className="font-mono text-sm text-silver-dark">
            Global rankings based on Bayesian-weighted scores.
          </p>
        </motion.div>

        {/* Stats strip */}
        {stats && (
          <motion.div
            variants={fadeUp}
            className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-10"
          >
            {[
              { label: "Albums Rated", value: stats.rated_albums.toLocaleString() },
              { label: "Total Ratings", value: stats.total_ratings.toLocaleString() },
              { label: "Avg Rating", value: stats.global_mean_rating.toFixed(1) },
            ].map(({ label, value }) => (
              <div
                key={label}
                className="border border-silver-light/40 rounded-xl p-4 text-center"
              >
                <p className="font-mono text-xs text-silver-dark mb-1">{label}</p>
                <p className="font-serif text-xl tracking-tight">{value}</p>
              </div>
            ))}
          </motion.div>
        )}

        {/* Tabs */}
        <motion.div variants={fadeUp} className="flex gap-6 mb-8 border-b border-silver-light/30">
          {(["rankings", "trending"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`pb-3 font-mono text-xs uppercase tracking-widest transition-colors ${
                tab === t
                  ? "border-b-2 border-zinc-900 text-zinc-900"
                  : "text-silver-dark hover:text-zinc-700"
              }`}
            >
              {t === "rankings" ? "All-Time Rankings" : "Trending"}
            </button>
          ))}
        </motion.div>

        {/* List */}
        {isLoading ? (
          <motion.div variants={fadeUp} className="space-y-3">
            {Array.from({ length: SKELETON_COUNT }).map((_, i) => (
              <div key={i} className="flex items-center gap-4 p-3 rounded-xl animate-pulse">
                <div className="w-8 shrink-0 h-4 bg-silver-light/30 rounded" />
                <div className="w-12 h-12 rounded-lg bg-silver-light/30 shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="h-3 bg-silver-light/30 rounded w-48" />
                  <div className="h-2 bg-silver-light/20 rounded w-32" />
                </div>
                <div className="h-3 bg-silver-light/20 rounded w-12" />
              </div>
            ))}
          </motion.div>
        ) : tab === "rankings" && rankings.length === 0 ? (
          <motion.div variants={fadeUp}>
            <EmptyState
              icon={Trophy}
              heading="No albums ranked yet."
              description="Be the first to rate albums and shape the community rankings."
              actionLabel="Search Albums"
              actionHref="/search"
            />
          </motion.div>
        ) : tab === "trending" && trending.length === 0 ? (
          <motion.div variants={fadeUp}>
            <EmptyState
              icon={TrendingUp}
              heading="Nothing trending yet."
              description="Rate more albums to surface community trends."
              actionLabel="Search Albums"
              actionHref="/search"
            />
          </motion.div>
        ) : tab === "rankings" ? (
          <motion.div variants={fadeUp} className="space-y-1">
            {rankings.map((album) => (
              <div
                key={album.id}
                className="flex items-center gap-4 px-3 py-3 rounded-xl hover:bg-silver-light/10 transition-colors"
              >
                <span className="w-8 shrink-0 font-mono text-xs text-silver-dark text-right">
                  {album.rank}
                </span>
                <AlbumCover title={album.title} coverUrl={album.cover_url} size="sm" className="shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-serif text-sm tracking-tight truncate">{album.title}</p>
                  <p className="font-mono text-[10px] text-silver-dark truncate">
                    {album.artist_name || "Unknown Artist"}
                    {album.release_year ? ` · ${album.release_year}` : ""}
                  </p>
                </div>
                <div className="text-right shrink-0">
                  <p className="font-mono text-sm">{album.bayesian_score.toFixed(2)}</p>
                  <p className="font-mono text-[10px] text-silver-dark">
                    {album.rating_count} {album.rating_count === 1 ? "rating" : "ratings"}
                  </p>
                </div>
              </div>
            ))}
          </motion.div>
        ) : (
          <motion.div variants={fadeUp} className="space-y-1">
            {trending.map((album, i) => (
              <div
                key={album.id}
                className="flex items-center gap-4 px-3 py-3 rounded-xl hover:bg-silver-light/10 transition-colors"
              >
                <span className="w-8 shrink-0 font-mono text-xs text-silver-dark text-right">
                  {i + 1}
                </span>
                <AlbumCover title={album.title} coverUrl={album.cover_url} size="sm" className="shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-serif text-sm tracking-tight truncate">{album.title}</p>
                  <p className="font-mono text-[10px] text-silver-dark truncate">
                    {album.artist_name || "Unknown Artist"}
                  </p>
                </div>
                <div className="text-right shrink-0">
                  <p className="font-mono text-sm">{album.average_rating.toFixed(1)}</p>
                  <p className="font-mono text-[10px] text-silver-dark">
                    {album.rating_count} {album.rating_count === 1 ? "rating" : "ratings"}
                  </p>
                </div>
              </div>
            ))}
          </motion.div>
        )}

        {/* Load more */}
        {tab === "rankings" && hasMore && !isLoading && (
          <motion.div variants={fadeUp} className="mt-8 flex justify-center">
            <button
              onClick={loadMore}
              disabled={isLoadingMore}
              className="font-mono text-xs uppercase tracking-widest border border-silver-light/40 rounded-full px-6 py-2 hover:bg-silver-light/10 transition-colors disabled:opacity-50"
            >
              {isLoadingMore ? "Loading…" : "Load more"}
            </button>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}
