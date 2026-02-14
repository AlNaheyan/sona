"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Star, Users, TrendingUp, Hash, BookmarkPlus, BookmarkCheck, Loader2 } from "lucide-react";
import { AlbumCover } from "@/components/album-cover";
import { apiFetch } from "@/lib/api";

/* ─── Types ─── */
interface AlbumDetailData {
  mbid: string;
  title: string;
  artist_name: string;
  release_year: number | null;
  cover_url: string | null;
  genres: string[];
  community_rating_count: number;
  community_average_rating: number | null;
  community_bayesian_score: number | null;
  user_rating: number | null;
  user_elo: number | null;
  user_elo_normalized: number | null;
  user_rank: number | null;
}

interface WishlistCheckResponse {
  in_wishlist: boolean;
  entry_id: string | null;
}

interface WishlistAddResponse {
  id: string;
}

export interface AlbumDetailModalProps {
  album: {
    mbid: string;
    title: string;
    artist_name: string;
    release_year: number | null;
    cover_url: string | null;
  } | null;
  onClose: () => void;
}

/* ─── Stat Card ─── */
function StatCard({
  icon: Icon,
  label,
  value,
  muted = false,
  skeleton = false,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  muted?: boolean;
  skeleton?: boolean;
}) {
  return (
    <div className="flex flex-col items-center gap-1 py-3 px-2 rounded-xl bg-cream-dark/50 border border-silver-light/20">
      <Icon className="w-3.5 h-3.5 text-silver-dark" />
      {skeleton ? (
        <div className="h-4 w-10 bg-silver-light/30 rounded animate-pulse" />
      ) : (
        <span
          className={`font-mono text-sm tabular-nums ${muted ? "text-silver-dark" : "text-foreground"}`}
        >
          {value}
        </span>
      )}
      <span className="font-mono text-[9px] uppercase tracking-widest text-silver-dark">
        {label}
      </span>
    </div>
  );
}

/* ─── Rating Selector ─── */
function RatingSelector({
  selected,
  onSelect,
}: {
  selected: number | null;
  onSelect: (value: number) => void;
}) {
  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => {
        const isSelected = selected === n;
        return (
          <button
            key={n}
            onClick={() => onSelect(n)}
            className={`w-6.5 h-6.5 rounded-full font-mono text-[11px] tabular-nums transition-all duration-150 cursor-pointer ${
              isSelected
                ? "bg-foreground text-cream shadow-sm"
                : "bg-cream-dark/60 text-silver-dark border border-silver-light/30 hover:border-silver-light/60 hover:text-foreground"
            }`}
          >
            {n}
          </button>
        );
      })}
    </div>
  );
}

