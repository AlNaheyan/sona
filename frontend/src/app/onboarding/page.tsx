"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight,
  Check,
  Search,
  X,
  Disc3,
  User,
  Camera,
} from "lucide-react";
import { useState, useCallback, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";

/* ─────────────────────────────────────────────
   Types
   ───────────────────────────────────────────── */
interface SearchResult {
  id: string;
  title: string;
  artist: string;
  year: number;
  gradient: string;
  initials: string;
}

interface RatedAlbum extends SearchResult {
  rating: number;
}

/* ─────────────────────────────────────────────
   Mock Search Database
   (Simulates backend /api/v1/albums/search)
   ───────────────────────────────────────────── */
const MOCK_DB: SearchResult[] = [
  { id: "1", title: "OK Computer", artist: "Radiohead", year: 1997, gradient: "from-sky-900 to-slate-800", initials: "OK" },
  { id: "2", title: "To Pimp a Butterfly", artist: "Kendrick Lamar", year: 2015, gradient: "from-emerald-800 to-yellow-900", initials: "TB" },
  { id: "3", title: "Kind of Blue", artist: "Miles Davis", year: 1959, gradient: "from-blue-900 to-indigo-950", initials: "KB" },
  { id: "4", title: "Random Access Memories", artist: "Daft Punk", year: 2013, gradient: "from-amber-700 to-stone-900", initials: "RA" },
  { id: "5", title: "Rumours", artist: "Fleetwood Mac", year: 1977, gradient: "from-stone-700 to-neutral-900", initials: "Rm" },
  { id: "6", title: "My Beautiful Dark Twisted Fantasy", artist: "Kanye West", year: 2010, gradient: "from-red-900 to-rose-950", initials: "MB" },
  { id: "7", title: "Blue", artist: "Joni Mitchell", year: 1971, gradient: "from-cyan-800 to-blue-950", initials: "Bl" },
  { id: "8", title: "Abbey Road", artist: "The Beatles", year: 1969, gradient: "from-sky-600 to-slate-700", initials: "AR" },
  { id: "9", title: "Blonde", artist: "Frank Ocean", year: 2016, gradient: "from-orange-300 to-lime-200", initials: "Bd" },
  { id: "10", title: "Loveless", artist: "My Bloody Valentine", year: 1991, gradient: "from-pink-700 to-fuchsia-950", initials: "Lv" },
  { id: "11", title: "The Miseducation of Lauryn Hill", artist: "Lauryn Hill", year: 1998, gradient: "from-amber-800 to-orange-950", initials: "ML" },
  { id: "12", title: "In Rainbows", artist: "Radiohead", year: 2007, gradient: "from-red-600 to-orange-800", initials: "IR" },
  { id: "13", title: "Thriller", artist: "Michael Jackson", year: 1982, gradient: "from-yellow-600 to-amber-900", initials: "Th" },
  { id: "14", title: "Discovery", artist: "Daft Punk", year: 2001, gradient: "from-blue-600 to-purple-800", initials: "Ds" },
  { id: "15", title: "Vespertine", artist: "Bj\u00f6rk", year: 2001, gradient: "from-slate-200 to-zinc-400", initials: "Vp" },
  { id: "16", title: "The Dark Side of the Moon", artist: "Pink Floyd", year: 1973, gradient: "from-gray-900 to-black", initials: "DS" },
  { id: "17", title: "Nevermind", artist: "Nirvana", year: 1991, gradient: "from-cyan-600 to-blue-900", initials: "Nv" },
  { id: "18", title: "good kid, m.A.A.d city", artist: "Kendrick Lamar", year: 2012, gradient: "from-zinc-700 to-neutral-900", initials: "gk" },
  { id: "19", title: "A Love Supreme", artist: "John Coltrane", year: 1965, gradient: "from-orange-900 to-amber-950", initials: "AL" },
  { id: "20", title: "Remain in Light", artist: "Talking Heads", year: 1980, gradient: "from-red-700 to-yellow-600", initials: "RL" },
  { id: "21", title: "Hounds of Love", artist: "Kate Bush", year: 1985, gradient: "from-violet-800 to-indigo-900", initials: "HL" },
  { id: "22", title: "The Queen Is Dead", artist: "The Smiths", year: 1986, gradient: "from-stone-600 to-zinc-800", initials: "QD" },
  { id: "23", title: "Funeral", artist: "Arcade Fire", year: 2004, gradient: "from-slate-700 to-stone-900", initials: "Fn" },
  { id: "24", title: "Melodrama", artist: "Lorde", year: 2017, gradient: "from-blue-500 to-purple-700", initials: "Md" },
  { id: "25", title: "Channel Orange", artist: "Frank Ocean", year: 2012, gradient: "from-orange-500 to-amber-700", initials: "CO" },
  { id: "26", title: "Currents", artist: "Tame Impala", year: 2015, gradient: "from-rose-500 to-purple-600", initials: "Cu" },
  { id: "27", title: "Igor", artist: "Tyler, The Creator", year: 2019, gradient: "from-pink-400 to-rose-600", initials: "Ig" },
  { id: "28", title: "Homework", artist: "Daft Punk", year: 1997, gradient: "from-yellow-500 to-red-600", initials: "Hw" },
  { id: "29", title: "Is This It", artist: "The Strokes", year: 2001, gradient: "from-sky-400 to-blue-700", initials: "IT" },
  { id: "30", title: "Songs in the Key of Life", artist: "Stevie Wonder", year: 1976, gradient: "from-yellow-700 to-orange-900", initials: "SK" },
];

function searchAlbums(query: string): SearchResult[] {
  if (!query.trim()) return [];
  const q = query.toLowerCase();
  return MOCK_DB.filter(
    (a) =>
      a.title.toLowerCase().includes(q) ||
      a.artist.toLowerCase().includes(q)
  ).slice(0, 6);
}

const GENRES = [
  "Rock", "Pop", "Hip Hop", "Electronic", "Jazz", "Classical",
  "R&B", "Metal", "Indie", "Folk", "Punk", "Soul",
  "Country", "Blues", "Reggae", "Latin",
];

/* ─────────────────────────────────────────────
   Animation Variants
   ───────────────────────────────────────────── */
const stepVariants = {
  enter: (direction: number) => ({
    x: direction > 0 ? 80 : -80,
    opacity: 0,
  }),
  center: { x: 0, opacity: 1 },
  exit: (direction: number) => ({
    x: direction > 0 ? -80 : 80,
    opacity: 0,
  }),
};

const stagger = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.06, delayChildren: 0.15 },
  },
};

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] as const },
  },
};

