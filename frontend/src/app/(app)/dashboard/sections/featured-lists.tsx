"use client";

import { motion } from "framer-motion";
import { ListMusic } from "lucide-react";
import { fadeUp } from "@/components/motion";
import { SectionLabel } from "@/components/section-label";

const featuredCategories = [
  "Top 10 Pop",
  "Top 10 Hip Hop",
  "Top 10 R&B",
  "Top 10 Rock",
  "Top 10 Electronic",
  "Top 10 Jazz",
];

export function FeaturedLists() {
  return (
    <motion.div variants={fadeUp} className="mb-10">
      <div className="flex items-center gap-2 mb-4">
        <ListMusic className="w-3.5 h-3.5 text-silver-dark" />
        <SectionLabel>Featured Lists</SectionLabel>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {featuredCategories.map((category) => (
          <div
            key={category}
            className="p-4 rounded-xl border border-silver-light/30 hover:border-silver-light/60 transition-colors duration-200 cursor-pointer"
          >
            <p className="font-serif text-sm tracking-tight mb-1">
              {category}
            </p>
            <p className="font-mono text-[10px] text-silver-dark">
              Coming soon
            </p>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
