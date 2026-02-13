"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import { Search, X, Clock } from "lucide-react";
import { stagger, fadeUp } from "@/components/motion";
import { AlbumCover } from "@/components/album-cover";
import { AlbumDetailModal } from "@/components/album-detail-modal";
import { EmptyState } from "@/components/empty-state";
import { SectionLabel } from "@/components/section-label";
import { apiFetch } from "@/lib/api";

/* ─── Types ─── */
interface AlbumSearchResult {
  mbid: string;
  title: string;
  artist_name: string;
  artist_mbid: string | null;
  release_year: number | null;
  cover_url: string | null;
}

interface AlbumSearchResponse {
  query: string;
  results: AlbumSearchResult[];
  count: number;
}

/* ─── Constants ─── */
const STORAGE_KEY = "rma-recent-searches";
const MAX_RECENT = 8;
const SKELETON_COUNT = 5;

type Tab = "albums" | "members";

/* ─── Recent searches helpers ─── */
function getRecentSearches(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveRecentSearch(query: string) {
  const trimmed = query.trim();
  if (!trimmed) return;
  const existing = getRecentSearches().filter((s) => s !== trimmed);
  const updated = [trimmed, ...existing].slice(0, MAX_RECENT);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
}

function clearRecentSearches() {
  localStorage.removeItem(STORAGE_KEY);
}

export default function SearchPage() {
  const [tab, setTab] = useState<Tab>("albums");

  return (
    <div className="max-w-4xl mx-auto px-8 py-16">
      <h1 className="font-serif text-3xl tracking-tight mb-6">Search</h1>

      {/* Tab bar */}
      <div className="flex justify-center gap-6 border-b border-silver-light/30 mb-6">
        <button
          onClick={() => setTab("albums")}
          className={`font-mono text-sm pb-2 transition-colors ${
            tab === "albums"
              ? "text-foreground border-b-2 border-foreground"
              : "text-silver-dark hover:text-foreground"
          }`}
        >
          Albums
        </button>
        <button
          onClick={() => setTab("members")}
          className={`font-mono text-sm pb-2 transition-colors ${
            tab === "members"
              ? "text-foreground border-b-2 border-foreground"
              : "text-silver-dark hover:text-foreground"
          }`}
        >
          Members
        </button>
      </div>

      {/* Tab content */}
      {tab === "albums" ? (
        <AlbumsTab />
      ) : (
        <EmptyState
          heading="Coming soon"
          description="Search for other members."
        />
      )}
    </div>
  );
}

/* ─── Albums Tab ─── */
function AlbumsTab() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<AlbumSearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [selectedAlbum, setSelectedAlbum] = useState<AlbumSearchResult | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Load recent searches on mount
  useEffect(() => {
    setRecentSearches(getRecentSearches());
  }, []);

  const executeSearch = useCallback((q: string) => {
    const trimmed = q.trim();
    if (!trimmed) {
      setResults([]);
      setHasSearched(false);
      setIsLoading(false);
      return;
    }

    // Cancel previous request
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setIsLoading(true);
    apiFetch<AlbumSearchResponse>(
      `/api/v1/albums/search?q=${encodeURIComponent(trimmed)}&limit=10`,
      { signal: controller.signal }
    )
      .then((data) => {
        setResults(data.results);
        setHasSearched(true);
      })
      .catch((err) => {
        if (err?.name !== "AbortError") {
          setResults([]);
          setHasSearched(true);
        }
      })
      .finally(() => setIsLoading(false));
  }, []);

  const handleInputChange = (value: string) => {
    setQuery(value);

    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (!value.trim()) {
      abortRef.current?.abort();
      setResults([]);
      setHasSearched(false);
      setIsLoading(false);
      return;
    }

    debounceRef.current = setTimeout(() => {
      executeSearch(value);
    }, 300);
  };

  const handleRecentClick = (term: string) => {
    setQuery(term);
    executeSearch(term);
  };

  const handleResultClick = (album: AlbumSearchResult) => {
    if (query.trim()) {
      saveRecentSearch(query);
      setRecentSearches(getRecentSearches());
    }
    setSelectedAlbum(album);
  };

  const handleClearRecent = () => {
    clearRecentSearches();
    setRecentSearches([]);
  };

  const showRecent = !query.trim() && recentSearches.length > 0;

  return (
    <div>
      {/* Search bar */}
      <div className="relative mb-6">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-silver-dark pointer-events-none" />
        <input
          type="text"
          value={query}
          onChange={(e) => handleInputChange(e.target.value)}
          placeholder="Search albums..."
          className="w-full font-mono text-sm pl-10 pr-10 py-3 rounded-xl border border-silver-light/30 focus-within:border-silver-light/60 focus:border-silver-light/60 bg-transparent outline-none transition-colors placeholder:text-silver-dark/50"
        />
        {query && (
          <button
            onClick={() => handleInputChange("")}
            className="absolute right-3.5 top-1/2 -translate-y-1/2 text-silver-dark hover:text-foreground transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Recent searches */}
      {showRecent && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <SectionLabel>Recent Searches</SectionLabel>
            <button
              onClick={handleClearRecent}
              className="font-mono text-[10px] text-silver-dark hover:text-foreground transition-colors"
            >
              Clear
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {recentSearches.map((term) => (
              <button
                key={term}
                onClick={() => handleRecentClick(term)}
                className="flex items-center gap-1.5 font-mono text-xs px-3 py-1.5 rounded-full border border-silver-light/30 hover:border-silver-light/60 text-silver-dark hover:text-foreground transition-colors"
              >
                <Clock className="w-3 h-3" />
                {term}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Loading skeletons */}
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

      {/* Search results */}
      {!isLoading && hasSearched && results.length > 0 && (
        <motion.div
          className="space-y-2"
          variants={stagger}
          initial="hidden"
          animate="show"
        >
          {results.map((album) => (
            <motion.div
              key={album.mbid}
              variants={fadeUp}
              onClick={() => handleResultClick(album)}
              className="flex items-center gap-3 p-3 rounded-xl border border-silver-light/30 hover:border-silver-light/60 transition-colors duration-200 cursor-pointer"
            >
              <AlbumCover
                title={album.title}
                coverUrl={album.cover_url}
              />
              <div className="min-w-0 flex-1">
                <p className="font-serif text-sm tracking-tight truncate">
                  {album.title}
                </p>
                <p className="font-mono text-[10px] text-silver-dark truncate">
                  {album.artist_name}
                </p>
              </div>
              {album.release_year && (
                <span className="font-mono text-xs text-silver-dark shrink-0 mr-1">
                  {album.release_year}
                </span>
              )}
            </motion.div>
          ))}
        </motion.div>
      )}

      {/* No results */}
      {!isLoading && hasSearched && results.length === 0 && (
        <p className="font-mono text-sm text-silver-dark">No albums found.</p>
      )}

      <AlbumDetailModal
        album={selectedAlbum}
        onClose={() => setSelectedAlbum(null)}
      />
    </div>
  );
}