/* ─────────────────────────────────────────────
   Shared Components
   ───────────────────────────────────────────── */
function ProgressBar({ step, total }: { step: number; total: number }) {
  const pct = (step / total) * 100;
  return (
    <div className="fixed top-0 left-0 right-0 z-50 h-0.75 bg-cream-dark">
      <motion.div
        className="h-full bg-foreground"
        initial={{ width: 0 }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      />
    </div>
  );
}

function StepDots({ current, total }: { current: number; total: number }) {
  return (
    <div className="flex items-center gap-2.5">
      {Array.from({ length: total }, (_, i) => (
        <motion.div
          key={i}
          className={`rounded-full transition-colors duration-300 ${
            i + 1 === current
              ? "w-6 h-1.5 bg-foreground"
              : i + 1 < current
              ? "w-1.5 h-1.5 bg-foreground"
              : "w-1.5 h-1.5 bg-silver-light"
          }`}
          layout
          transition={{ type: "spring", stiffness: 400, damping: 30 }}
        />
      ))}
    </div>
  );
}

function AlbumThumb({
  album,
  size = "sm",
}: {
  album: SearchResult;
  size?: "sm" | "xs";
}) {
  const dim = size === "sm" ? "w-12 h-12" : "w-9 h-9";
  const text = size === "sm" ? "text-[10px]" : "text-[8px]";
  return (
    <div
      className={`${dim} rounded-lg bg-linear-to-br ${album.gradient} flex items-center justify-center shrink-0`}
    >
      <span className={`font-serif ${text} text-white/40 italic select-none`}>
        {album.initials}
      </span>
    </div>
  );
}

/* ─────────────────────────────────────────────
   Step 1 — Welcome
   ───────────────────────────────────────────── */
function WelcomeStep({ onNext }: { onNext: () => void }) {
  const steps = [
    { num: "01", label: "Pick your genres" },
    { num: "02", label: "Add your albums" },
    { num: "03", label: "Set up your profile" },
  ];

  return (
    <motion.div
      variants={stagger}
      initial="hidden"
      animate="show"
      className="flex flex-col items-center text-center max-w-lg mx-auto"
    >
      <motion.div variants={fadeUp} className="mb-4">
        <Disc3 className="w-8 h-8 text-silver-dark mx-auto" strokeWidth={1.5} />
      </motion.div>

      <motion.h1
        variants={fadeUp}
        className="font-serif text-4xl md:text-5xl lg:text-6xl tracking-tight mb-4"
      >
        Welcome to <span className="italic">Sona.</span>
      </motion.h1>

      <motion.p
        variants={fadeUp}
        className="font-mono text-sm text-silver-dark leading-relaxed mb-12 max-w-sm"
      >
        Let&apos;s set up your taste profile. This takes about 2 minutes.
      </motion.p>

      <motion.div variants={fadeUp} className="w-full max-w-xs mb-12">
        <div className="space-y-4">
          {steps.map((s) => (
            <div key={s.num} className="flex items-center gap-4">
              <span className="font-mono text-[10px] tracking-widest text-silver w-6">
                {s.num}
              </span>
              <div className="h-px flex-1 bg-silver-light" />
              <span className="font-mono text-xs text-silver-dark">
                {s.label}
              </span>
            </div>
          ))}
        </div>
      </motion.div>

      <motion.div variants={fadeUp}>
        <motion.button
          onClick={onNext}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          className="font-mono text-sm tracking-widest uppercase py-4 px-12 bg-foreground text-cream rounded-full hover:shadow-[0_8px_30px_rgba(0,0,0,0.12)] transition-shadow duration-300"
        >
          Let&apos;s Go
        </motion.button>
      </motion.div>
    </motion.div>
  );
}

/* ─────────────────────────────────────────────
   Step 2 — Genre Selection
   ───────────────────────────────────────────── */
function GenreStep({
  selectedGenres,
  onToggle,
  onNext,
}: {
  selectedGenres: string[];
  onToggle: (g: string) => void;
  onNext: () => void;
}) {
  const canContinue = selectedGenres.length >= 2;

  return (
    <motion.div
      variants={stagger}
      initial="hidden"
      animate="show"
      className="flex flex-col items-center max-w-3xl mx-auto"
    >
      <motion.div variants={fadeUp} className="text-center mb-10">
        <h2 className="font-serif text-3xl md:text-4xl tracking-tight mb-3">
          What do you <span className="italic">listen</span> to?
        </h2>
        <p className="font-mono text-xs text-silver-dark">
          Select at least 2 genres to continue
        </p>
      </motion.div>

      <motion.div
        variants={fadeUp}
        className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 w-full mb-10"
      >
        {GENRES.map((genre) => {
          const selected = selectedGenres.includes(genre);
          return (
            <motion.button
              key={genre}
              onClick={() => onToggle(genre)}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.96 }}
              animate={{
                backgroundColor: selected ? "#171717" : "transparent",
                color: selected ? "#f5f0e8" : "#8a8a8a",
                borderColor: selected ? "#171717" : "#d4d4d4",
              }}
              transition={{ type: "spring", stiffness: 500, damping: 30 }}
              className="relative font-mono text-xs tracking-wide py-3.5 px-4 rounded-xl border text-left overflow-hidden"
            >
              <span className="relative z-10 flex items-center justify-between">
                {genre}
                <AnimatePresence>
                  {selected && (
                    <motion.span
                      initial={{ scale: 0, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0, opacity: 0 }}
                      transition={{ type: "spring", stiffness: 500, damping: 25 }}
                    >
                      <Check className="w-3.5 h-3.5" />
                    </motion.span>
                  )}
                </AnimatePresence>
              </span>
            </motion.button>
          );
        })}
      </motion.div>

      <motion.div variants={fadeUp} className="flex items-center gap-4">
        <span className="font-mono text-[10px] text-silver-dark tracking-wide">
          {selectedGenres.length} selected
        </span>
        <motion.button
          onClick={onNext}
          disabled={!canContinue}
          whileHover={canContinue ? { scale: 1.03 } : {}}
          whileTap={canContinue ? { scale: 0.97 } : {}}
          className="font-mono text-sm tracking-widest uppercase py-4 px-12 bg-foreground text-cream rounded-full transition-all duration-300 disabled:opacity-30 disabled:cursor-not-allowed hover:shadow-[0_8px_30px_rgba(0,0,0,0.12)]"
        >
          Continue
        </motion.button>
      </motion.div>
    </motion.div>
  );
}

