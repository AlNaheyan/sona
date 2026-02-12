"use client";

import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Eye, EyeOff } from "lucide-react";
import { useState, useMemo, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { signUp } from "@/lib/auth-client";

/* ─────────────────────────────────────────────
   Password Strength
   ───────────────────────────────────────────── */
function getStrength(pw: string) {
  if (!pw) return { score: 0, label: "", pct: 0 };
  let s = 0;
  if (pw.length >= 8) s++;
  if (pw.length >= 12) s++;
  if (/[A-Z]/.test(pw)) s++;
  if (/[0-9]/.test(pw)) s++;
  if (/[^a-zA-Z0-9]/.test(pw)) s++;

  if (s <= 2) return { score: 1, label: "Weak", pct: 33 };
  if (s <= 3) return { score: 2, label: "Fair", pct: 66 };
  return { score: 3, label: "Strong", pct: 100 };
}

/* ─────────────────────────────────────────────
   Auth Vinyl (smaller version)
   ───────────────────────────────────────────── */
function AuthVinyl() {
  return (
    <div className="absolute top-1/2 -translate-y-1/2 left-0 -translate-x-1/2 pointer-events-none select-none">
      <div className="vinyl relative w-[700px] h-[700px] lg:w-[800px] lg:h-[800px] rounded-full bg-[radial-gradient(ellipse_at_30%_30%,#3a3a3a,#1a1a1a_40%,#0d0d0d_70%,#000000)]">
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
              Sona
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
   Animation Variants
   ───────────────────────────────────────────── */
const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.07, delayChildren: 0.2 },
  },
};

const item = {
  hidden: { opacity: 0, x: 20 },
  show: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] },
  },
};

/* ─────────────────────────────────────────────
   Register Page
   ───────────────────────────────────────────── */
