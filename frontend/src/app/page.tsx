"use client";

import { motion, useScroll, useTransform } from "framer-motion";
import {
  ArrowDown,
  Disc3,
  BarChart3,
  GitCompareArrows,
  Sparkles,
  Search,
} from "lucide-react";
import { useRef, useState, useEffect } from "react";

/* ─────────────────────────────────────────────
   Grain Overlay — analog noise texture
   ───────────────────────────────────────────── */
function GrainOverlay() {
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 z-100 opacity-[0.04] mix-blend-multiply"
      style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
        backgroundRepeat: "repeat",
        backgroundSize: "200px 200px",
      }}
    />
  );
}

/* ─────────────────────────────────────────────
   Navbar
   ───────────────────────────────────────────── */
function Navbar() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <motion.nav
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8, delay: 0.8 }}
      className={`fixed top-4 left-50 right-50 z-50 flex items-center justify-between px-8 md:px-16 lg:px-24 py-5 transition-all duration-500 ${
        scrolled
          ? "top-4 bg-background/50 backdrop-blur-xl border border-silver-light/40 rounded-2xl"
          : ""
      }`}
    >
      <span className="font-serif text-xl tracking-tight">RateMyAlbum</span>
      <div className="flex items-center gap-6">
        <a
          href="/login"
          className="hidden sm:block font-mono text-[11px] tracking-[0.15em] uppercase text-silver-dark hover:text-foreground transition-colors duration-300"
        >
          Sign in
        </a>
        <a
          href="/register"
          className="font-mono text-[11px] tracking-[0.15em] uppercase px-5 py-2.5 border border-silver rounded-full hover:bg-foreground hover:text-cream hover:border-foreground transition-all duration-300"
        >
          Get Started
        </a>
      </div>
    </motion.nav>
  );
}

/* ─────────────────────────────────────────────
   Spinning Vinyl
   ───────────────────────────────────────────── */
function SpinningVinyl() {
  return (
    <div className="absolute top-1/2 -translate-y-1/2 right-0 translate-x-1/2 pointer-events-none select-none">
      <div className="vinyl relative w-[600px] h-[600px] md:w-[700px] md:h-[700px] lg:w-[800px] lg:h-[800px] rounded-full bg-[radial-gradient(ellipse_at_30%_30%,#3a3a3a,#1a1a1a_40%,#0d0d0d_70%,#000000)]">
        <div className="absolute inset-0 rounded-full border-2 border-zinc-600/20" />
        <div className="absolute inset-px rounded-full border border-zinc-800/40" />
        <div className="vinyl-grooves absolute inset-[4%] rounded-full" />
        <div className="vinyl-shine absolute inset-0 rounded-full" />
        <div className="vinyl-iridescence absolute inset-0 rounded-full" />
        <div className="absolute inset-[4%] rounded-full border border-zinc-700/15" />
        <div className="absolute inset-[6%] rounded-full border border-zinc-600/10" />
        <div className="absolute inset-[10%] rounded-full border border-zinc-700/10" />
        <div className="absolute inset-[15%] rounded-full border border-zinc-600/8" />
        <div className="absolute inset-[20%] rounded-full border border-zinc-700/10" />
        <div className="absolute inset-[25%] rounded-full border border-zinc-600/6" />
        <div className="absolute inset-[30%] rounded-full border border-zinc-700/8" />
        <div className="absolute inset-[34%] rounded-full border border-zinc-600/10" />
        <div className="absolute inset-[36%] rounded-full bg-[radial-gradient(ellipse_at_40%_35%,#e8e0d0,#c8c0b0_50%,#a8a098_100%)] shadow-[inset_0_2px_8px_rgba(0,0,0,0.15)]">
          <div className="absolute inset-[8%] rounded-full border border-black/5" />
          <div className="absolute inset-[15%] rounded-full border border-black/3" />
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="font-serif text-[10px] md:text-xs text-zinc-600/60 tracking-[0.2em] uppercase">
              RateMyAlbum
            </span>
            <div className="w-[30%] h-px bg-zinc-500/20 my-1.5" />
            <span className="font-mono text-[7px] md:text-[8px] text-zinc-500/40 tracking-wider">
              33 RPM
            </span>
          </div>
          <div className="absolute inset-[42%] rounded-full bg-[radial-gradient(circle,#2a2a2a,#1a1a1a)] shadow-[inset_0_1px_3px_rgba(0,0,0,0.4)]" />
        </div>
        <div className="vinyl-shimmer absolute inset-0 rounded-full bg-[radial-gradient(ellipse_at_25%_25%,rgba(255,255,255,0.06),transparent_60%)]" />
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   Search Bar
   ───────────────────────────────────────────── */
function SearchBar() {
  const [query, setQuery] = useState("");

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, delay: 0.6, ease: [0, 0, 0.2, 1] }}
      className="w-full max-w-md"
    >
      <div className="group relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-silver-dark group-focus-within:text-foreground transition-colors duration-300" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search for an album..."
          className="w-full font-mono text-sm bg-cream-dark/60 border border-silver-light rounded-full py-3.5 pl-11 pr-5 text-foreground placeholder:text-silver-dark outline-none focus:border-silver-dark focus:bg-cream-dark focus:shadow-[0_0_0_4px_rgba(0,0,0,0.03)] transition-all duration-300"
        />
      </div>
      <p className="font-mono text-[11px] text-silver mt-3 ml-4">
        Try &ldquo;OK Computer&rdquo; or &ldquo;Kind of Blue&rdquo;
      </p>
    </motion.div>
  );
}