/* ─────────────────────────────────────────────
   Step 3 — Search & Rate Albums
   ───────────────────────────────────────────── */
function SearchRateStep({
  ratedAlbums,
  onRate,
  onRemove,
  onUpdateRating,
  onNext,
}: {
  ratedAlbums: RatedAlbum[];
  onRate: (album: SearchResult, rating: number) => void;
  onRemove: (albumId: string) => void;
  onUpdateRating: (albumId: string, rating: number) => void;
  onNext: () => void;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [selectedAlbum, setSelectedAlbum] = useState<SearchResult | null>(null);
  const [showResults, setShowResults] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const canContinue = ratedAlbums.length >= 5;

  // Debounced search
  const trimmedQuery = query.trim();
  useEffect(() => {
    if (!trimmedQuery) return;
    const timer = setTimeout(() => {
      const found = searchAlbums(trimmedQuery).filter(
        (r) => !ratedAlbums.some((ra) => ra.id === r.id)
      );
      setResults(found);
      setShowResults(true);
    }, 200);
    return () => clearTimeout(timer);
  }, [trimmedQuery, ratedAlbums]);

  // Clear results when query is empty
  const handleQueryChange = (value: string) => {
    setQuery(value);
    if (!value.trim()) {
      setResults([]);
      setShowResults(false);
    }
  };

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setShowResults(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const selectAlbum = (album: SearchResult) => {
    setSelectedAlbum(album);
    setShowResults(false);
    setQuery("");
  };

  const rateAndAdd = (rating: number) => {
    if (!selectedAlbum) return;
    onRate(selectedAlbum, rating);
    setSelectedAlbum(null);
  };

  return (
    <div className="flex flex-col items-center max-w-2xl mx-auto w-full">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] as const }}
        className="text-center mb-8"
      >
        <h2 className="font-serif text-3xl md:text-4xl tracking-tight mb-2">
          Add your <span className="italic">albums.</span>
        </h2>
        <p className="font-mono text-xs text-silver-dark">
          Search for albums you know and rate them. Add at least 5.
        </p>
      </motion.div>

      {/* Search Bar */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1, ease: [0.16, 1, 0.3, 1] as const }}
        className="w-full max-w-md relative mb-6"
      >
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-silver" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => handleQueryChange(e.target.value)}
            onFocus={() => results.length > 0 && setShowResults(true)}
            placeholder="Search for an album or artist..."
            className="w-full font-mono text-sm bg-transparent border border-silver-light rounded-xl py-3.5 pl-11 pr-4 text-foreground placeholder:text-silver-light outline-none focus:border-silver-dark transition-colors duration-300"
          />
        </div>

        {/* Search Results Dropdown */}
        <AnimatePresence>
          {showResults && results.length > 0 && (
            <motion.div
              ref={dropdownRef}
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.2 }}
              className="absolute top-full mt-2 w-full bg-background border border-silver-light rounded-xl overflow-hidden shadow-lg z-30"
            >
              {results.map((album) => (
                <button
                  key={album.id}
                  onClick={() => selectAlbum(album)}
                  className="w-full flex items-center gap-3 px-4 py-3 hover:bg-cream-dark transition-colors duration-200 text-left"
                >
                  <AlbumThumb album={album} size="xs" />
                  <div className="min-w-0 flex-1">
                    <p className="font-serif text-sm truncate">{album.title}</p>
                    <p className="font-mono text-[10px] text-silver-dark truncate">
                      {album.artist} &middot; {album.year}
                    </p>
                  </div>
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {showResults && query.trim() && results.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute top-full mt-2 w-full bg-background border border-silver-light rounded-xl p-4 shadow-lg z-30"
          >
            <p className="font-mono text-xs text-silver-dark text-center">
              No albums found for &ldquo;{query}&rdquo;
            </p>
          </motion.div>
        )}
      </motion.div>

      {/* Rating Panel for Selected Album */}
      <AnimatePresence mode="wait">
        {selectedAlbum && (
          <motion.div
            key={selectedAlbum.id}
            initial={{ opacity: 0, scale: 0.97, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: -8 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] as const }}
            className="w-full max-w-md bg-cream-dark/60 border border-silver-light/40 rounded-2xl p-6 mb-6"
          >
            <div className="flex items-center gap-4 mb-5">
              <AlbumThumb album={selectedAlbum} size="sm" />
              <div className="min-w-0 flex-1">
                <p className="font-serif text-base tracking-tight truncate">
                  {selectedAlbum.title}
                </p>
                <p className="font-mono text-[10px] text-silver-dark truncate">
                  {selectedAlbum.artist} &middot; {selectedAlbum.year}
                </p>
              </div>
              <button
                onClick={() => setSelectedAlbum(null)}
                className="text-silver hover:text-foreground transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="font-mono text-[10px] text-silver-dark tracking-widest uppercase mb-3 text-center">
              Rate this album
            </p>

            <div className="flex items-center justify-center gap-1.5 mb-3">
              {Array.from({ length: 10 }, (_, i) => i + 1).map((val) => (
                <motion.button
                  key={val}
                  onClick={() => rateAndAdd(val)}
                  whileHover={{ scale: 1.15 }}
                  whileTap={{ scale: 0.9 }}
                  className="w-9 h-9 md:w-10 md:h-10 rounded-full border border-silver-light font-mono text-sm text-silver-dark hover:bg-foreground hover:text-cream hover:border-foreground transition-colors duration-200 flex items-center justify-center"
                >
                  {val}
                </motion.button>
              ))}
            </div>

            <div className="flex justify-between px-1">
              <span className="font-mono text-[9px] text-silver tracking-wider uppercase">
                Terrible
              </span>
              <span className="font-mono text-[9px] text-silver tracking-wider uppercase">
                Masterpiece
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Rated Albums List */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="w-full max-w-md"
      >
        {ratedAlbums.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center justify-between mb-3">
              <span className="font-mono text-[10px] text-silver-dark tracking-widest uppercase">
                Your albums ({ratedAlbums.length})
              </span>
              {!canContinue && (
                <span className="font-mono text-[10px] text-silver tracking-wide">
                  {5 - ratedAlbums.length} more needed
                </span>
              )}
            </div>

            <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
              <AnimatePresence>
                {ratedAlbums.map((album) => (
                  <motion.div
                    key={album.id}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20, height: 0, marginBottom: 0 }}
                    transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] as const }}
                    className="flex items-center gap-3 p-2.5 rounded-xl bg-cream-dark/40 border border-silver-light/20"
                  >
                    <AlbumThumb album={album} size="xs" />
                    <div className="min-w-0 flex-1">
                      <p className="font-serif text-xs tracking-tight truncate">
                        {album.title}
                      </p>
                      <p className="font-mono text-[9px] text-silver-dark truncate">
                        {album.artist}
                      </p>
                    </div>

                    {/* Inline rating adjuster */}
                    <div className="flex items-center gap-1">
                      {Array.from({ length: 10 }, (_, i) => i + 1).map((val) => (
                        <button
                          key={val}
                          onClick={() => onUpdateRating(album.id, val)}
                          className={`w-5 h-5 rounded-full font-mono text-[8px] flex items-center justify-center transition-colors duration-200 ${
                            val === album.rating
                              ? "bg-foreground text-cream"
                              : "text-silver-light hover:text-silver-dark"
                          }`}
                        >
                          {val}
                        </button>
                      ))}
                    </div>

                    <button
                      onClick={() => onRemove(album.id)}
                      className="text-silver hover:text-foreground transition-colors ml-1"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>
        )}

        {ratedAlbums.length === 0 && !selectedAlbum && (
          <div className="text-center py-8 border border-dashed border-silver-light/40 rounded-2xl">
            <Search className="w-5 h-5 text-silver-light mx-auto mb-2" />
            <p className="font-mono text-xs text-silver">
              Search above to start adding albums
            </p>
          </div>
        )}
      </motion.div>

      {/* Continue */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="mt-8"
      >
        <motion.button
          onClick={onNext}
          disabled={!canContinue}
          whileHover={canContinue ? { scale: 1.03 } : {}}
          whileTap={canContinue ? { scale: 0.97 } : {}}
          className="font-mono text-sm tracking-widest uppercase py-4 px-12 bg-foreground text-cream rounded-full transition-all duration-300 disabled:opacity-30 disabled:cursor-not-allowed hover:shadow-[0_8px_30px_rgba(0,0,0,0.12)] inline-flex items-center gap-3"
        >
          Continue
          <ArrowRight className="w-4 h-4" />
        </motion.button>
      </motion.div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   Step 4 — Profile Setup
   ───────────────────────────────────────────── */
function ProfileStep({ onComplete }: { onComplete: () => void }) {
  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [spotifyUsername, setSpotifyUsername] = useState("");
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const canComplete = displayName.trim().length >= 2;

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onloadend = () => setPhotoPreview(reader.result as string);
    reader.readAsDataURL(file);
  };

  return (
    <motion.div
      variants={stagger}
      initial="hidden"
      animate="show"
      className="flex flex-col items-center max-w-md mx-auto w-full"
    >
      <motion.div variants={fadeUp} className="text-center mb-10">
        <h2 className="font-serif text-3xl md:text-4xl tracking-tight mb-3">
          Set up your <span className="italic">profile.</span>
        </h2>
        <p className="font-mono text-xs text-silver-dark">
          Tell us a bit about yourself.
        </p>
      </motion.div>

      {/* Photo Upload */}
      <motion.div variants={fadeUp} className="mb-8">
        <button
          onClick={() => fileInputRef.current?.click()}
          className="relative w-24 h-24 rounded-full bg-cream-dark border-2 border-dashed border-silver-light hover:border-silver-dark transition-colors duration-300 flex items-center justify-center overflow-hidden group"
        >
          {photoPreview ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={photoPreview}
              alt="Profile"
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="flex flex-col items-center gap-1">
              <Camera className="w-5 h-5 text-silver group-hover:text-silver-dark transition-colors" />
              <span className="font-mono text-[8px] text-silver tracking-wider uppercase">
                Photo
              </span>
            </div>
          )}
          {photoPreview && (
            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
              <Camera className="w-5 h-5 text-white" />
            </div>
          )}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handlePhotoChange}
          className="hidden"
        />
      </motion.div>

      {/* Display Name */}
      <motion.div variants={fadeUp} className="w-full mb-5">
        <label className="block font-mono text-[10px] tracking-[0.2em] uppercase text-silver-dark mb-2">
          Display Name *
        </label>
        <input
          type="text"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          placeholder="How should we call you?"
          className="w-full font-mono text-sm bg-transparent border border-silver-light rounded-xl py-3 px-4 text-foreground placeholder:text-silver-light outline-none focus:border-silver-dark transition-colors duration-300"
        />
      </motion.div>

      {/* Bio */}
      <motion.div variants={fadeUp} className="w-full mb-5">
        <label className="block font-mono text-[10px] tracking-[0.2em] uppercase text-silver-dark mb-2">
          Bio
          <span className="normal-case tracking-normal text-silver ml-2">optional</span>
        </label>
        <textarea
          value={bio}
          onChange={(e) => setBio(e.target.value)}
          placeholder="A few words about your music taste..."
          rows={3}
          maxLength={160}
          className="w-full font-mono text-sm bg-transparent border border-silver-light rounded-xl py-3 px-4 text-foreground placeholder:text-silver-light outline-none focus:border-silver-dark transition-colors duration-300 resize-none"
        />
        <p className="font-mono text-[9px] text-silver text-right mt-1">
          {bio.length}/160
        </p>
      </motion.div>

      {/* Spotify Username */}
      <motion.div variants={fadeUp} className="w-full mb-10">
        <label className="block font-mono text-[10px] tracking-[0.2em] uppercase text-silver-dark mb-2">
          Spotify Username
          <span className="normal-case tracking-normal text-silver ml-2">optional</span>
        </label>
        <div className="relative">
          <User className="absolute left-4 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-silver" />
          <input
            type="text"
            value={spotifyUsername}
            onChange={(e) => setSpotifyUsername(e.target.value)}
            placeholder="your-spotify-username"
            className="w-full font-mono text-sm bg-transparent border border-silver-light rounded-xl py-3 pl-10 pr-4 text-foreground placeholder:text-silver-light outline-none focus:border-silver-dark transition-colors duration-300"
          />
        </div>
      </motion.div>

      {/* Complete */}
      <motion.div variants={fadeUp}>
        <motion.button
          onClick={onComplete}
          disabled={!canComplete}
          whileHover={canComplete ? { scale: 1.03 } : {}}
          whileTap={canComplete ? { scale: 0.97 } : {}}
          className="font-mono text-sm tracking-widest uppercase py-4 px-12 bg-foreground text-cream rounded-full transition-all duration-300 disabled:opacity-30 disabled:cursor-not-allowed hover:shadow-[0_8px_30px_rgba(0,0,0,0.12)] inline-flex items-center gap-3"
        >
          Go to Dashboard
          <ArrowRight className="w-4 h-4" />
        </motion.button>
      </motion.div>
    </motion.div>
  );
}

