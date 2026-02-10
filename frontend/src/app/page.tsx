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
      className="pointer-events-none fixed inset-0 z-[100] opacity-[0.04] mix-blend-multiply"
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
      className={`fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-8 md:px-16 lg:px-24 py-5 transition-all duration-500 ${
        scrolled
          ? "bg-background/80 backdrop-blur-xl border-b border-silver-light/40"
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
    <div className="absolute top-1/2 -translate-y-1/2 -right-[280px] md:-right-[250px] lg:-right-[200px] pointer-events-none select-none">
      <div className="vinyl relative w-[560px] h-[560px] md:w-[640px] md:h-[640px] lg:w-[720px] lg:h-[720px] rounded-full bg-[radial-gradient(ellipse_at_30%_30%,#3a3a3a,#1a1a1a_40%,#0d0d0d_70%,#000000)]">
        {/* Outer bevel / rim */}
        <div className="absolute inset-0 rounded-full border-2 border-zinc-600/20" />
        <div className="absolute inset-[1px] rounded-full border border-zinc-800/40" />

        {/* Grooves */}
        <div className="vinyl-grooves absolute inset-[4%] rounded-full" />

        {/* Shine sweep */}
        <div className="vinyl-shine absolute inset-0 rounded-full" />

        {/* Iridescence layer */}
        <div className="vinyl-iridescence absolute inset-0 rounded-full" />

        {/* Outer dead wax area */}
        <div className="absolute inset-[4%] rounded-full border border-zinc-700/15" />
        <div className="absolute inset-[6%] rounded-full border border-zinc-600/10" />

        {/* Inner groove rings */}
        <div className="absolute inset-[10%] rounded-full border border-zinc-700/10" />
        <div className="absolute inset-[15%] rounded-full border border-zinc-600/8" />
        <div className="absolute inset-[20%] rounded-full border border-zinc-700/10" />
        <div className="absolute inset-[25%] rounded-full border border-zinc-600/6" />
        <div className="absolute inset-[30%] rounded-full border border-zinc-700/8" />
        <div className="absolute inset-[34%] rounded-full border border-zinc-600/10" />

        {/* Label area */}
        <div className="absolute inset-[36%] rounded-full bg-[radial-gradient(ellipse_at_40%_35%,#e8e0d0,#c8c0b0_50%,#a8a098_100%)] shadow-[inset_0_2px_8px_rgba(0,0,0,0.15)]">
          {/* Label texture */}
          <div className="absolute inset-[8%] rounded-full border border-black/5" />
          <div className="absolute inset-[15%] rounded-full border border-black/3" />

          {/* Label text area */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="font-serif text-[10px] md:text-xs text-zinc-600/60 tracking-[0.2em] uppercase">
              RateMyAlbum
            </span>
            <div className="w-[30%] h-px bg-zinc-500/20 my-1.5" />
            <span className="font-mono text-[7px] md:text-[8px] text-zinc-500/40 tracking-wider">
              33 RPM
            </span>
          </div>

          {/* Spindle hole */}
          <div className="absolute inset-[42%] rounded-full bg-[radial-gradient(circle,#2a2a2a,#1a1a1a)] shadow-[inset_0_1px_3px_rgba(0,0,0,0.4)]" />
        </div>

        {/* Shimmer overlay */}
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
      className="w-full max-w-[28rem]"
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

      <div className="relative z-10 flex flex-col items-start gap-8 px-10 md:px-20 lg:px-30 max-w-3xl pt-20">
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
              className="font-serif text-xl md:text-2xl text-silver-light shrink-0 select-none"
            >
              {genre}
              <span className="inline-block mx-5 md:mx-8 text-silver-light/40">
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
    <section className="py-40 px-8 md:px-16 lg:px-24">
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
          className="font-serif text-5xl md:text-7xl tracking-tight mb-28"
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
              {/* Large watermark number */}
              <span className="absolute -top-6 -left-3 font-serif text-[4.5rem] leading-none text-silver-light/25 select-none pointer-events-none group-hover:text-silver-light/40 transition-colors duration-500">
                {feature.number}
              </span>

              <div className="relative flex items-start gap-5">
                <div className="shrink-0 w-11 h-11 rounded-full border border-silver-light flex items-center justify-center group-hover:border-foreground group-hover:bg-foreground transition-all duration-400">
                  <feature.icon className="w-[18px] h-[18px] text-silver-dark group-hover:text-cream transition-colors duration-400" />
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
   Steps Section
   ───────────────────────────────────────────── */
const steps = [
  {
    number: "01",
    label: "Search",
    description: "Find any album from our catalog",
  },
  {
    number: "02",
    label: "Rate",
    description: "Give it a score from 1 to 10",
  },
  {
    number: "03",
    label: "Compare",
    description: "Pick winners in head-to-head matchups",
  },
  {
    number: "04",
    label: "Discover",
    description: "Get recommendations that actually fit",
  },
];

function StepsSection() {
  const containerRef = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"],
  });
  const lineHeight = useTransform(scrollYProgress, [0.1, 0.7], ["0%", "100%"]);

  return (
    <section
      ref={containerRef}
      className="py-40 px-8 md:px-16 lg:px-24 bg-cream-dark"
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
          className="font-serif text-5xl md:text-7xl tracking-tight mb-28"
        >
          Four steps.
          <br />
          <span className="italic text-silver-dark">Infinite refinement.</span>
        </motion.h2>

        <div className="relative inline-block text-left">
          {/* Animated progress line */}
          <div className="absolute left-[23px] top-0 bottom-0 w-px bg-silver-light">
            <motion.div
              className="w-full bg-foreground origin-top"
              style={{ height: lineHeight }}
            />
          </div>

          <div className="space-y-20">
            {steps.map((step, i) => (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                className="flex items-start gap-10 group cursor-default"
              >
                <div className="relative shrink-0 w-12 h-12 rounded-full bg-cream-dark border border-silver-light flex items-center justify-center group-hover:border-foreground group-hover:bg-foreground transition-all duration-300 z-10">
                  <span className="font-mono text-sm text-silver-dark group-hover:text-cream transition-colors duration-300">
                    {step.number}
                  </span>
                </div>
                <div className="pt-2">
                  <h3 className="font-serif text-3xl md:text-4xl mb-1 group-hover:translate-x-1 transition-transform duration-300">
                    {step.label}
                  </h3>
                  <p className="font-mono text-sm md:text-base text-silver-dark">
                    {step.description}
                  </p>
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
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full border border-silver-light/20 pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] rounded-full border border-silver-light/15 pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[200px] h-[200px] rounded-full border border-silver-light/10 pointer-events-none" />

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
      <MarqueeStrip />
      <FeaturesSection />
      <StepsSection />
      <BottomCTA />
      <Footer />
    </main>
  );
}
