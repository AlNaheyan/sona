# RateMyAlbum

Album rating and recommendation API with confidence-weighted preference ranking.

## Tech Stack

- **Framework:** FastAPI (async)
- **Database:** PostgreSQL with SQLAlchemy 2.0 (async)
- **Cache:** Redis
- **Auth:** JWT (python-jose + bcrypt)
- **External API:** MusicBrainz for album metadata
- **Python:** 3.11+

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/login` - Login and get access token
- `GET /api/v1/auth/me` - Get current user profile (requires auth)

### Albums
- `GET /api/v1/albums/search` - Search albums via MusicBrainz
- `GET /api/v1/albums/db/list` - List rated albums from database
- `GET /api/v1/albums/{mbid}` - Get album details by MusicBrainz ID

### Ratings
- `POST /api/v1/ratings` - Rate an album 1-10 (requires auth)
- `GET /api/v1/ratings` - Get your ratings (requires auth)
- `DELETE /api/v1/ratings/{rating_id}` - Delete a rating (requires auth)

### Health
- `GET /health` - Health check
- `GET /` - API info

## Setup

### With Docker

```bash
docker-compose up -d
```

This starts the API on port 8000, PostgreSQL on 5432, and Redis on 6379.

### Local Development

1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install -e ".[dev]"
```

3. Set up environment variables (copy from .env.example or set directly):
```bash
export DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ratemyalbum
export REDIS_URL=redis://localhost:6379/0
export SECRET_KEY=your-secret-key
```

4. Run the server:
```bash
uvicorn backend.app.main:app --reload
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
  app/
    api/v1/endpoints/   # Route handlers
    core/               # Config, database
    models/             # SQLAlchemy models
    schemas/            # Pydantic schemas
    services/           # Business logic (auth, MusicBrainz client)
    main.py             # FastAPI app
  alembic/              # Database migrations
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | postgresql+asyncpg://... |
| REDIS_URL | Redis connection string | redis://localhost:6379/0 |
| SECRET_KEY | JWT signing key | dev-secret-key-change-in-production |
| DEBUG | Enable debug mode | true |
| CWPR_LAMBDA | Confidence penalty factor | 1.0 |
