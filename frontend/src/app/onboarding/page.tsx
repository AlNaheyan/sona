"use client";

import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, Check, SkipForward, Music, Disc3, Star } from "lucide-react";
import { useState, useMemo, useCallback } from "react";
import { useRouter } from "next/navigation";

/* ─────────────────────────────────────────────
   Mock Album Data
   ───────────────────────────────────────────── */
interface Album {
  id: string;
  title: string;
  artist: string;
  year: number;
  genres: string[];
  gradient: string;
  initials: string;
}

const ALBUMS: Album[] = [
  { id: "1", title: "OK Computer", artist: "Radiohead", year: 1997, genres: ["Rock"], gradient: "from-sky-900 to-slate-800", initials: "OK" },
  { id: "2", title: "To Pimp a Butterfly", artist: "Kendrick Lamar", year: 2015, genres: ["Hip Hop"], gradient: "from-emerald-800 to-yellow-900", initials: "TB" },
  { id: "3", title: "Kind of Blue", artist: "Miles Davis", year: 1959, genres: ["Jazz"], gradient: "from-blue-900 to-indigo-950", initials: "KB" },
  { id: "4", title: "Random Access Memories", artist: "Daft Punk", year: 2013, genres: ["Electronic"], gradient: "from-amber-700 to-stone-900", initials: "RA" },
  { id: "5", title: "Rumours", artist: "Fleetwood Mac", year: 1977, genres: ["Rock"], gradient: "from-stone-700 to-neutral-900", initials: "Rm" },
  { id: "6", title: "My Beautiful Dark Twisted Fantasy", artist: "Kanye West", year: 2010, genres: ["Hip Hop"], gradient: "from-red-900 to-rose-950", initials: "MB" },
  { id: "7", title: "Blue", artist: "Joni Mitchell", year: 1971, genres: ["Folk"], gradient: "from-cyan-800 to-blue-950", initials: "Bl" },
  { id: "8", title: "Abbey Road", artist: "The Beatles", year: 1969, genres: ["Rock"], gradient: "from-sky-600 to-slate-700", initials: "AR" },
  { id: "9", title: "Blonde", artist: "Frank Ocean", year: 2016, genres: ["R&B"], gradient: "from-orange-300 to-lime-200", initials: "Bd" },
  { id: "10", title: "Loveless", artist: "My Bloody Valentine", year: 1991, genres: ["Indie"], gradient: "from-pink-700 to-fuchsia-950", initials: "Lv" },
  { id: "11", title: "The Miseducation of Lauryn Hill", artist: "Lauryn Hill", year: 1998, genres: ["R&B", "Hip Hop"], gradient: "from-amber-800 to-orange-950", initials: "ML" },
  { id: "12", title: "In Rainbows", artist: "Radiohead", year: 2007, genres: ["Rock", "Indie"], gradient: "from-red-600 to-orange-800", initials: "IR" },
  { id: "13", title: "Thriller", artist: "Michael Jackson", year: 1982, genres: ["Pop"], gradient: "from-yellow-600 to-amber-900", initials: "Th" },
  { id: "14", title: "Discovery", artist: "Daft Punk", year: 2001, genres: ["Electronic", "Pop"], gradient: "from-blue-600 to-purple-800", initials: "Ds" },
  { id: "15", title: "Vespertine", artist: "Bj\u00f6rk", year: 2001, genres: ["Electronic"], gradient: "from-slate-200 to-zinc-400", initials: "Vp" },
];

const GENRES = [
  "Rock", "Pop", "Hip Hop", "Electronic", "Jazz", "Classical",
  "R&B", "Metal", "Indie", "Folk", "Punk", "Soul",
  "Country", "Blues", "Reggae", "Latin",
];

/* ─────────────────────────────────────────────
   Step Transition Variants
   ───────────────────────────────────────────── */