/* ─────────────────────────────────────────────
   Hero Section
   ───────────────────────────────────────────── */
const heroLines = [
  { words: ["Rank", "your"], italic: false },
  { words: ["music,", "discover"], italic: false },
  { words: ["your taste."], italic: true },
];

function HeroSection() {
  let wordIndex = 0;

  return (
    <section className="relative min-h-screen flex items-center overflow-hidden">
      <SpinningVinyl />

      <div className="relative z-10 flex flex-col items-start gap-8 px-10 md:px-24 lg:px-40 max-w-3xl pt-20">
        <h1 className="font-serif text-[3.25rem] md:text-[4.75rem] lg:text-[6.5rem] tracking-tight text-foreground leading-[0.95]">
          {heroLines.map((line, lineIdx) => (
            <span key={lineIdx} className="block overflow-hidden">
              {line.words.map((word) => {
                const delay = 0.1 + wordIndex * 0.07;
                wordIndex++;
                return (
                  <motion.span
                    key={word}
                    initial={{ y: "110%", opacity: 0 }}
                    animate={{ y: "0%", opacity: 1 }}
                    transition={{
                      duration: 0.8,
                      delay,
                      ease: [0.16, 1, 0.3, 1],
                    }}
                    className={`inline-block mr-[0.22em] ${
                      line.italic ? "italic" : ""
                    }`}
                  >
                    {word}
                  </motion.span>
                );
              })}
            </span>
          ))}
        </h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.55, ease: [0, 0, 0.2, 1] }}
          className="font-mono text-sm md:text-base text-silver-dark max-w-sm tracking-wide leading-relaxed"
        >
          Rate albums, compare them head-to-head, and build
          rankings that actually mean something.
        </motion.p>

        <SearchBar />
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2, duration: 1 }}
        className="absolute bottom-10 left-10 md:left-20 lg:left-30 z-10"
      >
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        >
          <ArrowDown className="w-5 h-5 text-silver" />
        </motion.div>
      </motion.div>
    </section>
  );
}

/* ─────────────────────────────────────────────
   Comparison Demo
   ───────────────────────────────────────────── */
