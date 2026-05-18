"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Trophy, X } from "lucide-react";
import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/contexts/auth";
import { apiFetch, ApiError } from "@/lib/api";
import { stagger, fadeUp } from "@/components/motion";
import { AlbumCover } from "@/components/album-cover";
import { SectionLabel } from "@/components/section-label";
import { StatCard } from "@/components/stat-card";
import { EmptyState } from "@/components/empty-state";

/* ─────────────────────────────────────────────
   Types
   ───────────────────────────────────────────── */
interface ProfileData {
  username: string;
  display_name: string | null;
  bio: string | null;
  avatar_url: string | null;
  spotify_username: string | null;
  favorite_genres: string | null;
  rated_albums_count: number;
  member_since: string;
}

interface RankedAlbum {
  rank: number;
  album_id: string;
  album_title: string;
  album_artist: string | null;
  album_cover_url: string | null;
  elo: number;
  rating_count: number;
  comparison_count: number;
}

interface RankingsResponse {
  rankings: RankedAlbum[];
  count: number;
}

/* ─────────────────────────────────────────────
   Helpers
   ───────────────────────────────────────────── */
function getInitials(name: string): string {
  const words = name.split(/\s+/).filter((w) => w.length > 0);
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

function formatMemberSince(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", { month: "short", year: "numeric" });
}

/* ─────────────────────────────────────────────
   Profile Page
   ───────────────────────────────────────────── */
export default function ProfilePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [topAlbums, setTopAlbums] = useState<RankedAlbum[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [imgFailed, setImgFailed] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);
  const editFormRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    if (!user) return;

    const profileReq = apiFetch<ProfileData>(`/api/v1/profile/${user.username}`)
      .then(setProfile)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 404) {
          setNotFound(true);
        }
      });

    const rankingsReq = apiFetch<RankingsResponse>("/api/v1/rankings?limit=5")
      .then((data) => setTopAlbums(data.rankings))
      .catch(() => {});

    Promise.all([profileReq, rankingsReq]).finally(() => setIsLoading(false));
  }, [user]);

  // Profile-specific loading (auth is handled by layout)
  if (isLoading && !notFound) {
    return (
      <div className="flex items-center justify-center py-32">
        <span className="font-mono text-sm text-silver-dark animate-pulse">Loading...</span>
      </div>
    );
  }

  // No profile found
  if (notFound) {
    return (
      <div className="max-w-2xl mx-auto px-8 py-16">
        <EmptyState
          heading="No profile yet."
          description="Complete onboarding to set up your profile."
          actionLabel="Set Up Profile"
          actionHref="/onboarding"
        />
      </div>
    );
  }

  if (!profile) return null;

  const displayName = profile.display_name || profile.username;
  const genres = profile.favorite_genres
    ? profile.favorite_genres.split(",").map((g) => g.trim()).filter(Boolean)
    : [];

  return (
    <div className="max-w-2xl mx-auto px-8 py-16">
      <motion.div
        variants={stagger}
        initial="hidden"
        animate="show"
      >
        {/* Profile header */}
        <motion.div variants={fadeUp} className="flex items-center gap-5 mb-6">
          {/* Avatar */}
          {profile.avatar_url && !imgFailed ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={profile.avatar_url}
              alt={displayName}
              className="w-24 h-24 rounded-full object-cover shrink-0"
              onError={() => setImgFailed(true)}
            />
          ) : (
            <div className="w-24 h-24 rounded-full bg-linear-to-br from-zinc-700 to-zinc-900 flex items-center justify-center shrink-0">
              <span className="font-serif text-2xl text-white/40 italic select-none">
                {getInitials(displayName)}
              </span>
            </div>
          )}

          <div className="min-w-0">
            <h1 className="font-serif text-3xl md:text-4xl tracking-tight">
              {displayName}
            </h1>
            <p className="font-mono text-sm text-silver-dark">
              @{profile.username}
            </p>
          </div>
        </motion.div>

        {/* Bio */}
        {profile.bio && (
          <motion.p
            variants={fadeUp}
            className="font-mono text-sm text-silver-dark leading-relaxed mb-8"
          >
            {profile.bio}
          </motion.p>
        )}

        {/* Stats row */}
        <motion.div variants={fadeUp} className="grid grid-cols-2 gap-4 mb-8">
          <StatCard label="Albums Rated" value={profile.rated_albums_count} />
          <StatCard label="Member Since" value={formatMemberSince(profile.member_since)} />
        </motion.div>

        {/* Top 5 Ranked Albums */}
        <motion.div variants={fadeUp} className="mb-8">
          <SectionLabel className="mb-3">Top 5 Albums</SectionLabel>
          {topAlbums.length > 0 ? (
            <div className="space-y-2">
              {topAlbums.map((album) => (
                <div
                  key={album.album_id}
                  className="flex items-center gap-3 p-3 rounded-xl border border-silver-light/30 hover:border-silver-light/60 transition-colors duration-200"
                >
                  <span className="font-mono text-[10px] text-silver-dark w-5 text-right shrink-0">
                    {album.rank}
                  </span>
                  <AlbumCover
                    title={album.album_title}
                    coverUrl={album.album_cover_url}
                  />
                  <div className="min-w-0 flex-1">
                    <p className="font-serif text-sm tracking-tight truncate">
                      {album.album_title}
                    </p>
                    <p className="font-mono text-[10px] text-silver-dark truncate">
                      {album.album_artist || "Unknown Artist"}
                    </p>
                  </div>
                  <span className="font-mono text-[10px] text-silver shrink-0">
                    {album.elo}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={Trophy}
              heading="No rankings yet."
              description="Rate and compare albums to build your personal ranking."
              actionLabel="Start Ranking"
              actionHref="/onboarding"
            />
          )}
        </motion.div>

        {/* Genres */}
        {genres.length > 0 && (
          <motion.div variants={fadeUp} className="mb-8">
            <SectionLabel className="mb-3">Favorite Genres</SectionLabel>
            <div className="flex flex-wrap gap-2">
              {genres.map((genre) => (
                <span
                  key={genre}
                  className="font-mono text-xs tracking-wide py-2 px-4 rounded-full border border-silver-light text-silver-dark"
                >
                  {genre}
                </span>
              ))}
            </div>
          </motion.div>
        )}

        {/* Spotify */}
        {profile.spotify_username && (
          <motion.div variants={fadeUp} className="mb-10">
            <SectionLabel className="mb-1">Spotify</SectionLabel>
            <p className="font-mono text-sm text-foreground">
              {profile.spotify_username}
            </p>
          </motion.div>
        )}

        {/* Edit Profile button */}
        <motion.div variants={fadeUp}>
          <button
            onClick={() => { setEditError(null); setEditOpen(true); }}
            className="font-mono text-sm tracking-widest uppercase py-3.5 px-10 border border-silver-light text-foreground rounded-full hover:border-foreground transition-colors duration-300"
          >
            Edit Profile
          </button>
        </motion.div>
      </motion.div>

      {/* Edit Profile Modal */}
      <AnimatePresence>
        {editOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center px-4"
          >
            <div
              className="absolute inset-0 bg-black/50 backdrop-blur-sm"
              onClick={() => setEditOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.96, y: 16 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.96, y: 16 }}
              transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
              className="relative bg-background border border-silver-light/40 rounded-2xl p-8 w-full max-w-md shadow-2xl"
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="font-serif text-xl tracking-tight">Edit Profile</h2>
                <button onClick={() => setEditOpen(false)} className="text-silver-dark hover:text-foreground transition-colors">
                  <X size={18} />
                </button>
              </div>

              <form
                ref={editFormRef}
                onSubmit={async (e) => {
                  e.preventDefault();
                  if (!profile) return;
                  const fd = new FormData(e.currentTarget);
                  setEditSaving(true);
                  setEditError(null);
                  try {
                    await apiFetch("/api/v1/profile/me", {
                      method: "PUT",
                      body: JSON.stringify({
                        display_name: fd.get("display_name") as string,
                        bio: (fd.get("bio") as string) || null,
                        spotify_username: (fd.get("spotify_username") as string) || null,
                        favorite_genres: (fd.get("favorite_genres") as string) || null,
                      }),
                    });
                    // Refresh profile data
                    const updated = await apiFetch<ProfileData>(`/api/v1/profile/${profile.username}`);
                    setProfile(updated);
                    setEditOpen(false);
                  } catch (err) {
                    setEditError(err instanceof ApiError ? err.message : "Failed to save. Try again.");
                  } finally {
                    setEditSaving(false);
                  }
                }}
                className="space-y-4"
              >
                {[
                  { name: "display_name", label: "Display Name", type: "text", defaultValue: profile.display_name || profile.username, required: true },
                  { name: "bio", label: "Bio", type: "textarea", defaultValue: profile.bio || "", required: false },
                  { name: "spotify_username", label: "Spotify Username", type: "text", defaultValue: profile.spotify_username || "", required: false },
                  { name: "favorite_genres", label: "Favorite Genres (comma-separated)", type: "text", defaultValue: profile.favorite_genres || "", required: false },
                ].map(({ name, label, type, defaultValue, required }) => (
                  <div key={name}>
                    <label className="block font-mono text-[10px] tracking-[0.2em] uppercase text-silver-dark mb-1.5">
                      {label}
                    </label>
                    {type === "textarea" ? (
                      <textarea
                        name={name}
                        defaultValue={defaultValue}
                        rows={3}
                        className="w-full bg-transparent border border-silver-light/40 rounded-lg px-3 py-2 font-mono text-sm focus:outline-none focus:border-zinc-900 transition-colors resize-none"
                      />
                    ) : (
                      <input
                        type="text"
                        name={name}
                        defaultValue={defaultValue}
                        required={required}
                        className="w-full bg-transparent border border-silver-light/40 rounded-lg px-3 py-2 font-mono text-sm focus:outline-none focus:border-zinc-900 transition-colors"
                      />
                    )}
                  </div>
                ))}

                {editError && (
                  <p className="font-mono text-xs text-red-500">{editError}</p>
                )}

                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setEditOpen(false)}
                    className="flex-1 font-mono text-xs uppercase tracking-widest py-3 border border-silver-light/40 rounded-full hover:border-silver-light transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={editSaving}
                    className="flex-1 font-mono text-xs uppercase tracking-widest py-3 bg-zinc-900 text-white rounded-full hover:bg-zinc-700 transition-colors disabled:opacity-50"
                  >
                    {editSaving ? "Saving…" : "Save"}
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
