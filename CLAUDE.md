# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**RateMyAlbum** is an album-first music rating, ranking, and recommendation platform. Users intentionally rate albums (not passive listening) and receive explainable recommendations based on expressed taste.

## Tech Stack
Backend
- **API:** FastAPI with async/await
- **Validation:** Pydantic v2
- **ORM:** SQLAlchemy 2.0 (async)
- **Database:** PostgreSQL
- **Cache:** Redis
- **Search:** OpenSearch/Elasticsearch
- **Auth:** JWT + OAuth (Spotify)
- **ML/Recsys:** NumPy, Scikit-learn
- **Background Jobs:** Celery + Redis
- **Events:** RabbitMQ or Redis Streams
- **Infrastructure:** Docker

Frontend
- Next.js
- TypeScript
- Tailwind CSS
- TanStack Query
- BetterAuth
- React Hook Form + Zod
- shadcn/ui
- Framer Motion
- dnd-kit
- Recharts

## Core Algorithm: CWPR (Confidence-Weighted Preference Ranking)

The ranking system models user preference as mean (μ) and uncertainty (σ):

```
Score = μ − λσ
```

Supports three input types:
- Numeric ratings (1-10)
- Pairwise comparisons
- Tier lists

Community rankings aggregate user means, penalize high disagreement, and weight by sample size.

## External Integrations

- **Spotify API:** Album/artist search and metadata (catalog grows on-demand)
- **Claude API:** AI-generated insights about user taste and recommendations

## Key Domain Concepts

- **Album Rating:** 1-10 score with context capture (mood, notes)
- **Personal Rankings:** Per-user confidence-aware album ordering
- **Community Rankings:** Aggregated scores surfacing best-regarded, controversial, and trending albums
- **Recommendations:** Phase 1 uses similar-user/similar-album approaches; Phase 2 adds latent embeddings and diversity-aware ranking

## MVP Scope

**Included:** Album/artist search, album pages with community scores, user auth, personal rankings, community rankings, personalized recommendations, confidence visualization

**Excluded:** Audio playback, playlists, social feeds, comments/reviews, implicit listening data