/* ─────────────────────────────────────────────
   Main Onboarding Page
   ───────────────────────────────────────────── */
export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [direction, setDirection] = useState(1);
  const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
  const [ratedAlbums, setRatedAlbums] = useState<RatedAlbum[]>([]);

  const totalSteps = 4;

  const goNext = useCallback(() => {
    setDirection(1);
    setStep((s) => Math.min(s + 1, totalSteps));
  }, []);

  const toggleGenre = useCallback((genre: string) => {
    setSelectedGenres((prev) =>
      prev.includes(genre) ? prev.filter((g) => g !== genre) : [...prev, genre]
    );
  }, []);

  const handleRateAlbum = useCallback((album: SearchResult, rating: number) => {
    setRatedAlbums((prev) => [...prev, { ...album, rating }]);
  }, []);

  const handleRemoveAlbum = useCallback((albumId: string) => {
    setRatedAlbums((prev) => prev.filter((a) => a.id !== albumId));
  }, []);

  const handleUpdateRating = useCallback((albumId: string, rating: number) => {
    setRatedAlbums((prev) =>
      prev.map((a) => (a.id === albumId ? { ...a, rating } : a))
    );
  }, []);

  const handleComplete = useCallback(() => {
    // TODO: Save onboarding data (genres, rated albums, profile) to backend
    router.push("/dashboard");
  }, [router]);

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <ProgressBar step={step} total={totalSteps} />

      {/* Top bar */}
      <div className="flex items-center justify-between px-8 md:px-12 pt-10 pb-6">
        <span className="font-serif text-lg tracking-tight">Sona</span>
        <StepDots current={step} total={totalSteps} />
        <span className="font-mono text-[10px] text-silver tracking-widest uppercase">
          Step {step}/{totalSteps}
        </span>
      </div>

      {/* Content */}
      <div className="flex-1 flex items-center justify-center px-6 md:px-12 pb-16">
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={step}
            custom={direction}
            variants={stepVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="w-full"
          >
            {step === 1 && <WelcomeStep onNext={goNext} />}
            {step === 2 && (
              <GenreStep
                selectedGenres={selectedGenres}
                onToggle={toggleGenre}
                onNext={goNext}
              />
            )}
            {step === 3 && (
              <SearchRateStep
                ratedAlbums={ratedAlbums}
                onRate={handleRateAlbum}
                onRemove={handleRemoveAlbum}
                onUpdateRating={handleUpdateRating}
                onNext={goNext}
              />
            )}
            {step === 4 && <ProfileStep onComplete={handleComplete} />}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