function ComparisonDemo() {
  const [hovered, setHovered] = useState<"left" | "right" | null>(null);

  return (
    <section className="py-24 px-8 md:px-16 lg:px-24">
      <div className="max-w-3xl mx-auto">
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.6 }}
          className="font-mono text-xs tracking-[0.3em] uppercase text-silver-dark mb-4 text-center"
        >
          The core interaction
        </motion.p>
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="font-serif text-4xl md:text-5xl tracking-tight mb-16 text-center"
        >
          Which one wins?
        </motion.h2>

        <div className="flex items-center justify-center gap-4 md:gap-8">
          {/* Album A */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="flex-1 max-w-56"
          >
            <motion.div
              onHoverStart={() => setHovered("left")}
              onHoverEnd={() => setHovered(null)}
              animate={{
                scale: hovered === "left" ? 1.03 : hovered === "right" ? 0.97 : 1,
                opacity: hovered === "right" ? 0.5 : 1,
              }}
              transition={{ duration: 0.3 }}
              className="cursor-pointer group"
            >
              <div
                className="aspect-square rounded-lg shadow-lg group-hover:shadow-xl transition-shadow duration-300 relative overflow-hidden"
                style={{
                  background:
                    "linear-gradient(135deg, #1a1a4e 0%, #2d3561 50%, #1a2744 100%)",
                }}
              >
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_30%_30%,rgba(255,255,255,0.08),transparent_60%)]" />
                <div className="absolute bottom-3 left-3 right-3">
                  <div className="w-full h-px bg-white/10 mb-2" />
                  <div className="w-2/3 h-px bg-white/5" />
                </div>
              </div>
              <p className="font-serif text-lg mt-3">OK Computer</p>
              <p className="font-mono text-xs text-silver-dark">
                Radiohead &middot; 1997
              </p>
            </motion.div>
          </motion.div>

          {/* VS */}
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.4 }}
            className="shrink-0"
          >
            <span className="font-serif text-2xl md:text-3xl text-silver-light italic">
              vs
            </span>
          </motion.div>

          {/* Album B */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="flex-1 max-w-56"
          >
            <motion.div
              onHoverStart={() => setHovered("right")}
              onHoverEnd={() => setHovered(null)}
              animate={{
                scale:
                  hovered === "right" ? 1.03 : hovered === "left" ? 0.97 : 1,
                opacity: hovered === "left" ? 0.5 : 1,
              }}
              transition={{ duration: 0.3 }}
              className="cursor-pointer group"
            >
              <div
                className="aspect-square rounded-lg shadow-lg group-hover:shadow-xl transition-shadow duration-300 relative overflow-hidden"
                style={{
                  background:
                    "linear-gradient(135deg, #5c3a1a 0%, #8b5e3c 50%, #3d2510 100%)",
                }}
              >
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_70%_30%,rgba(255,255,255,0.06),transparent_60%)]" />
                <div className="absolute bottom-3 left-3 right-3">
                  <div className="w-full h-px bg-white/10 mb-2" />
                  <div className="w-1/2 h-px bg-white/5" />
                </div>
              </div>
              <p className="font-serif text-lg mt-3">Kid A</p>
              <p className="font-mono text-xs text-silver-dark">
                Radiohead &middot; 2000
              </p>
            </motion.div>
          </motion.div>
        </div>

        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="text-center font-mono text-xs text-silver mt-10"
        >
          Hover to pick a side. Your choice is the strongest ranking signal.
        </motion.p>
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────
   Marquee Strip
   ───────────────────────────────────────────── */
const genres = [
  "Jazz",
  "Hip-Hop",
  "Rock",
  "Electronic",
  "Soul",
  "Classical",
  "Punk",
  "R&B",
  "Folk",
  "Ambient",
  "Metal",
  "Pop",
  "Blues",
  "Indie",
  "Funk",
];