export default function RegisterPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  const strength = useMemo(() => getStrength(password), [password]);

  const validate = () => {
    const e: Record<string, string> = {};

    if (!email) e.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
      e.email = "Invalid email address";

    if (!username) e.username = "Username is required";
    else if (username.length < 3) e.username = "At least 3 characters";
    else if (username.length > 50) e.username = "At most 50 characters";
    else if (!/^[a-zA-Z0-9_]+$/.test(username))
      e.username = "Letters, numbers, and underscores only";

    if (!password) e.password = "Password is required";
    else if (password.length < 8) e.password = "At least 8 characters";

    if (!termsAccepted) e.terms = "You must accept the terms";

    return e;
  };

  const handleBlur = (field: string) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
    const allErrors = validate();
    if (allErrors[field]) {
      setErrors((prev) => ({ ...prev, [field]: allErrors[field] }));
    } else {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const validationErrors = validate();
    setErrors(validationErrors);
    setTouched({ email: true, username: true, password: true, terms: true });

    if (Object.keys(validationErrors).length > 0) return;

    setIsSubmitting(true);
    const { error } = await signUp.email({
      email,
      password,
      name: username,
    });

    if (error) {
      setErrors({ email: error.message ?? "Something went wrong" });
      setIsSubmitting(false);
      return;
    }

    router.push("/onboarding");
  };

  return (
    <div className="min-h-screen flex bg-background">
      {/* ─── Left: Vinyl Visual ─── */}
      <div className="hidden lg:flex w-1/2 bg-cream-dark relative overflow-hidden">
        <AuthVinyl />

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="absolute bottom-14 right-14"
        >
          <span className="font-serif text-2xl block mb-1">Sona</span>
          <p className="font-mono text-[11px] text-silver-dark tracking-wide">
            Rank your music. Discover your taste.
          </p>
        </motion.div>
      </div>

      {/* ─── Right: Form ─── */}
      <div className="w-full lg:w-1/2 flex flex-col min-h-screen">
        {/* Back link */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="p-8 md:p-10"
        >
          <Link
            href="/"
            className="inline-flex items-center gap-2 font-mono text-[11px] text-silver-dark hover:text-foreground transition-colors duration-300 tracking-wide uppercase"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to home
          </Link>
        </motion.div>

        {/* Form area */}
        <div className="flex-1 flex items-center justify-center px-8 md:px-16 lg:px-20 pb-16">
          <motion.form
            variants={container}
            initial="hidden"
            animate="show"
            onSubmit={handleSubmit}
            className="w-full max-w-sm"
            noValidate
          >
            {/* Heading */}
            <motion.div variants={item} className="mb-10">
              <h1 className="font-serif text-4xl md:text-5xl tracking-tight mb-3">
                Create your
                <br />
                <span className="italic">account.</span>
              </h1>
              <p className="font-mono text-sm text-silver-dark leading-relaxed">
                Start ranking the music you love.
              </p>
            </motion.div>

            {/* Email */}
            <motion.div variants={item} className="mb-5">
              <label className="block font-mono text-[10px] tracking-[0.2em] uppercase text-silver-dark mb-2">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onBlur={() => handleBlur("email")}
                placeholder="you@example.com"
                className={`w-full font-mono text-sm bg-transparent border ${
                  errors.email && touched.email
                    ? "border-foreground"
                    : "border-silver-light"
                } rounded-xl py-3 px-4 text-foreground placeholder:text-silver-light outline-none focus:border-silver-dark transition-colors duration-300`}
              />
              <AnimatePresence>
                {errors.email && touched.email && (
                  <motion.p
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    className="font-mono text-[10px] text-foreground mt-1.5 ml-1"
                  >
                    {errors.email}
                  </motion.p>
                )}
              </AnimatePresence>
            </motion.div>

            {/* Username */}
            <motion.div variants={item} className="mb-5">
              <label className="block font-mono text-[10px] tracking-[0.2em] uppercase text-silver-dark mb-2">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onBlur={() => handleBlur("username")}
                placeholder="your_username"
                className={`w-full font-mono text-sm bg-transparent border ${
                  errors.username && touched.username
                    ? "border-foreground"
                    : "border-silver-light"
                } rounded-xl py-3 px-4 text-foreground placeholder:text-silver-light outline-none focus:border-silver-dark transition-colors duration-300`}
              />
              <AnimatePresence>
                {errors.username && touched.username && (
                  <motion.p
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    className="font-mono text-[10px] text-foreground mt-1.5 ml-1"
                  >
                    {errors.username}
                  </motion.p>
                )}
              </AnimatePresence>
            </motion.div>

            {/* Password */}
            <motion.div variants={item} className="mb-5">
              <label className="block font-mono text-[10px] tracking-[0.2em] uppercase text-silver-dark mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onBlur={() => handleBlur("password")}
                  placeholder="At least 8 characters"
                  className={`w-full font-mono text-sm bg-transparent border ${
                    errors.password && touched.password
                      ? "border-foreground"
                      : "border-silver-light"
                  } rounded-xl py-3 px-4 pr-11 text-foreground placeholder:text-silver-light outline-none focus:border-silver-dark transition-colors duration-300`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-silver-dark hover:text-foreground transition-colors duration-300"
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>

              {/* Strength meter */}
              <AnimatePresence>
                {password && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-2.5 flex items-center gap-3"
                  >
                    <div className="flex-1 h-1 bg-silver-light/30 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${strength.pct}%` }}
                        transition={{ duration: 0.4, ease: [0, 0, 0.2, 1] }}
                        className={`h-full rounded-full transition-colors duration-300 ${
                          strength.score === 1
                            ? "bg-silver-light"
                            : strength.score === 2
                              ? "bg-silver-dark"
                              : "bg-foreground"
                        }`}
                      />
                    </div>
                    <span className="font-mono text-[10px] text-silver-dark shrink-0">
                      {strength.label}
                    </span>
                  </motion.div>
                )}
              </AnimatePresence>

              <AnimatePresence>
                {errors.password && touched.password && (
                  <motion.p
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    className="font-mono text-[10px] text-foreground mt-1.5 ml-1"
                  >
                    {errors.password}
                  </motion.p>
                )}
              </AnimatePresence>
            </motion.div>

            {/* Terms */}
            <motion.div variants={item} className="mb-8">
              <label className="flex items-start gap-3 cursor-pointer group">
                <div className="relative mt-0.5">
                  <input
                    type="checkbox"
                    checked={termsAccepted}
                    onChange={(e) => setTermsAccepted(e.target.checked)}
                    className="sr-only"
                  />
                  <div
                    className={`w-4.5 h-4.5 rounded border ${
                      termsAccepted
                        ? "bg-foreground border-foreground"
                        : errors.terms && touched.terms
                          ? "border-foreground"
                          : "border-silver-light group-hover:border-silver-dark"
                    } transition-all duration-300 flex items-center justify-center`}
                  >
                    <motion.svg
                      initial={false}
                      animate={{
                        scale: termsAccepted ? 1 : 0,
                        opacity: termsAccepted ? 1 : 0,
                      }}
                      transition={{ duration: 0.2 }}
                      className="w-3 h-3 text-cream"
                      viewBox="0 0 12 12"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M2 6l3 3 5-5" />
                    </motion.svg>
                  </div>
                </div>
                <span className="font-mono text-[11px] text-silver-dark leading-relaxed">
                  I agree to the{" "}
                  <Link
                    href="/terms"
                    className="text-foreground hover:underline"
                  >
                    Terms of Service
                  </Link>
                </span>
              </label>
              <AnimatePresence>
                {errors.terms && touched.terms && (
                  <motion.p
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    className="font-mono text-[10px] text-foreground mt-1.5 ml-7"
                  >
                    {errors.terms}
                  </motion.p>
                )}
              </AnimatePresence>
            </motion.div>

            {/* Submit */}
            <motion.div variants={item} className="mb-8">
              <motion.button
                type="submit"
                disabled={isSubmitting}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full font-mono text-sm tracking-widest uppercase py-4 bg-foreground text-cream rounded-full hover:shadow-[0_8px_30px_rgba(0,0,0,0.12)] transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? "Creating..." : "Create Account"}
              </motion.button>
            </motion.div>

            {/* Sign in link */}
            <motion.p
              variants={item}
              className="text-center font-mono text-[11px] text-silver-dark"
            >
              Already have an account?{" "}
              <Link href="/login" className="text-foreground hover:underline">
                Sign in
              </Link>
            </motion.p>
          </motion.form>
        </div>
      </div>
    </div>
  );
}
