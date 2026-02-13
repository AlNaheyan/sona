"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { Trophy, TrendingUp } from "lucide-react";
import { stagger, fadeUp } from "@/components/motion";
import { AlbumCover } from "@/components/album-cover";
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
  rating_count: number;
  comparison_count: number;
}

interface RankingsResponse {
  rankings: RankedAlbum[];
  count: number;
}

/* ─── Constants ─── */
const PAGE_SIZE = 50;
const SKELETON_COUNT = 8;

type Tab = "listened" | "want-to-listen";

export default function RankingsPage() {
  const [tab, setTab] = useState<Tab>("listened");
  const [albums, setAlbums] = useState<RankedAlbum[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);

  useEffect(() => {
    setIsLoading(true);
    apiFetch<RankingsResponse>(`/api/v1/rankings?limit=${PAGE_SIZE}`)
      .then((data) => {
        setAlbums(data.rankings);
        setHasMore(data.count === PAGE_SIZE);
      })
      .catch(() => {
        setAlbums([]);
        setHasMore(false);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const loadMore = useCallback(() => {
    setIsLoadingMore(true);
    apiFetch<RankingsResponse>(
      `/api/v1/rankings?limit=${PAGE_SIZE}&offset=${albums.length}`
    )
      .then((data) => {
        setAlbums((prev) => [...prev, ...data.rankings]);
        setHasMore(data.count === PAGE_SIZE);
      })
      .catch(() => setHasMore(false))
      .finally(() => setIsLoadingMore(false));
  }, [albums.length]);

  return (
    <div className="max-w-4xl mx-auto px-8 py-16">
      <h1 className="font-serif text-3xl tracking-tight mb-6">My Ranking</h1>

      {/* Tab bar */}
      <div className="flex gap-6 border-b border-silver-light/30 mb-6">
        <button
          onClick={() => setTab("listened")}
          className={`font-mono text-sm pb-2 transition-colors ${
            tab === "listened"
              ? "text-foreground border-b-2 border-foreground"
              : "text-silver-dark hover:text-foreground"
          }`}
        >
          Listened
        </button>
        <button
          onClick={() => setTab("want-to-listen")}
          className={`font-mono text-sm pb-2 transition-colors ${
            tab === "want-to-listen"
              ? "text-foreground border-b-2 border-foreground"
              : "text-silver-dark hover:text-foreground"
          }`}
        >
          Want to Listen
        </button>
      </div>

      {/* Tab content */}
      {tab === "listened" ? (
        <ListenedTab
          albums={albums}
          isLoading={isLoading}
          isLoadingMore={isLoadingMore}
          hasMore={hasMore}
          onLoadMore={loadMore}
        />
      ) : (
        <EmptyState
          heading="Coming soon"
          description="Save albums you want to listen to."
        />
      )}
    </div>
  );
}

/* ─── Listened Tab ─── */
interface ListenedTabProps {
  albums: RankedAlbum[];
  isLoading: boolean;
  isLoadingMore: boolean;
  hasMore: boolean;
  onLoadMore: () => void;
}

function ListenedTab({
  albums,
  isLoading,
  isLoadingMore,
  hasMore,
  onLoadMore,
}: ListenedTabProps) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: SKELETON_COUNT }).map((_, i) => (
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
    );
  }

  if (albums.length === 0) {
    return (
      <EmptyState
        icon={Trophy}
        heading="No ranked albums yet."
        description="Rate and compare albums to build your personal ranking."
        actionLabel="Start Ranking"
        actionHref="/dashboard"
      />
    );
  }

  return (
    <>
      <motion.div
        className="space-y-2"
        variants={stagger}
        initial="hidden"
        animate="show"
      >
        {albums.map((album) => (
          <motion.div
            key={album.album_id}
            variants={fadeUp}
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
            <div className="flex items-center gap-1.5 shrink-0 mr-1">
              <TrendingUp className="w-3 h-3 text-foreground/40" />
              <span className="font-mono text-xs font-normal text-foreground/80 tabular-nums">
                {Math.round(album.elo)}
              </span>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {hasMore && (
        <div className="flex justify-center mt-6">
          <button
            onClick={onLoadMore}
            disabled={isLoadingMore}
            className="font-mono text-xs tracking-widest uppercase py-2.5 px-8 border border-silver-light rounded-full hover:border-foreground transition-colors disabled:opacity-50"
          >
            {isLoadingMore ? "Loading..." : "Load more"}
          </button>
        </div>
      )}
    </>
  );
}