function MarqueeStrip() {
  return (
    <div className="py-5 border-y border-silver-light/50 overflow-hidden">
      <motion.div
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
      >
        <div className="marquee-track flex whitespace-nowrap">
          {[...genres, ...genres].map((genre, i) => (
            <span
              key={i}
              className="font-serif text-xl md:text-2xl text-silver-dark shrink-0 select-none"
            >
              {genre}
              <span className="inline-block mx-5 md:mx-8 text-silver">
                &middot;
              </span>
            </span>
          ))}
        </div>
      </motion.div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   Stats Strip
   ───────────────────────────────────────────── */
const stats = [
  { value: "Fully", label: "Ordered rankings" },
  { value: "Zero", label: "Tier lists" },
  { value: "∞", label: "Precision" },
];

function StatsStrip() {
  return (
    <section className="py-16 px-8 md:px-16 lg:px-24">
      <div className="max-w-3xl mx-auto flex justify-center gap-12 md:gap-24">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.5, delay: i * 0.1 }}
            className="text-center"
          >
            <span className="font-serif text-4xl md:text-5xl block mb-1">
              {stat.value}
            </span>
            <p className="font-mono text-[10px] md:text-[11px] text-silver-dark tracking-wide uppercase">
              {stat.label}
            </p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────
   Features Section
   ───────────────────────────────────────────── */
const features = [
  {
    icon: Disc3,
    number: "01",
    title: "Rate with precision",
    description:
      "Give every album a score from 1 to 10. Your ratings feed into a personal Elo system that learns what you truly love.",
  },
  {
    icon: GitCompareArrows,
    number: "02",
    title: "Compare head-to-head",
    description:
      "Which album is better? Pairwise comparisons are the strongest signal. Pick a winner and watch your rankings sharpen.",
  },
  {
    icon: BarChart3,
    number: "03",
    title: "Rankings, not tiers",
    description:
      "No S-tier nonsense. Every album has a unique position in your fully ordered, continuously refined ranking.",
  },
  {
    icon: Sparkles,
    number: "04",
    title: "Discover what's next",
    description:
      "Your rankings train a taste profile. We surface albums you'll actually love — not just what's trending.",
  },
];

function FeaturesSection() {
  return (
    <section className="py-32 px-8 md:px-16 lg:px-24">
      <div className="max-w-5xl mx-auto text-center">
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="font-mono text-xs tracking-[0.3em] uppercase text-silver-dark mb-4"
        >
          How it works
        </motion.p>

        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="font-serif text-5xl md:text-7xl tracking-tight mb-24"
        >
          Every opinion counts.
          <br />
          <span className="italic text-silver-dark">Literally.</span>
        </motion.h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-16 gap-y-20 text-left max-w-4xl mx-auto">
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              className="group relative pl-6 border-l border-silver-light hover:border-foreground transition-colors duration-500"
            >
              <span className="absolute -top-6 -left-3 font-serif text-[4.5rem] leading-none text-silver-light/25 select-none pointer-events-none group-hover:text-silver-light/40 transition-colors duration-500">
                {feature.number}
              </span>

              <div className="relative flex items-start gap-5">
                <div className="shrink-0 w-11 h-11 rounded-full border border-silver-light flex items-center justify-center group-hover:border-foreground group-hover:bg-foreground transition-all duration-400">
                  <feature.icon className="w-4.5 h-4.5 text-silver-dark group-hover:text-cream transition-colors duration-400" />
                </div>
                <div>
                  <h3 className="font-serif text-2xl mb-2">{feature.title}</h3>
                  <p className="font-mono text-sm text-silver-dark leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────
   Ranking Showcase
   ───────────────────────────────────────────── */
const rankingData = [
  {
    rank: 1,
    title: "OK Computer",
    artist: "Radiohead",
    elo: 1847,
    gradient: "linear-gradient(135deg, #1a1a4e, #2d3561)",
  },
  {
    rank: 2,
    title: "Kind of Blue",
    artist: "Miles Davis",
    elo: 1823,
    gradient: "linear-gradient(135deg, #1a3a5c, #0d2137)",
  },
  {
    rank: 3,
    title: "Loveless",
    artist: "My Bloody Valentine",
    elo: 1801,
    gradient: "linear-gradient(135deg, #4a1942, #2d1028)",
  },
  {
    rank: 4,
    title: "In Rainbows",
    artist: "Radiohead",
    elo: 1789,
    gradient: "linear-gradient(135deg, #5c3a1a, #3d2510)",
  },
  {
    rank: 5,
    title: "Vespertine",
    artist: "Björk",
    elo: 1776,
    gradient: "linear-gradient(135deg, #1a4a4a, #0d2d2d)",
  },
];

function RankingShowcase() {
  return (
    <section className="py-32 px-8 md:px-16 lg:px-24 bg-cream-dark">
      <div className="max-w-2xl mx-auto">
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.6 }}
          className="font-mono text-xs tracking-[0.3em] uppercase text-silver-dark mb-4 text-center"
        >
          Your ranking
        </motion.p>
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="font-serif text-4xl md:text-5xl tracking-tight mb-16 text-center"
        >
          A living leaderboard.
        </motion.h2>

        <div className="space-y-2">
          {rankingData.map((album, i) => (
            <motion.div
              key={album.rank}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-30px" }}
              transition={{ duration: 0.4, delay: i * 0.07 }}
              className="group flex items-center gap-4 py-3.5 px-5 rounded-xl hover:bg-cream transition-colors duration-300"
            >
              <span className="font-mono text-sm text-silver w-7 shrink-0">
                {String(album.rank).padStart(2, "0")}
              </span>
              <div
                className="w-10 h-10 rounded-md shrink-0 shadow-sm"
                style={{ background: album.gradient }}
              />
              <div className="flex-1 min-w-0">
                <p className="font-serif text-lg leading-tight truncate">
                  {album.title}
                </p>
                <p className="font-mono text-[11px] text-silver-dark truncate">
                  {album.artist}
                </p>
              </div>
              <span className="font-mono text-xs text-silver-dark tabular-nums group-hover:text-foreground transition-colors duration-300">
                {album.elo}
              </span>
            </motion.div>
          ))}
        </div>

        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="text-center font-mono text-[11px] text-silver mt-8"
        >
          Every album has a unique Elo score. No ties, no tiers.
        </motion.p>
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────
   Step Illustrations
   ───────────────────────────────────────────── */
function StepVisual({ type }: { type: string }) {
  if (type === "search") {
    return (
      <div className="flex items-center gap-2 px-3 py-2 rounded-full border border-silver-light/50 w-fit">
        <div className="w-2.5 h-2.5 rounded-full border border-silver/50" />
        <div className="w-12 h-px bg-silver-light/40" />
      </div>
    );
  }
  if (type === "rate") {
    return (
      <div className="flex gap-1">
        {Array.from({ length: 10 }).map((_, i) => (
          <div
            key={i}
            className={`w-2 h-2 rounded-full ${
              i < 8 ? "bg-foreground/20" : "bg-silver-light/30"
            }`}
          />
        ))}
      </div>
    );
  }
  if (type === "compare") {
    return (
      <div className="relative w-16 h-12">
        <div className="absolute left-0 top-0 w-10 h-11 rounded-md border border-silver-light/50 bg-cream-dark" />
        <div className="absolute right-0 bottom-0 w-10 h-11 rounded-md border border-silver/40 bg-cream" />
      </div>
    );
  }
  if (type === "discover") {
    return (
      <div className="grid grid-cols-3 gap-1 w-fit">
        {[0.15, 0.25, 0.1, 0.3, 0.12, 0.35, 0.08, 0.22, 0.18].map(
          (opacity, i) => (
            <div
              key={i}
              className="w-3 h-3 rounded-sm"
              style={{ backgroundColor: `rgba(23, 23, 23, ${opacity})` }}
            />
          )
        )}
      </div>
    );
  }
  return null;
}

/* ─────────────────────────────────────────────
   Steps Section
   ───────────────────────────────────────────── */
const steps = [
  {
    number: "01",
    label: "Search",
    description: "Find any album from our catalog",
    visual: "search",
  },
  {
    number: "02",
    label: "Rate",
    description: "Give it a score from 1 to 10",
    visual: "rate",
  },
  {
    number: "03",
    label: "Compare",
    description: "Pick winners in head-to-head matchups",
    visual: "compare",
  },
  {
    number: "04",
    label: "Discover",
    description: "Get recommendations that actually fit",
    visual: "discover",
  },
];

function StepsSection() {
  const containerRef = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"],
  });
  const lineHeight = useTransform(
    scrollYProgress,
    [0.1, 0.7],
    ["0%", "100%"]
  );

  return (
    <section
      ref={containerRef}
      className="py-32 px-8 md:px-16 lg:px-24"
    >
      <div className="max-w-3xl mx-auto text-center">
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="font-mono text-xs tracking-[0.3em] uppercase text-silver-dark mb-4"
        >
          The loop
        </motion.p>

        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="font-serif text-5xl md:text-7xl tracking-tight mb-24"
        >
          Four steps.
          <br />
          <span className="italic text-silver-dark">Infinite refinement.</span>
        </motion.h2>

        <div className="relative inline-block text-left">
          <div className="absolute left-5.75 top-0 bottom-0 w-px bg-silver-light">
            <motion.div
              className="w-full bg-foreground origin-top"
              style={{ height: lineHeight }}
            />
          </div>

          <div className="space-y-16">
            {steps.map((step, i) => (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                className="flex items-start gap-8 md:gap-10 group cursor-default"
              >
                <div className="relative shrink-0 w-12 h-12 rounded-full bg-background border border-silver-light flex items-center justify-center group-hover:border-foreground group-hover:bg-foreground transition-all duration-300 z-10">
                  <span className="font-mono text-sm text-silver-dark group-hover:text-cream transition-colors duration-300">
                    {step.number}
                  </span>
                </div>
                <div className="pt-1.5 flex-1">
                  <h3 className="font-serif text-3xl md:text-4xl mb-1 group-hover:translate-x-1 transition-transform duration-300">
                    {step.label}
                  </h3>
                  <p className="font-mono text-sm md:text-base text-silver-dark mb-3">
                    {step.description}
                  </p>
                  <StepVisual type={step.visual} />
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────
   Taste Profile
   ───────────────────────────────────────────── */
const tastes = [
  { genre: "Art Rock", pct: 89 },
  { genre: "Jazz", pct: 74 },
  { genre: "Electronic", pct: 61 },
  { genre: "Hip-Hop", pct: 48 },
  { genre: "Classical", pct: 35 },
];

function TasteProfile() {
  return (
    <section className="py-32 px-8 md:px-16 lg:px-24 bg-cream-dark">
      <div className="max-w-4xl mx-auto">
        <div className="flex flex-col md:flex-row gap-16 md:gap-20 items-start md:items-center">
          <div className="md:w-1/2">
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.6 }}
              className="font-mono text-xs tracking-[0.3em] uppercase text-silver-dark mb-4"
            >
              Your taste DNA
            </motion.p>
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="font-serif text-4xl md:text-5xl tracking-tight mb-5"
            >
              More than
              <br />
              <span className="italic">a playlist.</span>
            </motion.h2>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="font-mono text-sm text-silver-dark leading-relaxed"
            >
              Every ranking builds a detailed taste profile. See what genres
              define you — and find music that matches.
            </motion.p>
          </div>
          <div className="md:w-1/2 space-y-5 w-full">
            {tastes.map((taste, i) => (
              <motion.div
                key={taste.genre}
                initial={{ opacity: 0, x: 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-30px" }}
                transition={{ duration: 0.5, delay: i * 0.08 }}
              >
                <div className="flex justify-between mb-1.5">
                  <span className="font-mono text-xs text-silver-dark">
                    {taste.genre}
                  </span>
                  <span className="font-mono text-xs text-silver">
                    {taste.pct}%
                  </span>
                </div>
                <div className="h-1.5 bg-silver-light/25 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    whileInView={{ width: `${taste.pct}%` }}
                    viewport={{ once: true }}
                    transition={{
                      duration: 0.8,
                      delay: 0.2 + i * 0.1,
                      ease: [0, 0, 0.2, 1],
                    }}
                    className="h-full bg-foreground/15 rounded-full"
                  />
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────
   Bottom CTA
   ───────────────────────────────────────────── */
function BottomCTA() {
  return (
    <section className="py-40 px-8 md:px-16 lg:px-24 relative overflow-hidden">
      {/* Decorative concentric circles */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-150 h-150 rounded-full border border-silver-light/20 pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-100 h-100 rounded-full border border-silver-light/15 pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-50 h-50 rounded-full border border-silver-light/10 pointer-events-none" />

      <div className="max-w-3xl mx-auto text-center relative z-10">
        <motion.h2
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="font-serif text-5xl md:text-7xl tracking-tight mb-6"
        >
          Ready to find out
          <br />
          <span className="italic">what you really think?</span>
        </motion.h2>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="font-mono text-base text-silver-dark mb-14"
        >
          Your music taste deserves more than a playlist algorithm.
        </motion.p>

        <motion.a
          href="/register"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6, delay: 0.2 }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.97 }}
          className="inline-block font-mono text-sm tracking-widest uppercase px-12 py-5 bg-foreground text-cream rounded-full hover:shadow-[0_8px_30px_rgba(0,0,0,0.12)] transition-shadow duration-300"
        >
          Start Ranking
        </motion.a>
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────
   Footer
   ───────────────────────────────────────────── */
function Footer() {
  return (
    <footer className="py-12 px-8 md:px-16 lg:px-24 border-t border-silver-light bg-cream-dark">
      <div className="max-w-5xl mx-auto">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-8">
          <div>
            <span className="font-serif text-xl block mb-1">RateMyAlbum</span>
            <span className="font-mono text-[11px] text-silver-dark">
              Rank the music you love.
            </span>
          </div>
          <div className="flex items-center gap-8">
            <a
              href="/about"
              className="font-mono text-[11px] text-silver-dark hover:text-foreground transition-colors duration-300 tracking-wide uppercase"
            >
              About
            </a>
            <a
              href="/privacy"
              className="font-mono text-[11px] text-silver-dark hover:text-foreground transition-colors duration-300 tracking-wide uppercase"
            >
              Privacy
            </a>
            <a
              href="/terms"
              className="font-mono text-[11px] text-silver-dark hover:text-foreground transition-colors duration-300 tracking-wide uppercase"
            >
              Terms
            </a>
          </div>
        </div>
        <div className="mt-8 pt-6 border-t border-silver-light/50 flex items-center justify-between">
          <span className="font-mono text-[11px] text-silver">
            &copy; {new Date().getFullYear()} RateMyAlbum
          </span>
          <span className="font-mono text-[10px] text-silver-light tracking-widest uppercase">
            Every album has a place
          </span>
        </div>
      </div>
    </footer>
  );
}

/* ─────────────────────────────────────────────
   Page
   ───────────────────────────────────────────── */
export default function Home() {
  return (
    <main className="bg-background text-foreground overflow-x-hidden">
      <GrainOverlay />
      <Navbar />
      <HeroSection />
      <ComparisonDemo />
      <MarqueeStrip />
      <StatsStrip />
      <FeaturesSection />
      <RankingShowcase />
      <StepsSection />
      <TasteProfile />
      <BottomCTA />
      <Footer />
    </main>
  );
}
