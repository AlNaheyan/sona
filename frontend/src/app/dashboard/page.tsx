"use client";

import { useSession } from "@/lib/auth-client";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function DashboardPage() {
  const { data: session, isPending } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (!isPending && !session?.user) {
      router.push("/login");
    }
  }, [isPending, session, router]);

  if (isPending) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <span className="font-mono text-sm text-silver-dark animate-pulse">Loading...</span>
      </div>
    );
  }

  if (!session?.user) return null;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="max-w-4xl mx-auto px-8 py-16">
        <h1 className="font-serif text-4xl md:text-5xl tracking-tight mb-3">
          Welcome back, <span className="italic">{session.user.name || "music lover"}.</span>
        </h1>
        <p className="font-mono text-sm text-silver-dark mb-12">
          Your dashboard is coming soon.
        </p>

        <div className="border border-dashed border-silver-light/40 rounded-2xl p-12 text-center">
          <span className="font-mono text-xs text-silver">
            Dashboard content will be built here — rankings, recommendations, comparison suggestions.
          </span>
        </div>
      </div>
    </div>
  );
}