const stepVariants = {
  enter: (direction: number) => ({
    x: direction > 0 ? 80 : -80,
    opacity: 0,
  }),
  center: {
    x: 0,
    opacity: 1,
  },
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
   Progress Bar
   ───────────────────────────────────────────── */
function ProgressBar({ step, total }: { step: number; total: number }) {
  const pct = ((step) / total) * 100;
  return (
    <div className="fixed top-0 left-0 right-0 z-50 h-[3px] bg-cream-dark">
      <motion.div
        className="h-full bg-foreground"
        initial={{ width: 0 }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      />
    </div>
  );
}

/* ─────────────────────────────────────────────
   Step Dots
   ───────────────────────────────────────────── */
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

/* ─────────────────────────────────────────────
   Album Art Placeholder
   ───────────────────────────────────────────── */
function AlbumArt({ album, size = "lg" }: { album: Album; size?: "lg" | "sm" }) {
  const dim = size === "lg" ? "w-56 h-56 md:w-64 md:h-64" : "w-12 h-12";
  const textSize = size === "lg" ? "text-4xl" : "text-[10px]";
  return (
    <div
      className={`${dim} rounded-lg bg-gradient-to-br ${album.gradient} flex items-center justify-center shadow-lg`}
    >
      <span className={`font-serif ${textSize} text-white/40 italic select-none`}>
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
    { num: "02", label: "Rate some albums" },
    { num: "03", label: "See your rankings" },
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
        Welcome to{" "}
        <span className="italic">Sona.</span>
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
  const canContinue = selectedGenres.length >= 3;

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
          Select at least 3 genres to continue
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
   Step 3 — Rate Albums
   ───────────────────────────────────────────── */
function RateStep({
  albums,
  ratings,
  onRate,
  onSkip,
  onNext,
}: {
  albums: Album[];
  ratings: Record<string, number>;
  onRate: (albumId: string, value: number) => void;
  onSkip: (albumId: string) => void;
  onNext: () => void;
}) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [skipped, setSkipped] = useState<Set<string>>(new Set());

  const ratedCount = Object.keys(ratings).length;
  const canContinue = ratedCount >= 5;
  const album = albums[currentIndex];
  const isLast = currentIndex >= albums.length - 1;
  const allDone = currentIndex >= albums.length;

  const handleRate = (value: number) => {
    if (!album) return;
    onRate(album.id, value);
    if (!isLast) {
      setTimeout(() => setCurrentIndex((i) => i + 1), 300);
    } else {
      setTimeout(() => setCurrentIndex((i) => i + 1), 300);
    }
  };

  const handleSkip = () => {
    if (!album) return;
    setSkipped((prev) => new Set(prev).add(album.id));
    onSkip(album.id);
    setCurrentIndex((i) => i + 1);
  };

  if (allDone || !album) {
    return (
      <motion.div
        variants={stagger}
        initial="hidden"
        animate="show"
        className="flex flex-col items-center text-center max-w-lg mx-auto"
      >
        <motion.div variants={fadeUp}>
          <Star className="w-8 h-8 text-silver-dark mx-auto mb-4" strokeWidth={1.5} />
        </motion.div>
        <motion.h2 variants={fadeUp} className="font-serif text-3xl md:text-4xl tracking-tight mb-3">
          {canContinue ? (
            <>Albums <span className="italic">rated.</span></>
          ) : (
            <>Rate a few <span className="italic">more.</span></>
          )}
        </motion.h2>
        <motion.p variants={fadeUp} className="font-mono text-xs text-silver-dark mb-8">
          {canContinue
            ? `You rated ${ratedCount} album${ratedCount !== 1 ? "s" : ""}. Let's see your rankings.`
            : `You've rated ${ratedCount} of 5 required. Go back to rate more.`}
        </motion.p>
        {canContinue && (
          <motion.div variants={fadeUp}>
            <motion.button
              onClick={onNext}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              className="font-mono text-sm tracking-widest uppercase py-4 px-12 bg-foreground text-cream rounded-full hover:shadow-[0_8px_30px_rgba(0,0,0,0.12)] transition-shadow duration-300 inline-flex items-center gap-3"
            >
              See Rankings
              <ArrowRight className="w-4 h-4" />
            </motion.button>
          </motion.div>
        )}
        {!canContinue && (
          <motion.div variants={fadeUp}>
            <motion.button
              onClick={() => setCurrentIndex(0)}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              className="font-mono text-xs tracking-wide text-silver-dark hover:text-foreground transition-colors duration-300"
            >
              Start over
            </motion.button>
          </motion.div>
        )}
      </motion.div>
    );
  }

  return (
    <div className="flex flex-col items-center max-w-lg mx-auto">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] as const }}
        className="text-center mb-8"
      >
        <h2 className="font-serif text-3xl md:text-4xl tracking-tight mb-2">
          Rate these <span className="italic">albums.</span>
        </h2>
        <p className="font-mono text-xs text-silver-dark">
          {ratedCount} of {albums.length} rated &middot; {Math.max(0, 5 - ratedCount)} more needed
        </p>
      </motion.div>

      {/* Album Card */}
      <AnimatePresence mode="wait">
        <motion.div
          key={album.id}
          initial={{ opacity: 0, x: 40, scale: 0.97 }}
          animate={{ opacity: 1, x: 0, scale: 1 }}
          exit={{ opacity: 0, x: -40, scale: 0.97 }}
          transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] as const }}
          className="flex flex-col items-center w-full"
        >
          {/* Art */}
          <div className="mb-6 relative">
            <AlbumArt album={album} size="lg" />
            <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-cream-dark border border-silver-light flex items-center justify-center">
              <span className="font-mono text-[10px] text-silver-dark">
                {currentIndex + 1}
              </span>
            </div>
          </div>

          {/* Info */}
          <div className="text-center mb-8">
            <h3 className="font-serif text-xl md:text-2xl tracking-tight mb-1">
              {album.title}
            </h3>
            <p className="font-mono text-xs text-silver-dark">
              {album.artist} &middot; {album.year}
            </p>
          </div>

          {/* Rating Scale */}
          <div className="flex items-center gap-1.5 mb-5 flex-wrap justify-center">
            {Array.from({ length: 10 }, (_, i) => i + 1).map((val) => {
              const isSelected = ratings[album.id] === val;
              return (
                <motion.button
                  key={val}
                  onClick={() => handleRate(val)}
                  whileHover={{ scale: 1.15 }}
                  whileTap={{ scale: 0.9 }}
                  animate={{
                    backgroundColor: isSelected ? "#171717" : "transparent",
                    color: isSelected ? "#f5f0e8" : "#8a8a8a",
                    borderColor: isSelected ? "#171717" : "#d4d4d4",
                  }}
                  transition={{ type: "spring", stiffness: 500, damping: 30 }}
                  className="w-10 h-10 md:w-11 md:h-11 rounded-full border font-mono text-sm flex items-center justify-center"
                >
                  {val}
                </motion.button>
              );
            })}
          </div>

          {/* Labels */}
          <div className="flex justify-between w-full max-w-xs mb-6 px-1">
            <span className="font-mono text-[9px] text-silver tracking-wider uppercase">
              Terrible
            </span>
            <span className="font-mono text-[9px] text-silver tracking-wider uppercase">
              Masterpiece
            </span>
          </div>

          {/* Skip */}
          <motion.button
            onClick={handleSkip}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="font-mono text-[11px] text-silver hover:text-silver-dark transition-colors duration-300 inline-flex items-center gap-2"
          >
            <SkipForward className="w-3 h-3" />
            Haven&apos;t heard it
          </motion.button>
        </motion.div>
      </AnimatePresence>

      {/* Mini progress */}
      <div className="flex items-center gap-1 mt-8">
        {albums.map((a, i) => (
          <div
            key={a.id}
            className={`h-1 rounded-full transition-all duration-300 ${
              i === currentIndex
                ? "w-4 bg-foreground"
                : ratings[a.id]
                ? "w-1.5 bg-foreground/40"
                : skipped.has(a.id)
                ? "w-1.5 bg-silver-light"
                : "w-1.5 bg-silver-light/50"
            }`}
          />
        ))}
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   Step 4 — Completion
   ───────────────────────────────────────────── */
