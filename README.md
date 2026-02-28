# StoryScape

StoryScape is a lightweight story-graph backend with responsive landing UI, token auth, branching nodes, and optional Gemini image generation.

## Simplified stack

- Django + Django REST Framework
- LangGraph (optional story pipeline)
- LlamaIndex (optional retrieval/query layer)
- ChromaDB (optional vector store hook)
- SQLite (default)
- Gemini image API (optional)

## Story graph model

Each story is a directed graph:

- `Story` = container
- `FlashCard` = node (text + image)
- `CardConnection` = edge (`source_card -> target_card`)

## Ramayan-style dummy graph (multiverse)

A management command seeds a branching graph like:

- Start: Sharat by the river
- Next: tracks in the forest
- Branch A: he goes hunting
- Branch B (multiverse): he goes eating with villagers
- Each branch continues to its own next node

Run:

```bash
python manage.py migrate
python manage.py seed_dummy_story
```

The command prints graph JSON (`nodes` and `edges`) so you can inspect structure directly.

## API endpoints

### Auth

- `POST /api/auth/register/`
- `POST /api/auth/token/`
- `GET /api/auth/profile/`

### Stories

- `GET /api/stories/`
- `POST /api/stories/`
- `GET /api/stories/{id}/`
- `DELETE /api/stories/{id}/delete/`
- `GET /api/stories/{id}/graph/`

### Flashcards

- `POST /api/stories/{story_id}/flashcards/`
- `PUT /api/flashcards/{id}/`
- `DELETE /api/flashcards/{id}/delete/`
- `POST /api/flashcards/{id}/generate-image/`

## Root UI

Open:

- `http://127.0.0.1:8000/`

You get a responsive web flow with separate pages:

- `/` landing page
- `/login/` login page
- `/register/` register page
- `/app/` story workspace with visual graph viewer

Workspace features:

- Story creation form
- Story list loader
- Graph visualization (SVG nodes + edges)

This avoids manual `401 Authentication credentials were not provided` errors on protected endpoints.

Guest mode allows up to 5 stories per browser session without login.

## Gemini image generation

Set env vars in `.env`:

```env
GEMINI_API_KEY=your_key
GEMINI_IMAGE_MODEL=gemini-2.0-flash-exp
```

Then call image endpoint. If API is unavailable, the app safely falls back to a placeholder image URL.

## Docker (SQLite-first)

```bash
docker compose up --build
```

Services:

- `web` (Django)

No PostgreSQL, Redis, or Celery services are required.

## Local run

```bash
pip install -r requirements.txt
cp env.example .env
python manage.py migrate
python manage.py runserver
```

## Notes

- This repository is now simplified to SQLite-first operation and removes runtime dependence on PostgreSQL/pgvector.
- Celery dispatch in views has inline fallback, so core flows still work even if broker is down.
