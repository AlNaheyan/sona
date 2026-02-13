"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { TrendingUp } from "lucide-react";
import { fadeUp } from "@/components/motion";
import { AlbumCover } from "@/components/album-cover";
import { SectionLabel } from "@/components/section-label";
import { apiFetch } from "@/lib/api";

/* ─── Types ─── */
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

export function Trending() {
  const [albums, setAlbums] = useState<TrendingAlbum[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    apiFetch<TrendingResponse>("/api/v1/community/trending?limit=8")
      .then((data) => setAlbums(data.trending))
      .catch(() => setAlbums([]))
      .finally(() => setIsLoading(false));
  }, []);

  // Don't render section at all if no trending data
  if (!isLoading && albums.length === 0) return null;

  return (
    <motion.div variants={fadeUp} className="mb-10">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="w-3.5 h-3.5 text-silver-dark" />
        <SectionLabel>Trending in the Community</SectionLabel>
      </div>

      {isLoading ? (
        <div className="flex gap-4 overflow-x-auto scrollbar-none pb-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="shrink-0 w-36 animate-pulse">
              <div className="w-36 h-36 bg-silver-light/30 rounded-lg mb-2" />
              <div className="h-3 w-24 bg-silver-light/30 rounded mb-1" />
              <div className="h-2 w-16 bg-silver-light/30 rounded" />
            </div>
          ))}
        </div>
      ) : (
        <div className="flex gap-4 overflow-x-auto scrollbar-none pb-2">
          {albums.map((album) => (
            <div key={album.id} className="shrink-0 w-36">
              <AlbumCover
                title={album.title}
                coverUrl={album.cover_url}
                size="2xl"
              />
              <div className="mt-2">
                <p className="font-serif text-sm tracking-tight truncate">
                  {album.title}
                </p>
                <p className="font-mono text-[10px] text-silver-dark truncate">
                  {album.artist_name || "Unknown Artist"}
                </p>
                <p className="font-mono text-[10px] text-silver mt-0.5">
                  {album.average_rating.toFixed(1)} · {album.rating_count} rating{album.rating_count !== 1 ? "s" : ""}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
