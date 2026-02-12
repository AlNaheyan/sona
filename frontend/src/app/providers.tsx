"use client";

import { AuthProvider } from "@/contexts/auth";
import type { ReactNode } from "react";

export function Providers({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}
