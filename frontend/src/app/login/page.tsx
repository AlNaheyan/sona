"use client";

import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Eye, EyeOff } from "lucide-react";
import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth, ApiError } from "@/contexts/auth";

/* ─────────────────────────────────────────────
   Auth Vinyl (half off-screen left)
   ───────────────────────────────────────────── */
function AuthVinyl() {
  return (
    <div className="absolute top-1/2 -translate-y-1/2 left-0 -translate-x-1/2 pointer-events-none select-none">
      <div className="vinyl relative w-175 h-175 lg:w-200 lg:h-200 rounded-full bg-[radial-gradient(ellipse_at_30%_30%,#3a3a3a,#1a1a1a_40%,#0d0d0d_70%,#000000)]">
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
    transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] as const },
  },
};

/* ─────────────────────────────────────────────
   Login Page
   ───────────────────────────────────────────── */
export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  const validate = () => {
    const e: Record<string, string> = {};

    if (!email) e.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
      e.email = "Invalid email address";

    if (!password) e.password = "Password is required";

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
    setTouched({ email: true, password: true });

    if (Object.keys(validationErrors).length > 0) return;

    setIsSubmitting(true);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      setIsSubmitting(false);
      const message = err instanceof ApiError ? err.message : "Invalid email or password";
      setErrors({ email: message });
    }
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
                Welcome
                <br />
                <span className="italic">back.</span>
              </h1>
              <p className="font-mono text-sm text-silver-dark leading-relaxed">
                Sign in to continue ranking.
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

            {/* Password */}
            <motion.div variants={item} className="mb-8">
              <div className="flex items-center justify-between mb-2">
                <label className="block font-mono text-[10px] tracking-[0.2em] uppercase text-silver-dark">
                  Password
                </label>
                <span className="font-mono text-[10px] text-silver-dark/50">
                  Forgot password?
                </span>
              </div>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onBlur={() => handleBlur("password")}
                  placeholder="Your password"
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

            {/* Submit */}
            <motion.div variants={item} className="mb-8">
              <motion.button
                type="submit"
                disabled={isSubmitting}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full font-mono text-sm tracking-widest uppercase py-4 bg-foreground text-cream rounded-full hover:shadow-[0_8px_30px_rgba(0,0,0,0.12)] transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? "Signing in..." : "Sign In"}
              </motion.button>
            </motion.div>

            {/* Register link */}
            <motion.p
              variants={item}
              className="text-center font-mono text-[11px] text-silver-dark"
            >
              Don&apos;t have an account?{" "}
              <Link
                href="/register"
                className="text-foreground hover:underline"
              >
                Sign up
              </Link>
            </motion.p>
          </motion.form>
        </div>
      </div>
    </div>
  );
}
