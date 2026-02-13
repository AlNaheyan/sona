"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  Trophy,
  Users,
  Sparkles,
  Search,
  User,
  Menu,
  X,
  LogOut,
} from "lucide-react";
import { useAuth } from "@/contexts/auth";

const navItems = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard" },
  { icon: Trophy, label: "My Ranking", href: "/rankings" },
  { icon: Users, label: "Community", href: "/community" },
  { icon: Sparkles, label: "Recommendations", href: "/recommendations" },
  { icon: Search, label: "Search", href: "/search" },
  { icon: User, label: "Profile", href: "/profile" },
] as const;

function getInitials(name: string): string {
  const words = name.split(/\s+/).filter((w) => w.length > 0);
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const displayName = user?.username || "User";

  return (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="px-6 pt-8 pb-8">
        <Link
          href="/dashboard"
          onClick={onNavigate}
          className="font-serif text-xl tracking-tight italic"
        >
          Sona
        </Link>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3">
        <ul className="space-y-1">
          {navItems.map(({ icon: Icon, label, href }) => {
            const isActive = pathname === href || pathname.startsWith(href + "/");
            return (
              <li key={href}>
                <Link
                  href={href}
                  onClick={onNavigate}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg font-mono text-sm transition-colors duration-200 ${
                    isActive
                      ? "bg-cream-dark text-foreground"
                      : "text-silver-dark hover:bg-cream-dark/50 hover:text-foreground"
                  }`}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  {label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* User section */}
      <div className="px-4 pb-6 pt-4 border-t border-silver-light/30">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-9 h-9 rounded-full bg-linear-to-br from-zinc-700 to-zinc-900 flex items-center justify-center shrink-0">
            <span className="font-serif text-xs text-white/40 italic select-none">
              {getInitials(displayName)}
            </span>
          </div>
          <p className="font-serif text-sm tracking-tight truncate min-w-0 flex-1">
            {displayName}
          </p>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-2 font-mono text-xs text-silver-dark hover:text-foreground transition-colors duration-200 w-full px-1"
        >
          <LogOut className="w-3.5 h-3.5" />
          Sign out
        </button>
      </div>
    </div>
  );
}

export function Sidebar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  const closeMobile = useCallback(() => setMobileOpen(false), []);

  // Close on Escape
  useEffect(() => {
    if (!mobileOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeMobile();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [mobileOpen, closeMobile]);

  // Lock body scroll when mobile sidebar open
  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex lg:flex-col lg:fixed lg:inset-y-0 lg:left-0 lg:w-60 lg:bg-background lg:border-r lg:border-silver-light/40">
        <SidebarContent />
      </aside>

      {/* Mobile hamburger */}
      <button
        onClick={() => setMobileOpen(true)}
        className="lg:hidden fixed top-5 left-5 z-40 p-2 rounded-lg bg-background/80 backdrop-blur-sm border border-silver-light/30 text-foreground"
        aria-label="Open menu"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Mobile overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              onClick={closeMobile}
              className="lg:hidden fixed inset-0 z-40 bg-black/20 backdrop-blur-sm"
            />

            {/* Sliding panel */}
            <motion.aside
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="lg:hidden fixed inset-y-0 left-0 z-50 w-60 bg-background border-r border-silver-light/40"
            >
              {/* Close button */}
              <button
                onClick={closeMobile}
                className="absolute top-5 right-4 p-1.5 rounded-lg text-silver-dark hover:text-foreground transition-colors duration-200"
                aria-label="Close menu"
              >
                <X className="w-5 h-5" />
              </button>

              <SidebarContent onNavigate={closeMobile} />
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