/* ─── Modal ─── */
export function AlbumDetailModal({ album, onClose }: AlbumDetailModalProps) {
  // Detail API state
  const [detail, setDetail] = useState<AlbumDetailData | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(false);

  // Rating state
  const [selectedRating, setSelectedRating] = useState<number | null>(null);
  const [savedRating, setSavedRating] = useState<number | null>(null);
  const [ratingSaving, setRatingSaving] = useState(false);

  // Wishlist state
  const [inWishlist, setInWishlist] = useState(false);
  const [wishlistEntryId, setWishlistEntryId] = useState<string | null>(null);
  const [wishlistLoading, setWishlistLoading] = useState(false);
  const [wishlistSaving, setWishlistSaving] = useState(false);

  // Track current mbid to avoid stale updates
  const currentMbid = useRef<string | null>(null);

  // Reset all state when album changes
  useEffect(() => {
    if (!album) {
      setDetail(null);
      setDetailError(false);
      setDetailLoading(false);
      setSelectedRating(null);
      setSavedRating(null);
      setInWishlist(false);
      setWishlistEntryId(null);
      currentMbid.current = null;
      return;
    }

    const mbid = album.mbid;
    currentMbid.current = mbid;
    setDetail(null);
    setDetailError(false);
    setSelectedRating(null);
    setSavedRating(null);
    setInWishlist(false);
    setWishlistEntryId(null);

    // Fetch detail (non-blocking — modal renders from props immediately)
    setDetailLoading(true);
    apiFetch<AlbumDetailData>(`/api/v1/albums/${mbid}/detail`)
      .then((data) => {
        if (currentMbid.current !== mbid) return;
        setDetail(data);
        if (data.user_rating != null) {
          const rounded = Math.round(data.user_rating);
          setSelectedRating((prev) => prev ?? rounded);
          setSavedRating(rounded);
        }
      })
      .catch(() => {
        if (currentMbid.current !== mbid) return;
        setDetailError(true);
      })
      .finally(() => {
        if (currentMbid.current !== mbid) return;
        setDetailLoading(false);
      });

    // Fetch wishlist state
    setWishlistLoading(true);
    apiFetch<WishlistCheckResponse>(`/api/v1/wishlist/check?mbid=${mbid}`)
      .then((data) => {
        if (currentMbid.current !== mbid) return;
        setInWishlist(data.in_wishlist);
        setWishlistEntryId(data.entry_id);
      })
      .catch(() => {})
      .finally(() => {
        if (currentMbid.current !== mbid) return;
        setWishlistLoading(false);
      });
  }, [album?.mbid]); // eslint-disable-line react-hooks/exhaustive-deps

  // Save rating (called when user presses Rate button)
  const handleSaveRating = useCallback(async () => {
    if (!album || !selectedRating || ratingSaving) return;
    setRatingSaving(true);
    try {
      await apiFetch("/api/v1/ratings", {
        method: "POST",
        body: JSON.stringify({ mbid: album.mbid, value: selectedRating }),
      });
      setSavedRating(selectedRating);
      // Re-fetch detail so Elo, rank, and community stats update
      apiFetch<AlbumDetailData>(`/api/v1/albums/${album.mbid}/detail`)
        .then((data) => {
          if (currentMbid.current !== album.mbid) return;
          setDetail(data);
        })
        .catch(() => {});
    } catch {
      // keep selection so user can retry
    } finally {
      setRatingSaving(false);
    }
  }, [album, selectedRating, ratingSaving]);

  const ratingDirty = selectedRating != null && selectedRating !== savedRating;

  // Toggle wishlist
  const handleWishlistToggle = useCallback(async () => {
    if (!album || wishlistSaving) return;
    setWishlistSaving(true);

    if (inWishlist && wishlistEntryId) {
      // Optimistic remove
      setInWishlist(false);
      const prevId = wishlistEntryId;
      setWishlistEntryId(null);
      try {
        await apiFetch(`/api/v1/wishlist/${prevId}`, { method: "DELETE" });
      } catch {
        setInWishlist(true);
        setWishlistEntryId(prevId);
      }
    } else {
      // Optimistic add
      setInWishlist(true);
      try {
        const data = await apiFetch<WishlistAddResponse>("/api/v1/wishlist", {
          method: "POST",
          body: JSON.stringify({ mbid: album.mbid }),
        });
        setWishlistEntryId(data.id);
      } catch {
        setInWishlist(false);
        setWishlistEntryId(null);
      }
    }

    setWishlistSaving(false);
  }, [album, inWishlist, wishlistEntryId, wishlistSaving]);

  // Escape key
  useEffect(() => {
    if (!album) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [album, onClose]);

  // Body scroll lock
  useEffect(() => {
    if (album) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [album]);

  // Display values: always from props, enriched from detail
  const displayTitle = album?.title ?? "";
  const displayArtist = album?.artist_name ?? "";
  const displayYear = album?.release_year ?? detail?.release_year ?? null;
  const displayCover = album?.cover_url ?? detail?.cover_url ?? null;

  return (
    <AnimatePresence>
      {album && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm"
          />

          {/* Panel */}
          <motion.div
            initial={{ opacity: 0, y: 32, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 32, scale: 0.97 }}
            transition={{ type: "spring", damping: 28, stiffness: 320 }}
            className="fixed inset-0 z-50 flex items-center justify-center pointer-events-none"
          >
            <div className="relative max-w-[600px] w-full mx-4 rounded-2xl bg-background border border-silver-light/30 shadow-[0_24px_80px_-12px_rgba(0,0,0,0.12)] pointer-events-auto overflow-hidden">
              {/* Close button */}
              <button
                onClick={onClose}
                className="absolute top-3.5 right-3.5 z-10 p-1.5 rounded-lg text-silver-dark hover:text-foreground transition-colors duration-200"
                aria-label="Close"
              >
                <X className="w-4 h-4" />
              </button>

              <div className="p-6 pb-5">
                {/* Side-by-side: Cover left, info right */}
                <div className="flex gap-6">
                  {/* Left — Cover art */}
                  <div className="shrink-0">
                    <AlbumCover
                      title={displayTitle}
                      coverUrl={displayCover}
                      size="3xl"
                    />
                  </div>

                  {/* Right — Info + actions */}
                  <div className="flex-1 min-w-0 pt-0.5">
                    {/* Title + Artist inline */}
                    <div className="flex items-baseline gap-2 pr-6">
                      <h2 className="font-serif text-2xl tracking-tight leading-snug truncate">
                        {displayTitle}
                      </h2>
                      <span className="font-mono text-sm text-silver-dark shrink-0">
                        {displayArtist}
                      </span>
                    </div>
                    {displayYear && (
                      <p className="font-mono text-xs text-silver-dark/70 mt-1">
                        {displayYear}
                      </p>
                    )}

                    {/* Genre pills */}
                    {detail && detail.genres.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-3">
                        {detail.genres.slice(0, 4).map((genre) => (
                          <span
                            key={genre}
                            className="inline-flex items-center font-mono text-[10px] tracking-wide px-2 py-0.5 rounded-full border border-silver-light/40 text-silver-dark bg-cream-dark/40"
                          >
                            {genre}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Rating selector */}
                    <div className="mt-4">
                      <p className="font-mono text-[10px] uppercase tracking-widest text-silver-dark mb-2">
                        Your Rating
                      </p>
                      <RatingSelector
                        selected={selectedRating}
                        onSelect={setSelectedRating}
                      />
                    </div>

                    {/* Action buttons */}
                    <div className="flex gap-2 mt-3">
                      <button
                        onClick={handleSaveRating}
                        disabled={!ratingDirty || ratingSaving}
                        className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg font-mono text-xs tracking-wide transition-all duration-200 ${
                          ratingDirty && !ratingSaving
                            ? "bg-foreground text-cream cursor-pointer hover:shadow-[0_8px_30px_rgba(0,0,0,0.12)]"
                            : "bg-cream-dark/50 border border-silver-light/30 text-silver-dark cursor-not-allowed opacity-50"
                        }`}
                      >
                        {ratingSaving ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Star className="w-3.5 h-3.5" />
                        )}
                        {savedRating != null ? "Update" : "Rate"}
                      </button>
                      <button
                        onClick={handleWishlistToggle}
                        disabled={wishlistSaving || wishlistLoading}
                        className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg font-mono text-xs tracking-wide transition-all duration-200 ${
                          inWishlist
                            ? "bg-foreground/5 border border-foreground/20 text-foreground"
                            : "bg-cream-dark/50 border border-silver-light/30 text-silver-dark hover:border-silver-light/60 hover:text-foreground"
                        } ${wishlistSaving || wishlistLoading ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
                      >
                        {wishlistSaving ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : inWishlist ? (
                          <BookmarkCheck className="w-3.5 h-3.5" />
                        ) : (
                          <BookmarkPlus className="w-3.5 h-3.5" />
                        )}
                        {inWishlist ? "Saved" : "Want to Listen"}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Divider */}
                <div className="h-px bg-silver-light/30 my-5" />

                {/* Stats grid — 4 columns */}
                <div className="grid grid-cols-4 gap-2">
                  <StatCard
                    icon={Star}
                    label="Your Rating"
                    value={
                      selectedRating != null
                        ? selectedRating.toFixed(1)
                        : detail?.user_rating != null
                          ? detail.user_rating.toFixed(1)
                          : "\u2014"
                    }
                    muted={selectedRating == null && detail?.user_rating == null}
                    skeleton={detailLoading}
                  />
                  <StatCard
                    icon={Hash}
                    label="Your Rank"
                    value={
                      detail?.user_rank != null
                        ? `#${detail.user_rank}`
                        : "\u2014"
                    }
                    muted={!detail?.user_rank}
                    skeleton={detailLoading}
                  />
                  <StatCard
                    icon={Users}
                    label="Community"
                    value={
                      detail?.community_average_rating != null
                        ? `${detail.community_average_rating.toFixed(1)} / 10`
                        : "\u2014"
                    }
                    muted={detail?.community_average_rating == null}
                    skeleton={detailLoading}
                  />
                  <StatCard
                    icon={TrendingUp}
                    label="Elo"
                    value={
                      detail?.user_elo_normalized != null
                        ? detail.user_elo_normalized.toFixed(1)
                        : "\u2014"
                    }
                    muted={detail?.user_elo_normalized == null}
                    skeleton={detailLoading}
                  />
                </div>

                {/* Community rating count footnote */}
                {detail && detail.community_rating_count > 0 && (
                  <p className="font-mono text-[9px] text-silver-dark/60 text-center mt-3">
                    {detail.community_rating_count}{" "}
                    {detail.community_rating_count === 1
                      ? "rating"
                      : "ratings"}{" "}
                    from the community
                  </p>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