function CompletionStep({
  ratings,
  albums,
}: {
  ratings: Record<string, number>;
  albums: Album[];
}) {
  const router = useRouter();

  const rankedAlbums = useMemo(() => {
    return Object.entries(ratings)
      .map(([albumId, rating]) => {
        const album = albums.find((a) => a.id === albumId);
        if (!album) return null;
        const elo = Math.round(rating * 50 + 1200 + (Math.random() * 30 - 15));
        return { album, rating, elo };
      })
      .filter(Boolean)
      .sort((a, b) => b!.elo - a!.elo)
      .slice(0, 5) as { album: Album; rating: number; elo: number }[];
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <motion.div
      variants={stagger}
      initial="hidden"
      animate="show"
      className="flex flex-col items-center max-w-lg mx-auto"
    >
      <motion.div variants={fadeUp} className="text-center mb-10">
        <Music className="w-8 h-8 text-silver-dark mx-auto mb-4" strokeWidth={1.5} />
        <h2 className="font-serif text-4xl md:text-5xl tracking-tight mb-3">
          You&apos;re all <span className="italic">set.</span>
        </h2>
        <p className="font-mono text-xs text-silver-dark leading-relaxed">
          Your initial taste profile is ready. Here are your top albums.
        </p>
      </motion.div>

      {/* Rankings */}
      <motion.div variants={fadeUp} className="w-full space-y-3 mb-12">
        {rankedAlbums.map((item, i) => (
          <motion.div
            key={item.album.id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{
              duration: 0.5,
              delay: 0.3 + i * 0.1,
              ease: [0.16, 1, 0.3, 1] as const,
            }}
            className="flex items-center gap-4 p-3 rounded-xl bg-cream-dark/50 border border-silver-light/30"
          >
            {/* Rank */}
            <span className="font-serif text-2xl text-silver-light w-8 text-center italic">
              {i + 1}
            </span>

            {/* Art */}
            <AlbumArt album={item.album} size="sm" />

            {/* Info */}
            <div className="flex-1 min-w-0">
              <p className="font-serif text-sm tracking-tight truncate">
                {item.album.title}
              </p>
              <p className="font-mono text-[10px] text-silver-dark truncate">
                {item.album.artist}
              </p>
            </div>

            {/* Elo */}
            <div className="text-right">
              <span className="font-mono text-xs text-foreground">{item.elo}</span>
              <p className="font-mono text-[8px] text-silver tracking-widest uppercase">
                Elo
              </p>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* CTAs */}
      <motion.div variants={fadeUp} className="flex flex-col sm:flex-row items-center gap-3 w-full">
        <motion.button
          onClick={() => router.push("/dashboard")}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          className="w-full sm:w-auto flex-1 font-mono text-sm tracking-widest uppercase py-4 px-8 bg-foreground text-cream rounded-full hover:shadow-[0_8px_30px_rgba(0,0,0,0.12)] transition-shadow duration-300 text-center"
        >
          Dashboard
        </motion.button>
        <motion.button
          onClick={() => router.push("/recommendations")}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          className="w-full sm:w-auto flex-1 font-mono text-xs tracking-wide py-4 px-8 border border-silver-light rounded-full text-silver-dark hover:border-foreground hover:text-foreground transition-colors duration-300 text-center inline-flex items-center justify-center gap-2"
        >
          Recommendations
          <ArrowRight className="w-3.5 h-3.5" />
        </motion.button>
      </motion.div>
    </motion.div>
  );
}

/* ─────────────────────────────────────────────
   Main Onboarding Page
   ───────────────────────────────────────────── */
export default function OnboardingPage() {
  const [step, setStep] = useState(1);
  const [direction, setDirection] = useState(1);
  const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
  const [ratings, setRatings] = useState<Record<string, number>>({});

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

  const handleRate = useCallback((albumId: string, value: number) => {
    setRatings((prev) => ({ ...prev, [albumId]: value }));
  }, []);

  const handleSkip = useCallback((_albumId: string) => {
    // no-op for now, skipped albums just aren't rated
  }, []);

  // Filter albums by selected genres
  const filteredAlbums = useMemo(() => {
    if (selectedGenres.length === 0) return ALBUMS;
    return ALBUMS.filter((album) =>
      album.genres.some((g) => selectedGenres.includes(g))
    );
  }, [selectedGenres]);

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Progress */}
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
            transition={{
              duration: 0.4,
              ease: [0.16, 1, 0.3, 1],
            }}
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
              <RateStep
                albums={filteredAlbums}
                ratings={ratings}
                onRate={handleRate}
                onSkip={handleSkip}
                onNext={goNext}
              />
            )}
            {step === 4 && (
              <CompletionStep ratings={ratings} albums={filteredAlbums} />
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
