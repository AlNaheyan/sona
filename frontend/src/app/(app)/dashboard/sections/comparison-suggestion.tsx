"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Disc3 } from "lucide-react";
import { fadeUp } from "@/components/motion";
import { AlbumCover } from "@/components/album-cover";
import { SectionLabel } from "@/components/section-label";
import { EmptyState } from "@/components/empty-state";
import { apiFetch } from "@/lib/api";

/* ─── Types ─── */
interface SuggestedAlbum {
  id: string;
  mbid: string | null;
  title: string;
  artist_name: string | null;
  cover_url: string | null;
  elo: number;
  comparison_count: number;
}

interface Suggestion {
  album_a: SuggestedAlbum;
  album_b: SuggestedAlbum;
  reason: string;
  priority_score: number;
}

interface SuggestionsResponse {
  suggestions: Suggestion[];
  count: number;
}

interface ComparisonSuggestionProps {
  onComparisonSubmitted?: () => void;
}

export function ComparisonSuggestion({
  onComparisonSubmitted,
}: ComparisonSuggestionProps) {
  const [suggestion, setSuggestion] = useState<Suggestion | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEmpty, setIsEmpty] = useState(false);
  const [hoveredSide, setHoveredSide] = useState<"a" | "b" | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [pairKey, setPairKey] = useState(0);

  const fetchSuggestion = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await apiFetch<SuggestionsResponse>(
        "/api/v1/comparisons/suggestions?limit=1"
      );
      if (data.suggestions.length > 0) {
        setSuggestion(data.suggestions[0]);
        setIsEmpty(false);
      } else {
        setSuggestion(null);
        setIsEmpty(true);
      }
    } catch {
      setSuggestion(null);
      setIsEmpty(true);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSuggestion();
  }, [fetchSuggestion]);

  const handlePick = async (winner: "a" | "b") => {
    if (!suggestion || submitting) return;
    setSubmitting(true);
    try {
      await apiFetch("/api/v1/comparisons", {
        method: "POST",
        body: JSON.stringify({
          mbid_a: suggestion.album_a.mbid,
          mbid_b: suggestion.album_b.mbid,
          winner,
        }),
      });
      onComparisonSubmitted?.();
      setPairKey((k) => k + 1);
      await fetchSuggestion();
    } catch {
      // Silently handle — user can retry
    } finally {
      setSubmitting(false);
      setHoveredSide(null);
    }
  };

  if (isLoading) {
    return (
      <motion.div variants={fadeUp} className="mb-10">
        <SectionLabel className="mb-4">Compare</SectionLabel>
        <div className="border border-silver-light/40 rounded-2xl p-8 animate-pulse">
          <div className="flex items-center justify-center gap-6">
            <div className="w-28 h-28 rounded-lg bg-silver-light/30" />
            <div className="font-mono text-xs text-silver-light">vs</div>
            <div className="w-28 h-28 rounded-lg bg-silver-light/30" />
          </div>
        </div>
      </motion.div>
    );
  }

  if (isEmpty) {
    return (
      <motion.div variants={fadeUp} className="mb-10">
        <SectionLabel className="mb-4">Compare</SectionLabel>
        <EmptyState
          icon={Disc3}
          heading="No comparisons available."
          description="Rate more albums to unlock pairwise comparisons."
          actionLabel="Rate Albums"
          actionHref="/onboarding"
        />
      </motion.div>
    );
  }

  if (!suggestion) return null;

  return (
    <motion.div variants={fadeUp} className="mb-10">
      <SectionLabel className="mb-4">Compare</SectionLabel>
      <div className="border border-silver-light/40 rounded-2xl p-6 md:p-8">
        <AnimatePresence mode="wait">
          <motion.div
            key={pairKey}
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.97 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="flex items-center justify-center gap-4 md:gap-8"
          >
            {/* Album A */}
            <button
              onClick={() => handlePick("a")}
              onMouseEnter={() => setHoveredSide("a")}
              onMouseLeave={() => setHoveredSide(null)}
              disabled={submitting}
              className="flex flex-col items-center gap-3 transition-all duration-300 cursor-pointer group"
              style={{
                transform: hoveredSide === "a" ? "scale(1.03)" : "scale(1)",
                opacity: hoveredSide === "b" ? 0.5 : 1,
              }}
            >
              <AlbumCover
                title={suggestion.album_a.title}
                coverUrl={suggestion.album_a.cover_url}
                size="xl"
                className="group-hover:shadow-lg transition-shadow duration-300"
              />
              <div className="text-center max-w-[7rem]">
                <p className="font-serif text-sm tracking-tight truncate">
                  {suggestion.album_a.title}
                </p>
                <p className="font-mono text-[10px] text-silver-dark truncate">
                  {suggestion.album_a.artist_name || "Unknown"}
                </p>
              </div>
            </button>

            {/* VS divider */}
            <div className="flex flex-col items-center gap-1">
              <span className="font-mono text-[10px] tracking-[0.2em] uppercase text-silver-dark">
                vs
              </span>
            </div>

            {/* Album B */}
            <button
              onClick={() => handlePick("b")}
              onMouseEnter={() => setHoveredSide("b")}
              onMouseLeave={() => setHoveredSide(null)}
              disabled={submitting}
              className="flex flex-col items-center gap-3 transition-all duration-300 cursor-pointer group"
              style={{
                transform: hoveredSide === "b" ? "scale(1.03)" : "scale(1)",
                opacity: hoveredSide === "a" ? 0.5 : 1,
              }}
            >
              <AlbumCover
                title={suggestion.album_b.title}
                coverUrl={suggestion.album_b.cover_url}
                size="xl"
                className="group-hover:shadow-lg transition-shadow duration-300"
              />
              <div className="text-center max-w-[7rem]">
                <p className="font-serif text-sm tracking-tight truncate">
                  {suggestion.album_b.title}
                </p>
                <p className="font-mono text-[10px] text-silver-dark truncate">
                  {suggestion.album_b.artist_name || "Unknown"}
                </p>
              </div>
            </button>
          </motion.div>
        </AnimatePresence>

        <p className="font-mono text-[10px] text-silver text-center mt-4">
          {suggestion.reason}
        </p>
      </div>
    </motion.div>
  );
}
